"""Unit tests for EPIC-002 — PDF Geometry Extraction.

Covers:
  - BasePDFNormalizer helpers
  - Each concrete normalizer (AutoCAD, Revit, ArchiCAD, Generic)
  - PDFSourceDetector (with real fixture PDFs)
  - PDFImportAdapter (with real fixture PDFs)
  - FileFacadePlanRepository
  - _color_to_rgb helper
  - _lt_curve_to_raw_geometry helper
"""
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from facade_planner.domain.enums import PDFSource
from facade_planner.domain.value_objects.raw_geometry import RawGeometry
from facade_planner.infrastructure.adapters.pdf_import_adapter import (
    PDFImportAdapter,
    _color_to_rgb,
    _lt_curve_to_raw_geometry,
)
from facade_planner.infrastructure.adapters.pdf_normalizers.autocad_normalizer import (
    AutoCADPDFNormalizer,
)
from facade_planner.infrastructure.adapters.pdf_normalizers.archicad_normalizer import (
    ArchiCADPDFNormalizer,
)
from facade_planner.infrastructure.adapters.pdf_normalizers.factory import get_normalizer
from facade_planner.infrastructure.adapters.pdf_normalizers.generic_normalizer import (
    GenericPDFNormalizer,
)
from facade_planner.infrastructure.adapters.pdf_normalizers.revit_normalizer import (
    RevitPDFNormalizer,
)
from facade_planner.infrastructure.adapters.pdf_source_detector import PDFSourceDetector
from facade_planner.infrastructure.persistence.facade_plan_repository import (
    FileFacadePlanRepository,
)

# ── Paths to fixture PDFs ─────────────────────────────────────────────────────

_FIXTURES = Path(__file__).parent.parent / "fixtures" / "pdf"
_GENERIC_PDF = _FIXTURES / "minimal_generic.pdf"
_AUTOCAD_PDF = _FIXTURES / "minimal_autocad.pdf"
_REVIT_PDF = _FIXTURES / "minimal_revit.pdf"
_ARCHICAD_PDF = _FIXTURES / "minimal_archicad.pdf"
_OPENING_PDF = _FIXTURES / "rect_with_opening.pdf"
_EMPTY_PDF = _FIXTURES / "empty_page.pdf"


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _make_geom(
    coords: list[tuple[float, float]],
    layer: str = "",
    is_closed: bool = False,
) -> RawGeometry:
    return RawGeometry(coordinates=coords, layer=layer, is_closed=is_closed)


# ── COLOR CONVERSION ──────────────────────────────────────────────────────────

class TestColorToRgb:
    def test_rgb_triplet(self) -> None:
        assert _color_to_rgb([1.0, 0.0, 0.0]) == (255, 0, 0)

    def test_greyscale(self) -> None:
        result = _color_to_rgb([0.5])
        assert result == (127, 127, 127)

    def test_none_returns_none(self) -> None:
        assert _color_to_rgb(None) is None

    def test_clamps_overflow(self) -> None:
        r, g, b = _color_to_rgb([1.1, -0.1, 0.5])  # type: ignore[misc]
        assert r == 255 and g == 0

    def test_unknown_format_returns_none(self) -> None:
        assert _color_to_rgb("red") is None  # type: ignore[arg-type]


# ── LT CURVE → RAW GEOMETRY ──────────────────────────────────────────────────

class TestLtCurveToRawGeometry:
    def _mock_curve(self, pts: list, color=None) -> MagicMock:
        m = MagicMock()
        m.pts = pts
        m.stroking_color = color
        return m

    def test_rectangle_converted(self) -> None:
        pts = [(100.0, 100.0), (200.0, 100.0), (200.0, 300.0), (100.0, 300.0), (100.0, 100.0)]
        geom = _lt_curve_to_raw_geometry(self._mock_curve(pts))
        assert geom is not None
        assert geom.is_closed
        assert len(geom.coordinates) == 4  # closing point removed

    def test_open_path(self) -> None:
        pts = [(0.0, 0.0), (100.0, 50.0), (200.0, 0.0)]
        geom = _lt_curve_to_raw_geometry(self._mock_curve(pts))
        assert geom is not None
        assert not geom.is_closed
        assert len(geom.coordinates) == 3

    def test_single_point_returns_none(self) -> None:
        geom = _lt_curve_to_raw_geometry(self._mock_curve([(0.0, 0.0)]))
        assert geom is None

    def test_empty_pts_returns_none(self) -> None:
        geom = _lt_curve_to_raw_geometry(self._mock_curve([]))
        assert geom is None

    def test_color_is_extracted(self) -> None:
        pts = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)]
        geom = _lt_curve_to_raw_geometry(self._mock_curve(pts, color=[1.0, 0.0, 0.0]))
        assert geom is not None
        assert geom.color == (255, 0, 0)

    def test_layer_argument(self) -> None:
        pts = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)]
        geom = _lt_curve_to_raw_geometry(self._mock_curve(pts), layer="A-WALL")
        assert geom is not None
        assert geom.layer == "A-WALL"


# ── NORMALIZER BASE HELPERS ───────────────────────────────────────────────────

class TestBasePDFNormalizerHelpers:
    """Tests shared helper methods via a concrete subclass."""

    _normalizer = AutoCADPDFNormalizer()

    def test_remove_degenerate_drops_single_point(self) -> None:
        geoms = [_make_geom([(0.0, 0.0), (0.0, 0.0)])]  # all same
        result = self._normalizer._remove_degenerate(geoms)
        assert result == []

    def test_remove_degenerate_keeps_valid(self) -> None:
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)])]
        assert self._normalizer._remove_degenerate(geoms) == geoms

    def test_deduplicate_removes_exact_copy(self) -> None:
        g = _make_geom([(0.0, 0.0), (100.0, 0.0)])
        result = self._normalizer._deduplicate([g, g])
        assert len(result) == 1

    def test_deduplicate_keeps_different(self) -> None:
        g1 = _make_geom([(0.0, 0.0), (100.0, 0.0)])
        g2 = _make_geom([(0.0, 0.0), (200.0, 0.0)])
        assert len(self._normalizer._deduplicate([g1, g2])) == 2


# ── AUTOCAD NORMALIZER ────────────────────────────────────────────────────────

class TestAutoCADNormalizer:
    _n = AutoCADPDFNormalizer()

    def test_excludes_titleblk_layer(self) -> None:
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)], layer="TITLEBLK")]
        assert self._n.normalize(geoms) == []

    def test_excludes_border_layer(self) -> None:
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)], layer="BORDER")]
        assert self._n.normalize(geoms) == []

    def test_keeps_facade_layer(self) -> None:
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)], layer="A-WALL")]
        assert len(self._n.normalize(geoms)) == 1

    def test_case_insensitive_exclusion(self) -> None:
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)], layer="titleblk")]
        assert self._n.normalize(geoms) == []

    def test_empty_layer_kept(self) -> None:
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)], layer="")]
        assert len(self._n.normalize(geoms)) == 1


# ── REVIT NORMALIZER ──────────────────────────────────────────────────────────

class TestRevitNormalizer:
    def test_warns_when_no_layer_names(self) -> None:
        n = RevitPDFNormalizer(warn_on_no_layers=True)
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)])]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            n.normalize(geoms)
        assert len(w) == 1
        assert "RISK-PDF-001" in str(w[0].message)

    def test_no_warning_when_layers_present(self) -> None:
        n = RevitPDFNormalizer()
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)], layer="Walls")]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            n.normalize(geoms)
        assert len(w) == 0

    def test_excludes_title_block_layer(self) -> None:
        n = RevitPDFNormalizer(warn_on_no_layers=False)
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)], layer="Title Block")]
        assert n.normalize(geoms) == []


# ── ARCHICAD NORMALIZER ───────────────────────────────────────────────────────

class TestArchiCADNormalizer:
    _n = ArchiCADPDFNormalizer()

    def test_excludes_stempel(self) -> None:
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)], layer="Stempel")]
        assert self._n.normalize(geoms) == []

    def test_excludes_schriftfeld(self) -> None:
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)], layer="Schriftfeld")]
        assert self._n.normalize(geoms) == []

    def test_keeps_facade_geometry(self) -> None:
        geoms = [_make_geom([(0.0, 0.0), (1000.0, 0.0)], layer="Fassade")]
        assert len(self._n.normalize(geoms)) == 1


# ── GENERIC NORMALIZER ────────────────────────────────────────────────────────

class TestGenericNormalizer:
    def test_warns_always(self) -> None:
        n = GenericPDFNormalizer()
        geoms = [_make_geom([(0.0, 0.0), (100.0, 0.0)])]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            n.normalize(geoms)
        assert len(w) == 1

    def test_keeps_all_layers(self) -> None:
        n = GenericPDFNormalizer()
        assert n.should_include_layer("ANY_LAYER")
        assert n.should_include_layer("")


# ── NORMALIZER FACTORY ────────────────────────────────────────────────────────

class TestNormalizerFactory:
    def test_autocad_source(self) -> None:
        assert isinstance(get_normalizer(PDFSource.AUTOCAD), AutoCADPDFNormalizer)

    def test_revit_source(self) -> None:
        assert isinstance(get_normalizer(PDFSource.REVIT), RevitPDFNormalizer)

    def test_archicad_source(self) -> None:
        assert isinstance(get_normalizer(PDFSource.ARCHICAD), ArchiCADPDFNormalizer)

    def test_generic_source(self) -> None:
        assert isinstance(get_normalizer(PDFSource.GENERIC), GenericPDFNormalizer)


# ── PDF SOURCE DETECTOR ───────────────────────────────────────────────────────

class TestPDFSourceDetector:
    _d = PDFSourceDetector()

    def test_detects_autocad(self) -> None:
        assert self._d.detect(_AUTOCAD_PDF) == PDFSource.AUTOCAD

    def test_detects_revit(self) -> None:
        assert self._d.detect(_REVIT_PDF) == PDFSource.REVIT

    def test_detects_archicad(self) -> None:
        assert self._d.detect(_ARCHICAD_PDF) == PDFSource.ARCHICAD

    def test_generic_for_unknown(self) -> None:
        assert self._d.detect(_GENERIC_PDF) == PDFSource.GENERIC

    def test_missing_file_returns_generic(self) -> None:
        result = self._d.detect(Path("/nonexistent/file.pdf"))
        assert result == PDFSource.GENERIC


# ── PDF IMPORT ADAPTER ────────────────────────────────────────────────────────

class TestPDFImportAdapter:
    def test_import_returns_facade_plan(self) -> None:
        adapter = PDFImportAdapter()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            plan = adapter.import_plan(_GENERIC_PDF, "Test Plan")
        assert plan.name == "Test Plan"
        assert plan.source_path == str(_GENERIC_PDF)

    def test_import_has_one_page(self) -> None:
        adapter = PDFImportAdapter()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            plan = adapter.import_plan(_GENERIC_PDF, "Test")
        assert plan.page_count == 1

    def test_import_extracts_geometry(self) -> None:
        adapter = PDFImportAdapter()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            plan = adapter.import_plan(_GENERIC_PDF, "Test")
        assert plan.total_geometry_count > 0

    def test_import_autocad_sets_source(self) -> None:
        adapter = PDFImportAdapter()
        plan = adapter.import_plan(_AUTOCAD_PDF, "AutoCAD Plan")
        assert plan.pdf_source == PDFSource.AUTOCAD

    def test_import_revit_sets_source(self) -> None:
        adapter = PDFImportAdapter()
        plan = adapter.import_plan(_REVIT_PDF, "Revit Plan")
        assert plan.pdf_source == PDFSource.REVIT

    def test_import_empty_page_returns_empty_geometries(self) -> None:
        adapter = PDFImportAdapter()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            plan = adapter.import_plan(_EMPTY_PDF, "Empty")
        assert plan.total_geometry_count == 0

    def test_rect_with_opening_extracts_multiple_paths(self) -> None:
        adapter = PDFImportAdapter()
        plan = adapter.import_plan(_OPENING_PDF, "With Opening")
        assert plan.total_geometry_count >= 2

    def test_page_dimensions_match_mediabox(self) -> None:
        adapter = PDFImportAdapter()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            plan = adapter.import_plan(_GENERIC_PDF, "Dims")
        page = plan.pages[0]
        assert page.width_pdf == pytest.approx(595.0, abs=1.0)
        assert page.height_pdf == pytest.approx(842.0, abs=1.0)

    def test_plan_id_is_unique(self) -> None:
        adapter = PDFImportAdapter()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            p1 = adapter.import_plan(_GENERIC_PDF, "A")
            p2 = adapter.import_plan(_GENERIC_PDF, "B")
        assert p1.id != p2.id


# ── FILE FACADE PLAN REPOSITORY ───────────────────────────────────────────────

class TestFileFacadePlanRepository:
    def test_save_and_load(self, tmp_path: Path) -> None:
        adapter = PDFImportAdapter()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            plan = adapter.import_plan(_GENERIC_PDF, "Persisted Plan")

        repo = FileFacadePlanRepository(tmp_path / "plans")
        repo.save(plan)
        loaded = repo.load(plan.id)

        assert loaded.id == plan.id
        assert loaded.name == plan.name
        assert loaded.page_count == plan.page_count

    def test_load_missing_raises(self, tmp_path: Path) -> None:
        from facade_planner.domain.exceptions import EntityNotFoundError
        repo = FileFacadePlanRepository(tmp_path / "plans")
        with pytest.raises(EntityNotFoundError):
            repo.load("nonexistent-id")

    def test_list_all_empty(self, tmp_path: Path) -> None:
        repo = FileFacadePlanRepository(tmp_path / "plans")
        assert repo.list_all() == []

    def test_list_all_returns_saved_plans(self, tmp_path: Path) -> None:
        adapter = PDFImportAdapter()
        repo = FileFacadePlanRepository(tmp_path / "plans")
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            p1 = adapter.import_plan(_GENERIC_PDF, "Plan A")
            p2 = adapter.import_plan(_GENERIC_PDF, "Plan B")
        repo.save(p1)
        repo.save(p2)
        plans = repo.list_all()
        assert len(plans) == 2
        ids = {p.id for p in plans}
        assert p1.id in ids and p2.id in ids

    def test_delete_removes_file(self, tmp_path: Path) -> None:
        adapter = PDFImportAdapter()
        repo = FileFacadePlanRepository(tmp_path / "plans")
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            plan = adapter.import_plan(_GENERIC_PDF, "To Delete")
        repo.save(plan)
        repo.delete(plan.id)
        assert repo.list_all() == []

"""Unit tests for EPIC-003 — Surface Detection.

Covers: SurfaceDetectionService, SurfaceDetectionConfig, DetectSurfacesUseCase,
        FileFacadeSurfaceRepository, surface CLI commands.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from facade_planner.application.use_cases.detect_surfaces import DetectSurfacesUseCase
from facade_planner.cli.main import app
from facade_planner.domain.entities.facade_plan import FacadePlan, PlanPage
from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.enums import SurfaceStatus
from facade_planner.domain.exceptions import DomainRuleError, EntityNotFoundError
from facade_planner.domain.services.surface_detection_service import (
    SurfaceDetectionConfig,
    SurfaceDetectionService,
    _exterior_coords,
    _try_gap_close,
    _try_polygon,
)
from facade_planner.domain.value_objects.raw_geometry import RawGeometry
from facade_planner.domain.value_objects.scale_calibration import ScaleCalibration
from facade_planner.domain.enums import ScaleMethod
from facade_planner.infrastructure.persistence.facade_surface_repository import (
    FileFacadeSurfaceRepository,
)


# ── HELPERS ──────────────────────────────────────────────────────────────────

def _rect_coords(x: float, y: float, w: float, h: float) -> list[tuple[float, float]]:
    """Return a closed rectangular path (4 unique corners, no closing duplicate)."""
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _rect_geom(
    x: float, y: float, w: float, h: float, is_closed: bool = True
) -> RawGeometry:
    return RawGeometry(coordinates=_rect_coords(x, y, w, h), is_closed=is_closed)


def _large_rect(is_closed: bool = True) -> RawGeometry:
    """4 m × 3 m rectangle → 12 000 000 mm² > default min_area."""
    return _rect_geom(0, 0, 4000, 3000, is_closed=is_closed)


def _small_rect(is_closed: bool = True) -> RawGeometry:
    """100 mm × 100 mm → 10 000 mm² < default min_area."""
    return _rect_geom(0, 0, 100, 100, is_closed=is_closed)


def _make_plan(
    geometries: list[RawGeometry],
    is_calibrated: bool = True,
    page_number: int = 1,
) -> FacadePlan:
    calibration = ScaleCalibration(
        method=ScaleMethod.DIRECT,
        factor=35.278,
        description="1:100",
    )
    page = PlanPage(
        page_number=page_number,
        width_pdf=595.0,
        height_pdf=842.0,
        geometries=geometries,
        calibration=calibration if is_calibrated else None,
        is_calibrated=is_calibrated,
    )
    return FacadePlan(
        id=str(uuid.uuid4()),
        name="Test Plan",
        source_path="/tmp/test.pdf",
        pages=[page],
    )


# ── _try_polygon ──────────────────────────────────────────────────────────────

class TestTryPolygon:
    def test_valid_rectangle(self) -> None:
        coords = _rect_coords(0, 0, 1000, 500)
        poly = _try_polygon(coords)
        assert poly is not None
        assert poly.area == pytest.approx(500_000.0)

    def test_too_few_points_returns_none(self) -> None:
        assert _try_polygon([(0, 0), (1, 1)]) is None

    def test_degenerate_all_same_returns_none(self) -> None:
        assert _try_polygon([(0, 0), (0, 0), (0, 0)]) is None

    def test_closing_duplicate_is_stripped(self) -> None:
        coords = [(0, 0), (1000, 0), (1000, 500), (0, 500), (0, 0)]
        poly = _try_polygon(coords)
        assert poly is not None
        assert poly.area == pytest.approx(500_000.0)

    def test_triangle(self) -> None:
        poly = _try_polygon([(0, 0), (1000, 0), (500, 1000)])
        assert poly is not None
        assert poly.area > 0


# ── _try_gap_close ────────────────────────────────────────────────────────────

class TestTryGapClose:
    def test_within_tolerance_closes(self) -> None:
        coords = [(0, 0), (1000, 0), (1000, 500), (0.3, 0.3)]  # gap ≈ 0.42 mm
        poly = _try_gap_close(coords, tolerance_mm=0.5)
        assert poly is not None

    def test_outside_tolerance_returns_none(self) -> None:
        coords = [(0, 0), (1000, 0), (1000, 500), (10, 10)]  # gap ≈ 14 mm
        poly = _try_gap_close(coords, tolerance_mm=0.5)
        assert poly is None

    def test_too_few_points_returns_none(self) -> None:
        assert _try_gap_close([(0, 0), (1, 0)], 1.0) is None

    def test_exact_closure_returns_polygon(self) -> None:
        coords = [(0, 0), (1000, 0), (1000, 500), (0, 0)]
        poly = _try_gap_close(coords, tolerance_mm=0.5)
        assert poly is not None


# ── SurfaceDetectionService ───────────────────────────────────────────────────

class TestSurfaceDetectionService:
    def _svc(self, min_area: float = 100_000.0) -> SurfaceDetectionService:
        return SurfaceDetectionService(SurfaceDetectionConfig(min_area_mm2=min_area))

    def test_single_large_closed_rect(self) -> None:
        geoms = [_large_rect()]
        surfaces = self._svc().detect("plan-1", 1, geoms)
        assert len(surfaces) == 1

    def test_small_rect_filtered_out(self) -> None:
        geoms = [_small_rect()]
        surfaces = self._svc().detect("plan-1", 1, geoms)
        assert len(surfaces) == 0

    def test_open_rect_skipped_without_gap_tolerance(self) -> None:
        geoms = [_large_rect(is_closed=False)]
        surfaces = self._svc().detect("plan-1", 1, geoms)
        assert len(surfaces) == 0

    def test_nearly_closed_rect_within_gap_tolerance(self) -> None:
        # 5-point path, last vertex (0.3, 0.2) is ≈0.36mm from first (0, 0) → within 0.5mm
        # Using a 5-point path avoids the last point landing on another edge (which makes Shapely invalid)
        coords = [(0, 0), (4000, 0), (4000, 3000), (0, 3000), (0.3, 0.2)]
        geom = RawGeometry(coordinates=coords, is_closed=False)
        svc = SurfaceDetectionService(
            SurfaceDetectionConfig(min_area_mm2=100_000.0, gap_tolerance_mm=0.5)
        )
        surfaces = svc.detect("plan-1", 1, [geom])
        assert len(surfaces) == 1

    def test_surfaces_sorted_largest_first(self) -> None:
        # Rects must NOT overlap — overlapping inner rect would be treated as duplicate
        big = _rect_geom(0, 0, 5000, 4000)    # 20 000 000 mm²
        small = _rect_geom(6000, 0, 1500, 500)  # 750 000 mm²  — no overlap with big
        surfaces = self._svc().detect("plan-1", 1, [small, big])
        assert len(surfaces) == 2
        assert surfaces[0].gross_area_mm2 > surfaces[1].gross_area_mm2

    def test_duplicate_polygons_deduplicated(self) -> None:
        geom1 = _large_rect()
        # near-identical rect (1mm offset) — should be treated as duplicate
        geom2 = _rect_geom(0, 0, 4001, 3000)
        surfaces = self._svc().detect("plan-1", 1, [geom1, geom2])
        assert len(surfaces) == 1

    def test_two_distinct_surfaces(self) -> None:
        rect_a = _rect_geom(0, 0, 4000, 3000)
        rect_b = _rect_geom(5000, 0, 4000, 3000)
        surfaces = self._svc().detect("plan-1", 1, [rect_a, rect_b])
        assert len(surfaces) == 2

    def test_returns_facade_surface_objects(self) -> None:
        surfaces = self._svc().detect("plan-1", 1, [_large_rect()])
        s = surfaces[0]
        assert isinstance(s, FacadeSurface)
        assert s.status == SurfaceStatus.DETECTED
        assert s.plan_id == "plan-1"
        assert s.page_number == 1

    def test_surface_has_boundary_coords(self) -> None:
        surfaces = self._svc().detect("plan-1", 1, [_large_rect()])
        assert len(surfaces[0].boundary) >= 3

    def test_surface_area_matches_input_rect(self) -> None:
        surfaces = self._svc().detect("plan-1", 1, [_large_rect()])
        assert surfaces[0].gross_area_mm2 == pytest.approx(12_000_000.0, rel=0.01)

    def test_max_area_filter(self) -> None:
        svc = SurfaceDetectionService(
            SurfaceDetectionConfig(min_area_mm2=0, max_area_mm2=500_000)
        )
        small = _rect_geom(0, 0, 500, 500)   # 250 000 mm²
        big = _large_rect()                   # 12 000 000 mm²
        surfaces = svc.detect("plan-1", 1, [small, big])
        assert len(surfaces) == 1
        assert surfaces[0].gross_area_mm2 < 500_001

    def test_empty_geometry_list(self) -> None:
        surfaces = self._svc().detect("plan-1", 1, [])
        assert surfaces == []

    def test_each_surface_has_unique_id(self) -> None:
        rect_a = _rect_geom(0, 0, 4000, 3000)
        rect_b = _rect_geom(5000, 0, 4000, 3000)
        surfaces = self._svc().detect("plan-1", 1, [rect_a, rect_b])
        assert surfaces[0].id != surfaces[1].id

    def test_default_config_min_area(self) -> None:
        svc = SurfaceDetectionService()
        cfg = svc._cfg
        assert cfg.min_area_mm2 == 100_000.0

    def test_pentagon_polygon(self) -> None:
        import math
        n = 5
        r = 1000.0  # radius in mm → area ≈ 2 378 000 mm²
        coords = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]
        geom = RawGeometry(coordinates=coords, is_closed=True)
        svc = SurfaceDetectionService(SurfaceDetectionConfig(min_area_mm2=100_000.0))
        surfaces = svc.detect("plan-1", 1, [geom])
        assert len(surfaces) == 1

    def test_non_closed_line_not_detected(self) -> None:
        line = RawGeometry(coordinates=[(0, 0), (5000, 0)], is_closed=False)
        surfaces = self._svc().detect("plan-1", 1, [line])
        assert surfaces == []


# ── DetectSurfacesUseCase ─────────────────────────────────────────────────────

class TestDetectSurfacesUseCase:
    def test_detect_from_calibrated_page(self) -> None:
        plan = _make_plan([_large_rect()])
        uc = DetectSurfacesUseCase()
        surfaces = uc.execute(plan, page_number=1)
        assert len(surfaces) == 1

    def test_uncalibrated_page_raises(self) -> None:
        plan = _make_plan([_large_rect()], is_calibrated=False)
        uc = DetectSurfacesUseCase()
        with pytest.raises(DomainRuleError, match="kalibriert"):
            uc.execute(plan, page_number=1)

    def test_missing_page_raises(self) -> None:
        plan = _make_plan([_large_rect()])
        uc = DetectSurfacesUseCase()
        with pytest.raises(EntityNotFoundError):
            uc.execute(plan, page_number=99)

    def test_custom_config_passed_through(self) -> None:
        geoms = [_small_rect()]
        plan = _make_plan(geoms)
        uc = DetectSurfacesUseCase()
        # with default config (min_area=100 000) small rect is filtered
        assert uc.execute(plan, 1) == []
        # with small min_area it passes
        cfg = SurfaceDetectionConfig(min_area_mm2=1_000)
        surfaces = uc.execute(plan, 1, config=cfg)
        assert len(surfaces) == 1

    def test_surface_linked_to_plan_id(self) -> None:
        plan = _make_plan([_large_rect()])
        uc = DetectSurfacesUseCase()
        surfaces = uc.execute(plan, 1)
        assert surfaces[0].plan_id == plan.id


# ── FileFacadeSurfaceRepository ───────────────────────────────────────────────

class TestFileFacadeSurfaceRepository:
    def _make_surface(self, surface_id: str = "surf-001") -> FacadeSurface:
        return FacadeSurface(
            id=surface_id,
            plan_id="plan-001",
            page_number=1,
            boundary=_rect_coords(0, 0, 4000, 3000),
            status=SurfaceStatus.DETECTED,
        )

    def test_save_creates_file(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        repo.save(self._make_surface())
        assert (tmp_path / "surf-001.json").exists()

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        s = self._make_surface()
        repo.save(s)
        loaded = repo.load("surf-001")
        assert loaded.id == s.id
        assert loaded.plan_id == s.plan_id
        assert loaded.page_number == s.page_number
        assert len(loaded.boundary) == 4

    def test_load_missing_raises(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        with pytest.raises(EntityNotFoundError):
            repo.load("nonexistent")

    def test_list_all_empty(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path / "nonexistent")
        assert repo.list_all() == []

    def test_list_all_returns_saved(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        repo.save(self._make_surface("surf-001"))
        repo.save(self._make_surface("surf-002"))
        surfaces = repo.list_all()
        assert len(surfaces) == 2

    def test_list_by_plan_filters(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        s1 = FacadeSurface(id="s1", plan_id="plan-A", page_number=1, boundary=_rect_coords(0,0,100,100))
        s2 = FacadeSurface(id="s2", plan_id="plan-B", page_number=1, boundary=_rect_coords(0,0,100,100))
        repo.save(s1)
        repo.save(s2)
        result = repo.list_by_plan("plan-A")
        assert len(result) == 1
        assert result[0].plan_id == "plan-A"

    def test_exists_false_before_save(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        assert not repo.exists("surf-001")

    def test_exists_true_after_save(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        repo.save(self._make_surface())
        assert repo.exists("surf-001")

    def test_delete_removes_file(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        repo.save(self._make_surface())
        repo.delete("surf-001")
        assert not repo.exists("surf-001")

    def test_delete_missing_raises(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        with pytest.raises(EntityNotFoundError):
            repo.delete("nonexistent")

    def test_confirm_status_persisted(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        s = self._make_surface()
        s.confirm(zone_id="zone-001")
        repo.save(s)
        loaded = repo.load("surf-001")
        assert loaded.status == SurfaceStatus.CONFIRMED
        assert loaded.zone_id == "zone-001"

    def test_reject_status_persisted(self, tmp_path: Path) -> None:
        repo = FileFacadeSurfaceRepository(tmp_path)
        s = self._make_surface()
        s.reject(reason="Titelblock")
        repo.save(s)
        loaded = repo.load("surf-001")
        assert loaded.status == SurfaceStatus.REJECTED
        assert loaded.reject_reason == "Titelblock"


# ── CLI — surface commands ────────────────────────────────────────────────────

@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _setup_project_with_calibrated_plan(
    tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> str:
    """Creates project + saves a calibrated plan; returns plan_id."""
    from facade_planner.infrastructure.persistence.facade_plan_repository import (
        FileFacadePlanRepository,
    )

    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)

    geoms = [_large_rect()]
    plan = _make_plan(geoms)

    plans_dir = tmp_path / ".facadeplanner" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    FileFacadePlanRepository(plans_dir).save(plan)
    return plan.id


class TestSurfaceCLI:
    def test_detect_basic(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plan_id = _setup_project_with_calibrated_plan(tmp_path, runner, monkeypatch)
        result = runner.invoke(
            app, ["surface", "detect", plan_id, "--min-area", "100000"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "gespeichert" in result.output

    def test_detect_saves_surfaces(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plan_id = _setup_project_with_calibrated_plan(tmp_path, runner, monkeypatch)
        runner.invoke(
            app, ["surface", "detect", plan_id, "--min-area", "100000"],
            catch_exceptions=False,
        )
        surfaces_dir = tmp_path / ".facadeplanner" / "surfaces"
        assert surfaces_dir.exists()
        assert len(list(surfaces_dir.glob("*.json"))) >= 1

    def test_detect_no_surfaces_message(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plan_id = _setup_project_with_calibrated_plan(tmp_path, runner, monkeypatch)
        # Set min_area very high so nothing is detected
        result = runner.invoke(
            app, ["surface", "detect", plan_id, "--min-area", "999999999"],
        )
        assert result.exit_code == 0
        assert "Keine Flächen erkannt" in result.output

    def test_detect_uncalibrated_plan_fails(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from facade_planner.infrastructure.persistence.facade_plan_repository import (
            FileFacadePlanRepository,
        )
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)

        plan = _make_plan([_large_rect()], is_calibrated=False)
        plans_dir = tmp_path / ".facadeplanner" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        FileFacadePlanRepository(plans_dir).save(plan)

        result = runner.invoke(app, ["surface", "detect", plan.id])
        assert result.exit_code != 0
        assert "kalibriert" in result.output

    def test_detect_missing_plan_fails(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        result = runner.invoke(app, ["surface", "detect", "nonexistent-plan-id"])
        assert result.exit_code != 0

    def test_list_empty(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        result = runner.invoke(app, ["surface", "list"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Keine Flächen" in result.output

    def test_list_shows_detected(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plan_id = _setup_project_with_calibrated_plan(tmp_path, runner, monkeypatch)
        runner.invoke(
            app, ["surface", "detect", plan_id, "--min-area", "100000"],
            catch_exceptions=False,
        )
        result = runner.invoke(app, ["surface", "list"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "DETECTED" in result.output

    def test_confirm_changes_status(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plan_id = _setup_project_with_calibrated_plan(tmp_path, runner, monkeypatch)
        runner.invoke(
            app, ["surface", "detect", plan_id, "--min-area", "100000"],
            catch_exceptions=False,
        )
        surfaces_dir = tmp_path / ".facadeplanner" / "surfaces"
        surf_file = next(surfaces_dir.glob("*.json"))
        surf_id = surf_file.stem

        result = runner.invoke(app, ["surface", "confirm", surf_id], catch_exceptions=False)
        assert result.exit_code == 0
        assert "bestätigt" in result.output

        loaded = FileFacadeSurfaceRepository(surfaces_dir).load(surf_id)
        assert loaded.status == SurfaceStatus.CONFIRMED

    def test_reject_changes_status(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plan_id = _setup_project_with_calibrated_plan(tmp_path, runner, monkeypatch)
        runner.invoke(
            app, ["surface", "detect", plan_id, "--min-area", "100000"],
            catch_exceptions=False,
        )
        surfaces_dir = tmp_path / ".facadeplanner" / "surfaces"
        surf_file = next(surfaces_dir.glob("*.json"))
        surf_id = surf_file.stem

        result = runner.invoke(
            app, ["surface", "reject", surf_id, "--reason", "Titelblock"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        loaded = FileFacadeSurfaceRepository(surfaces_dir).load(surf_id)
        assert loaded.status == SurfaceStatus.REJECTED
        assert loaded.reject_reason == "Titelblock"

    def test_list_filter_by_status(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plan_id = _setup_project_with_calibrated_plan(tmp_path, runner, monkeypatch)
        runner.invoke(
            app, ["surface", "detect", plan_id, "--min-area", "100000"],
            catch_exceptions=False,
        )
        result = runner.invoke(
            app, ["surface", "list", "--status", "CONFIRMED"], catch_exceptions=False
        )
        assert result.exit_code == 0
        assert "Keine Flächen" in result.output

    def test_confirm_missing_surface_fails(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        result = runner.invoke(app, ["surface", "confirm", "nonexistent-id"])
        assert result.exit_code != 0

    def test_requires_project(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["surface", "list"])
        assert result.exit_code != 0

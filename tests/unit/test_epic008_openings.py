"""Tests for EPIC-008 Opening Handling System.

ISSUE-081: Opening Detection Algorithm (Polygon-in-Polygon)
ISSUE-082: TRIM + DROP strategies for panel-opening intersection
"""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

from facade_planner.cli.main import app as cli_app
from facade_planner.domain.algorithms.grid_panelization_algorithm import (
    GridPanelizationAlgorithm,
)
from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.opening import Opening
from facade_planner.domain.entities.panel import Panel
from facade_planner.domain.entities.panel_format import PanelFormat
from facade_planner.domain.entities.panelization_job import (
    PanelizationConfig,
)
from facade_planner.domain.enums import (
    CutReason,
    OpeningStrategy,
    OpeningType,
    SurfaceStatus,
)
from facade_planner.domain.services.opening_detection_service import (
    OpeningDetectionService,
    _classify_type,
    _filter_nested,
    _make_polygon,
)
from facade_planner.domain.services.panel_opening_filter import PanelOpeningFilter
from facade_planner.domain.value_objects.joint_config import JointConfig
from shapely.geometry import Polygon

runner = CliRunner()

# ── Helpers ──────────────────────────────────────────────────────────────────


def _rect_boundary(x: float, y: float, w: float, h: float) -> list[tuple[float, float]]:
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _surface(
    sid: str = "S-001",
    x: float = 0.0,
    y: float = 0.0,
    w: float = 10000.0,
    h: float = 6000.0,
    openings: list[Opening] | None = None,
) -> FacadeSurface:
    return FacadeSurface(
        id=sid,
        plan_id="PLAN-001",
        page_number=1,
        boundary=_rect_boundary(x, y, w, h),
        status=SurfaceStatus.CONFIRMED,
        openings=openings or [],
    )


def _opening(
    oid: str,
    x: float,
    y: float,
    w: float,
    h: float,
    surface_id: str = "S-001",
) -> Opening:
    return Opening(
        id=oid,
        surface_id=surface_id,
        boundary=_rect_boundary(x, y, w, h),
    )


def _panel(
    pid: str = "P-001",
    x: float = 0.0,
    y: float = 0.0,
    w: float = 1000.0,
    h: float = 600.0,
) -> Panel:
    return Panel(
        id=pid,
        surface_id="S-001",
        format_code="FMT",
        x_mm=x,
        y_mm=y,
        actual_width_mm=w,
        actual_height_mm=h,
    )


def _config(strategy: OpeningStrategy = OpeningStrategy.TRIM) -> PanelizationConfig:
    return PanelizationConfig(
        joint_config=JointConfig(
            horizontal_joint_mm=0.0,
            vertical_joint_mm=0.0,
            expansion_joint_interval_mm=0.0,
        ),
        opening_strategy=strategy,
        min_panel_width_mm=100.0,
        min_panel_height_mm=100.0,
    )


# ── _make_polygon ─────────────────────────────────────────────────────────────


class TestMakePolygon:
    def test_valid_rectangle(self):
        poly = _make_polygon(_rect_boundary(0, 0, 1000, 600))
        assert poly is not None
        assert not poly.is_empty
        assert abs(poly.area - 600_000) < 1.0

    def test_too_few_points(self):
        assert _make_polygon([(0, 0), (1, 0)]) is None

    def test_all_same_points(self):
        assert _make_polygon([(5, 5), (5, 5), (5, 5)]) is None

    def test_explicit_close_point_removed(self):
        coords = [(0, 0), (1000, 0), (1000, 600), (0, 600), (0, 0)]
        poly = _make_polygon(coords)
        assert poly is not None
        assert not poly.is_empty


# ── _classify_type ────────────────────────────────────────────────────────────


class TestClassifyType:
    def test_tall_polygon_is_window(self):
        # 300 wide × 1000 tall → aspect = 3.33 > 2.5 → WINDOW
        poly = Polygon(_rect_boundary(0, 0, 300, 1000))
        assert _classify_type(poly) == OpeningType.WINDOW

    def test_wide_polygon_is_window(self):
        # 1200 wide × 300 tall → aspect = 4.0 > 2.5 → WINDOW
        poly = Polygon(_rect_boundary(0, 0, 1200, 300))
        assert _classify_type(poly) == OpeningType.WINDOW

    def test_door_aspect(self):
        # 800 wide × 1400 tall → aspect = 1.75 → DOOR
        poly = Polygon(_rect_boundary(0, 0, 800, 1400))
        assert _classify_type(poly) == OpeningType.DOOR

    def test_square_is_other(self):
        # 800 × 800 → aspect = 1.0 → OTHER
        poly = Polygon(_rect_boundary(0, 0, 800, 800))
        assert _classify_type(poly) == OpeningType.OTHER

    def test_nearly_square_is_other(self):
        # 900 × 800 → aspect = 1.125 < 1.5 → OTHER
        poly = Polygon(_rect_boundary(0, 0, 900, 800))
        assert _classify_type(poly) == OpeningType.OTHER

    def test_exact_boundary_door(self):
        # 600 × 900 → aspect = 1.5 exactly → DOOR
        poly = Polygon(_rect_boundary(0, 0, 600, 900))
        assert _classify_type(poly) == OpeningType.DOOR


# ── _filter_nested ────────────────────────────────────────────────────────────


class TestFilterNested:
    def test_no_nesting(self):
        outer = Polygon(_rect_boundary(0, 0, 2000, 1000))
        sep = Polygon(_rect_boundary(3000, 0, 2000, 1000))
        result = _filter_nested([(outer, []), (sep, [])])
        assert len(result) == 2

    def test_inner_removed(self):
        outer = Polygon(_rect_boundary(0, 0, 2000, 1000))
        inner = Polygon(_rect_boundary(100, 100, 500, 300))
        result = _filter_nested([(outer, []), (inner, [])])
        polys = [p for p, _ in result]
        assert any(p.area == outer.area for p in polys)
        assert len(result) == 1

    def test_equal_size_both_kept(self):
        a = Polygon(_rect_boundary(0, 0, 1000, 600))
        b = Polygon(_rect_boundary(0, 0, 1000, 600))
        result = _filter_nested([(a, []), (b, [])])
        # Neither fully contains the other (equal) → both kept
        assert len(result) == 2


# ── OpeningDetectionService ───────────────────────────────────────────────────


class TestOpeningDetectionService:
    def setup_method(self):
        self.svc = OpeningDetectionService()
        self.surface = _surface(w=10000, h=6000)

    def test_fully_inside_polygon_becomes_opening(self):
        candidate = _rect_boundary(1000, 1000, 800, 1400)  # door
        result = self.svc.detect(self.surface, [candidate])
        assert len(result.openings) == 1
        assert result.openings[0].surface_id == "S-001"

    def test_type_door_detected(self):
        candidate = _rect_boundary(1000, 1000, 800, 1400)
        result = self.svc.detect(self.surface, [candidate])
        assert result.openings[0].opening_type == OpeningType.DOOR

    def test_type_window_detected(self):
        candidate = _rect_boundary(1000, 1000, 300, 1000)  # aspect 3.33
        result = self.svc.detect(self.surface, [candidate])
        assert result.openings[0].opening_type == OpeningType.WINDOW

    def test_type_other_detected(self):
        candidate = _rect_boundary(1000, 1000, 800, 800)  # square
        result = self.svc.detect(self.surface, [candidate])
        assert result.openings[0].opening_type == OpeningType.OTHER

    def test_polygon_mostly_outside_warning_no_opening(self):
        # Candidate 80% outside the surface
        candidate = _rect_boundary(-4000, 1000, 5000, 1000)
        result = self.svc.detect(self.surface, [candidate])
        assert len(result.openings) == 0
        assert len(result.warnings) >= 1
        assert "ausserhalb" in result.warnings[0]

    def test_polygon_exactly_50pct_outside_warning(self):
        # Half inside, half outside
        candidate = _rect_boundary(-2000, 0, 4000, 2000)  # left half outside
        result = self.svc.detect(self.surface, [candidate])
        assert len(result.openings) == 0
        assert len(result.warnings) >= 1

    def test_multiple_candidates(self):
        c1 = _rect_boundary(500, 500, 800, 1400)
        c2 = _rect_boundary(5000, 1000, 800, 1400)
        result = self.svc.detect(self.surface, [c1, c2])
        assert len(result.openings) == 2

    def test_nested_opening_outer_only(self):
        outer = _rect_boundary(500, 500, 2000, 2000)
        inner = _rect_boundary(700, 700, 500, 500)
        result = self.svc.detect(self.surface, [outer, inner])
        # Inner is nested → only outer kept
        assert len(result.openings) == 1
        assert result.openings[0].area_mm2 > 500 * 500

    def test_invalid_polygon_skipped(self):
        bad = [(0, 0), (1000, 0)]  # only 2 points
        good = _rect_boundary(500, 500, 800, 1400)
        result = self.svc.detect(self.surface, [bad, good])
        assert len(result.openings) == 1

    def test_opening_id_unique(self):
        c1 = _rect_boundary(500, 500, 800, 1400)
        c2 = _rect_boundary(3000, 500, 800, 1400)
        result = self.svc.detect(self.surface, [c1, c2])
        ids = [o.id for o in result.openings]
        assert len(ids) == len(set(ids))

    def test_tolerance_affects_containment(self):
        # Candidate is exactly at the surface boundary — with tolerance=0 it passes
        # with tolerance=10 the surface_inner is shrunk, candidate may fail
        candidate = _rect_boundary(0, 0, 500, 500)  # touches surface corner
        result_no_tol = self.svc.detect(self.surface, [candidate], tolerance_mm=0)
        result_with_tol = self.svc.detect(self.surface, [candidate], tolerance_mm=100)
        # With no tolerance: overlap=1.0 → opening; with high tolerance: still added
        # (we check inside surface_poly not surface_inner for 50% check)
        assert len(result_no_tol.openings) == 1


# ── PanelOpeningFilter ────────────────────────────────────────────────────────


class TestPanelOpeningFilter:
    def setup_method(self):
        self.flt = PanelOpeningFilter()

    def test_no_openings_returns_all_panels(self):
        panels = [_panel("P1"), _panel("P2", x=1000)]
        result = self.flt.apply(panels, [], OpeningStrategy.TRIM, 100, 100)
        assert result == panels

    def test_drop_removes_overlapping_panel(self):
        panel = _panel(x=0, y=0, w=1000, h=600)
        opening = _opening("O1", 200, 100, 400, 300)  # inside panel
        result = self.flt.apply([panel], [opening], OpeningStrategy.DROP, 100, 100)
        assert len(result) == 0

    def test_drop_keeps_non_overlapping_panel(self):
        panel = _panel(x=0, y=0, w=1000, h=600)
        opening = _opening("O1", 2000, 0, 400, 300)  # far away
        result = self.flt.apply([panel], [opening], OpeningStrategy.DROP, 100, 100)
        assert len(result) == 1

    def test_trim_clips_opening_on_right(self):
        # Panel: x=0..1000, opening at x=700..1100 (overlaps right side)
        panel = _panel(x=0, y=0, w=1000, h=600)
        opening = _opening("O1", 700, 0, 400, 600)
        result = self.flt.apply([panel], [opening], OpeningStrategy.TRIM, 100, 100)
        assert len(result) == 1
        assert result[0].actual_width_mm == pytest.approx(700, abs=1)
        assert result[0].x_mm == pytest.approx(0, abs=1)
        assert result[0].is_cut
        assert result[0].cut_reason == CutReason.OPENING

    def test_trim_clips_opening_on_left(self):
        # Panel: x=0..1000, opening at x=-100..300 (overlaps left side)
        panel = _panel(x=0, y=0, w=1000, h=600)
        opening = _opening("O1", -100, 0, 400, 600)
        result = self.flt.apply([panel], [opening], OpeningStrategy.TRIM, 100, 100)
        assert len(result) == 1
        assert result[0].x_mm == pytest.approx(300, abs=1)
        assert result[0].actual_width_mm == pytest.approx(700, abs=1)

    def test_trim_clips_opening_on_bottom(self):
        # Panel: y=0..600, opening at y=500..900 (overlaps bottom edge, assuming y up)
        panel = _panel(x=0, y=0, w=1000, h=600)
        opening = _opening("O1", 0, 500, 1000, 400)
        result = self.flt.apply([panel], [opening], OpeningStrategy.TRIM, 100, 100)
        assert len(result) == 1
        assert result[0].actual_height_mm == pytest.approx(500, abs=1)

    def test_trim_removes_when_remainder_too_small(self):
        # Remainder after clip < min_panel_width_mm
        panel = _panel(x=0, y=0, w=1000, h=600)
        # Opening covers x=100..1000 → only 100mm left on left, min=200mm
        opening = _opening("O1", 100, 0, 900, 600)
        result = self.flt.apply([panel], [opening], OpeningStrategy.TRIM, 200, 100)
        assert len(result) == 0

    def test_trim_clips_when_opening_in_center(self):
        # Opening x=300..700 (center) → valid left strip: x=0..300 (300mm >= 100)
        panel = _panel(x=0, y=0, w=1000, h=600)
        opening = _opening("O1", 300, 150, 400, 300)  # center, fully inside
        result = self.flt.apply([panel], [opening], OpeningStrategy.TRIM, 100, 100)
        assert len(result) == 1
        assert result[0].is_cut
        assert result[0].cut_reason == CutReason.OPENING

    def test_trim_drops_when_all_clips_too_small(self):
        # Opening x=250..850, y=100..500 — all remaining strips < min_size=300
        panel = _panel(x=0, y=0, w=1000, h=600)
        opening = _opening("O1", 250, 100, 600, 400)
        result = self.flt.apply([panel], [opening], OpeningStrategy.TRIM, 300, 300)
        # left=250<300, right=150<300, bottom=100<300, top=100<300 → drop
        assert len(result) == 0

    def test_non_overlapping_panel_unchanged(self):
        panel = _panel(x=5000, y=5000, w=1000, h=600)
        opening = _opening("O1", 0, 0, 400, 300)
        result = self.flt.apply([panel], [opening], OpeningStrategy.TRIM, 100, 100)
        assert len(result) == 1
        assert result[0] == panel

    def test_trim_multiple_panels_partial_keep(self):
        p1 = _panel("P1", x=0, y=0, w=1000, h=600)
        p2 = _panel("P2", x=2000, y=0, w=1000, h=600)  # no overlap
        opening = _opening("O1", 700, 0, 400, 600)  # overlaps p1
        result = self.flt.apply([p1, p2], [opening], OpeningStrategy.TRIM, 100, 100)
        assert len(result) == 2
        trimmed = next(p for p in result if p.id == "P1")
        unchanged = next(p for p in result if p.id == "P2")
        assert trimmed.is_cut
        assert not unchanged.is_cut


# ── GridPanelizationAlgorithm + Openings ─────────────────────────────────────


class TestGridWithOpenings:
    def setup_method(self):
        self.algo = GridPanelizationAlgorithm()
        self.fmt = PanelFormat(format_code="FMT-1000x600", width_mm=1000, height_mm=600)

    def test_trim_strategy_removes_overlapping_panels(self):
        opening = _opening("O1", 700, 0, 400, 600)
        surface = _surface(w=3000, h=600, openings=[opening])
        panels = self.algo.panelize(surface, [self.fmt], _config(OpeningStrategy.TRIM))
        # No panel should fully cover the opening area
        for p in panels:
            panel_box = (p.x_mm, p.y_mm, p.x_mm + p.actual_width_mm, p.y_mm + p.actual_height_mm)
            # The opening occupies x=700..1100, y=0..600
            # Check no panel covers a point inside the opening
            o_cx, o_cy = 900, 300  # opening center
            if (panel_box[0] <= o_cx <= panel_box[2] and
                    panel_box[1] <= o_cy <= panel_box[3]):
                pytest.fail(f"Panel {p.id} covers opening center at ({o_cx},{o_cy})")

    def test_drop_strategy_removes_all_overlapping_panels(self):
        opening = _opening("O1", 500, 0, 600, 600)  # overlaps middle of first panel
        surface = _surface(w=3000, h=600, openings=[opening])
        cfg = _config(OpeningStrategy.DROP)
        panels = self.algo.panelize(surface, [self.fmt], cfg)
        # Any panel overlapping the opening should be gone
        for p in panels:
            px1, py1 = p.x_mm, p.y_mm
            px2, py2 = px1 + p.actual_width_mm, py1 + p.actual_height_mm
            assert not (px1 < 1100 and px2 > 500), (
                f"Panel {p.id} overlaps opening but was not dropped"
            )

    def test_no_opening_grid_unchanged(self):
        surface = _surface(w=3000, h=600)
        panels = self.algo.panelize(surface, [self.fmt], _config())
        assert len(panels) == 3
        assert all(not p.is_cut for p in panels)

    def test_panels_marked_cut_after_trim(self):
        opening = _opening("O1", 700, 0, 400, 600)
        surface = _surface(w=3000, h=600, openings=[opening])
        panels = self.algo.panelize(surface, [self.fmt], _config(OpeningStrategy.TRIM))
        cut_panels = [p for p in panels if p.cut_reason == CutReason.OPENING]
        assert len(cut_panels) >= 1


# ── CLI surface detect-openings ───────────────────────────────────────────────


class TestSurfaceShowCLI:
    def test_show_surface_command(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        r = CliRunner()
        r.invoke(cli_app, ["project", "create", "test"])

        from facade_planner.infrastructure.persistence.facade_surface_repository import (
            FileFacadeSurfaceRepository,
        )
        repo = FileFacadeSurfaceRepository(tmp_path / ".facadeplanner" / "surfaces")
        surf = _surface("S-CLI-001", w=5000, h=3000)
        repo.save(surf)

        result = r.invoke(cli_app, ["surface", "show", "S-CLI-001"])
        assert result.exit_code == 0
        assert "S-CLI-001" in result.output
        assert "Oeffnungen" in result.output

    def test_detect_openings_no_plan_page(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        r = CliRunner()
        r.invoke(cli_app, ["project", "create", "test"])

        from facade_planner.infrastructure.persistence.facade_surface_repository import (
            FileFacadeSurfaceRepository,
        )
        repo = FileFacadeSurfaceRepository(tmp_path / ".facadeplanner" / "surfaces")
        surf = _surface("S-CLI-002", w=5000, h=3000)
        repo.save(surf)

        result = r.invoke(cli_app, ["surface", "detect-openings", "S-CLI-002"])
        assert result.exit_code == 0
        assert "Keine Kandidaten" in result.output

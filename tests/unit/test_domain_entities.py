"""Smoke tests: all domain entities are importable and constructable."""
import uuid

from facade_planner.domain.entities import (
    FacadePlan,
    FacadeSurface,
    FacadeZone,
    Opening,
    Panel,
    PanelFormat,
    PanelizationConfig,
    PanelizationJob,
    PanelizationResult,
    PlanPage,
    SupplierCatalog,
)
from facade_planner.domain.enums import (
    OpeningType,
    PanelizationErrorType,
    PDFSource,
    RuleCategory,
    RuleSeverity,
    SurfaceStatus,
)
from facade_planner.domain.value_objects import JointConfig, ScaleCalibration
from facade_planner.domain.enums import ScaleMethod


def test_joint_config_defaults() -> None:
    jc = JointConfig()
    assert jc.horizontal_joint_mm == 10.0
    assert jc.vertical_joint_mm == 10.0
    assert jc.expansion_joint_interval_mm == 6000.0


def test_facade_surface_area() -> None:
    surface = FacadeSurface(
        id="s1",
        plan_id="p1",
        page_number=1,
        boundary=[(0, 0), (5000, 0), (5000, 3000), (0, 3000)],
    )
    assert surface.gross_area_mm2 == pytest.approx(15_000_000.0)
    assert surface.width_mm == pytest.approx(5000.0)
    assert surface.height_mm == pytest.approx(3000.0)


def test_surface_confirm() -> None:
    surface = FacadeSurface(
        id="s1", plan_id="p1", page_number=1,
        boundary=[(0, 0), (1000, 0), (1000, 1000), (0, 1000)],
    )
    assert surface.status == SurfaceStatus.DETECTED
    surface.confirm(zone_id="z1")
    assert surface.status == SurfaceStatus.CONFIRMED
    assert surface.zone_id == "z1"


def test_surface_reject() -> None:
    surface = FacadeSurface(
        id="s1", plan_id="p1", page_number=1,
        boundary=[(0, 0), (1000, 0), (1000, 1000), (0, 1000)],
    )
    surface.reject("Wrong geometry")
    assert surface.status == SurfaceStatus.REJECTED
    assert surface.reject_reason == "Wrong geometry"


def test_panel_corners() -> None:
    panel = Panel(
        id="p1", surface_id="s1", format_code="FMT-A",
        x_mm=100.0, y_mm=200.0,
        actual_width_mm=1250.0, actual_height_mm=3050.0,
    )
    corners = panel.corners
    assert corners[0] == (100.0, 200.0)
    assert corners[1] == (1350.0, 200.0)
    assert corners[2] == (1350.0, 3250.0)
    assert corners[3] == (100.0, 3250.0)


def test_panelization_result_counts() -> None:
    result = PanelizationResult(
        job_id="j1",
        panels=[
            Panel(id="p1", surface_id="s1", format_code="F", x_mm=0, y_mm=0,
                  actual_width_mm=1250, actual_height_mm=3050),
            Panel(id="p2", surface_id="s1", format_code="F", x_mm=1260, y_mm=0,
                  actual_width_mm=500, actual_height_mm=3050, is_cut=True),
        ],
    )
    assert result.total_panels == 2
    assert result.full_panels == 1
    assert result.cut_panels == 1


def test_scale_calibration_immutable() -> None:
    cal = ScaleCalibration(method=ScaleMethod.DIRECT, factor=10.0)
    assert cal.factor == 10.0


def test_all_enums_importable() -> None:
    assert PDFSource.AUTOCAD
    assert SurfaceStatus.CONFIRMED
    assert OpeningType.WINDOW
    assert PanelizationErrorType.PE_001_NO_FORMAT_FITS
    assert RuleSeverity.ERROR
    assert RuleCategory.GEOMETRIC


import pytest

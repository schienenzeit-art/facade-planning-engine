"""Unit tests for EPIC-004 — Scale Calibration."""
import math
import uuid

import pytest
from typer.testing import CliRunner

from facade_planner.application.use_cases.calibrate_scale import (
    DirectScaleInputUseCase,
    TwoPointCalibrationUseCase,
    apply_calibration_to_plan,
)
from facade_planner.cli.main import app
from facade_planner.domain.entities.facade_plan import FacadePlan, PlanPage
from facade_planner.domain.enums import ScaleMethod
from facade_planner.domain.exceptions import DomainRuleError
from facade_planner.domain.value_objects.raw_geometry import RawGeometry
from facade_planner.domain.value_objects.scale_calibration import ScaleCalibration


# ── FIXTURES ─────────────────────────────────────────────────────────────────

@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def simple_page() -> PlanPage:
    return PlanPage(
        page_number=1,
        width_pdf=595.0,
        height_pdf=842.0,
        geometries=[
            RawGeometry(
                coordinates=((0.0, 0.0), (100.0, 0.0), (100.0, 50.0), (0.0, 50.0)),
                layer="FASSADE",
                is_closed=True,
            )
        ],
    )


@pytest.fixture
def simple_plan(simple_page: PlanPage) -> FacadePlan:
    return FacadePlan(
        id=str(uuid.uuid4()),
        name="Testplan",
        source_path="/tmp/test.pdf",
        pages=[simple_page],
    )


# ── TWO-POINT CALIBRATION ────────────────────────────────────────────────────

class TestTwoPointCalibrationUseCase:
    def test_correct_factor(self) -> None:
        uc = TwoPointCalibrationUseCase()
        cal = uc.execute(pdf_distance=100.0, real_distance_mm=6000.0)
        assert math.isclose(cal.factor, 60.0)

    def test_method_is_two_point(self) -> None:
        uc = TwoPointCalibrationUseCase()
        cal = uc.execute(100.0, 1000.0)
        assert cal.method == ScaleMethod.TWO_POINT

    def test_description_contains_values(self) -> None:
        uc = TwoPointCalibrationUseCase()
        cal = uc.execute(200.0, 6000.0)
        assert "6000" in cal.description
        assert "200" in cal.description

    def test_zero_pdf_distance_raises(self) -> None:
        uc = TwoPointCalibrationUseCase()
        with pytest.raises(DomainRuleError, match="pdf_distance"):
            uc.execute(0.0, 6000.0)

    def test_negative_pdf_distance_raises(self) -> None:
        uc = TwoPointCalibrationUseCase()
        with pytest.raises(DomainRuleError):
            uc.execute(-10.0, 6000.0)

    def test_zero_real_distance_raises(self) -> None:
        uc = TwoPointCalibrationUseCase()
        with pytest.raises(DomainRuleError, match="real_distance_mm"):
            uc.execute(100.0, 0.0)

    def test_result_is_frozen(self) -> None:
        uc = TwoPointCalibrationUseCase()
        cal = uc.execute(100.0, 6000.0)
        with pytest.raises(Exception):
            cal.factor = 1.0  # type: ignore[misc]


# ── DIRECT SCALE INPUT ────────────────────────────────────────────────────────

class TestDirectScaleInputUseCase:
    _MM_PER_POINT = 25.4 / 72  # ≈ 0.35278mm

    def test_factor_for_1_to_100(self) -> None:
        uc = DirectScaleInputUseCase()
        cal = uc.execute(100)
        expected = self._MM_PER_POINT * 100
        assert math.isclose(cal.factor, expected, rel_tol=1e-9)

    def test_factor_for_1_to_50(self) -> None:
        uc = DirectScaleInputUseCase()
        cal = uc.execute(50)
        expected = self._MM_PER_POINT * 50
        assert math.isclose(cal.factor, expected, rel_tol=1e-9)

    def test_method_is_direct(self) -> None:
        uc = DirectScaleInputUseCase()
        cal = uc.execute(100)
        assert cal.method == ScaleMethod.DIRECT

    def test_description_contains_ratio(self) -> None:
        uc = DirectScaleInputUseCase()
        cal = uc.execute(200)
        assert "1:200" in cal.description

    def test_zero_denominator_raises(self) -> None:
        uc = DirectScaleInputUseCase()
        with pytest.raises(DomainRuleError, match="scale_denominator"):
            uc.execute(0)

    def test_negative_denominator_raises(self) -> None:
        uc = DirectScaleInputUseCase()
        with pytest.raises(DomainRuleError):
            uc.execute(-100)


# ── APPLY CALIBRATION TO PLAN ─────────────────────────────────────────────────

class TestApplyCalibrationToPlan:
    def test_scales_coordinates(self, simple_plan: FacadePlan) -> None:
        cal = ScaleCalibration(method=ScaleMethod.DIRECT, factor=10.0)
        apply_calibration_to_plan(simple_plan, page_number=1, calibration=cal)
        geom = simple_plan.pages[0].geometries[0]
        assert geom.coordinates[1][0] == pytest.approx(1000.0)  # 100 * 10

    def test_marks_page_as_calibrated(self, simple_plan: FacadePlan) -> None:
        cal = ScaleCalibration(method=ScaleMethod.DIRECT, factor=10.0)
        apply_calibration_to_plan(simple_plan, page_number=1, calibration=cal)
        assert simple_plan.pages[0].is_calibrated

    def test_stores_calibration_on_page(self, simple_plan: FacadePlan) -> None:
        cal = ScaleCalibration(method=ScaleMethod.TWO_POINT, factor=5.0)
        apply_calibration_to_plan(simple_plan, page_number=1, calibration=cal)
        assert simple_plan.pages[0].calibration == cal

    def test_double_calibration_raises(self, simple_plan: FacadePlan) -> None:
        cal = ScaleCalibration(method=ScaleMethod.DIRECT, factor=10.0)
        apply_calibration_to_plan(simple_plan, page_number=1, calibration=cal)
        with pytest.raises(DomainRuleError, match="bereits kalibriert"):
            apply_calibration_to_plan(simple_plan, page_number=1, calibration=cal)

    def test_missing_page_raises(self, simple_plan: FacadePlan) -> None:
        cal = ScaleCalibration(method=ScaleMethod.DIRECT, factor=10.0)
        with pytest.raises(DomainRuleError, match="Seite 99"):
            apply_calibration_to_plan(simple_plan, page_number=99, calibration=cal)


# ── CLI: facade plan scale ────────────────────────────────────────────────────

class TestPlanScaleCLI:
    def test_direct_ratio_no_project(
        self, runner: CliRunner, tmp_path: "Path", monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["plan", "scale", "--ratio", "100"], catch_exceptions=False)
        assert result.exit_code != 0

    def test_missing_args_exits_error(
        self, runner: CliRunner, tmp_path: "Path", monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"])
        result = runner.invoke(app, ["plan", "scale"])
        assert result.exit_code != 0

    def test_direct_ratio_with_project(
        self, runner: CliRunner, tmp_path: "Path", monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        result = runner.invoke(app, ["plan", "scale", "--ratio", "100"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "DIRECT" in result.output or "1:100" in result.output

    def test_two_point_with_project(
        self, runner: CliRunner, tmp_path: "Path", monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        result = runner.invoke(
            app,
            ["plan", "scale", "--pdf-dist", "283.5", "--real-dist", "6000"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "TWO_POINT" in result.output or "6000" in result.output

"""Scale calibration use cases for EPIC-004.

Two modes:
- DirectScaleInputUseCase: user provides the scale factor directly (e.g. 1:100 → factor=1000/10 = ...)
  Actually: user provides scale denominator (e.g. 100 for 1:100) and pdf unit size in points.
  Simpler: user provides mm_per_pdf_unit directly.
- TwoPointCalibrationUseCase: user measures a known distance in PDF units and provides real mm value.
"""
import math

from facade_planner.domain.enums import ScaleMethod
from facade_planner.domain.entities.facade_plan import FacadePlan, PlanPage
from facade_planner.domain.exceptions import DomainRuleError
from facade_planner.domain.value_objects.scale_calibration import ScaleCalibration


class TwoPointCalibrationUseCase:
    """Compute ScaleCalibration from a known real-world distance and its PDF-unit measurement.

    Typical flow:
        1. User picks two recognizable points on the plan (e.g. column grid 6000mm apart).
        2. CLI or upstream tool measures the distance between those points in PDF units.
        3. User supplies the real distance in mm.
        4. This use case computes factor = real_mm / pdf_units.
    """

    def execute(
        self,
        pdf_distance: float,
        real_distance_mm: float,
    ) -> ScaleCalibration:
        """Return a ScaleCalibration for the measured segment.

        Args:
            pdf_distance: distance between the two points as measured in PDF coordinate units.
            real_distance_mm: actual distance in millimetres.

        Raises:
            DomainRuleError: if either argument is non-positive.
        """
        if pdf_distance <= 0:
            raise DomainRuleError(
                f"pdf_distance muss positiv sein, erhalten: {pdf_distance}"
            )
        if real_distance_mm <= 0:
            raise DomainRuleError(
                f"real_distance_mm muss positiv sein, erhalten: {real_distance_mm}"
            )
        factor = real_distance_mm / pdf_distance
        return ScaleCalibration(
            method=ScaleMethod.TWO_POINT,
            factor=factor,
            description=(
                f"Zwei-Punkt-Kalibrierung: {real_distance_mm:.1f}mm / {pdf_distance:.4f}pdf-units"
                f" = {factor:.6f}mm/unit"
            ),
        )


class DirectScaleInputUseCase:
    """Create a ScaleCalibration from a user-supplied scale ratio (e.g. 1:100).

    PDF coordinates use 1/72 inch ≈ 0.3528mm per point.
    For a 1:100 plan: 1mm on paper = 100mm in reality.
    1 PDF point = 0.3528mm on paper = 35.28mm in reality.
    factor = 25.4 / 72 * scale_denominator   (convert points → mm)
    """

    _MM_PER_PDF_POINT: float = 25.4 / 72  # ≈ 0.352 777 mm

    def execute(
        self,
        scale_denominator: int,
    ) -> ScaleCalibration:
        """Return a ScaleCalibration for a standard architectural scale.

        Args:
            scale_denominator: the n in "1:n" (e.g. 100 for 1:100).

        Raises:
            DomainRuleError: if scale_denominator is not positive.
        """
        if scale_denominator <= 0:
            raise DomainRuleError(
                f"scale_denominator muss positiv sein, erhalten: {scale_denominator}"
            )
        factor = self._MM_PER_PDF_POINT * scale_denominator
        return ScaleCalibration(
            method=ScaleMethod.DIRECT,
            factor=factor,
            description=f"Direkte Massstab-Eingabe 1:{scale_denominator} → {factor:.6f}mm/point",
        )


def apply_calibration_to_plan(plan: FacadePlan, page_number: int, calibration: ScaleCalibration) -> None:
    """Apply a ScaleCalibration to a specific page of a FacadePlan in-place.

    Raises:
        DomainRuleError: if the page does not exist or is already calibrated.
    """
    page = next((p for p in plan.pages if p.page_number == page_number), None)
    if page is None:
        raise DomainRuleError(
            f"Seite {page_number} existiert nicht in Plan '{plan.id}'."
        )
    if page.is_calibrated:
        raise DomainRuleError(
            f"Seite {page_number} ist bereits kalibriert (Methode: {page.calibration.method.value if page.calibration else '?'})."
            " Verwende '--force' um die Kalibrierung zu überschreiben."
        )
    page.apply_scale(calibration)

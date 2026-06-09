"""DetectSurfacesUseCase — orchestrates surface detection for one plan page."""
from __future__ import annotations

from facade_planner.domain.entities.facade_plan import FacadePlan
from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.exceptions import DomainRuleError, EntityNotFoundError
from facade_planner.domain.services.surface_detection_service import (
    SurfaceDetectionConfig,
    SurfaceDetectionService,
)


class DetectSurfacesUseCase:
    """Detect FacadeSurface candidates from a calibrated PlanPage.

    Does not persist — the caller (CLI) is responsible for saving to the
    FacadeSurfaceRepository.
    """

    def execute(
        self,
        plan: FacadePlan,
        page_number: int,
        config: SurfaceDetectionConfig | None = None,
    ) -> list[FacadeSurface]:
        """Run detection and return the list of detected surfaces.

        Args:
            plan: The FacadePlan whose page we will analyse.
            page_number: 1-based page index (same convention as PlanPage.page_number).
            config: Optional detection config; defaults to SurfaceDetectionConfig().

        Raises:
            EntityNotFoundError: if the page_number is not found in the plan.
            DomainRuleError: if the page has not been calibrated yet.
        """
        page = next((p for p in plan.pages if p.page_number == page_number), None)
        if page is None:
            raise EntityNotFoundError(
                "PlanPage",
                f"{plan.id}/page/{page_number}",
            )
        if not page.is_calibrated:
            raise DomainRuleError(
                f"Seite {page_number} muss vor der Erkennung kalibriert sein "
                "('facade plan scale ...')."
            )

        service = SurfaceDetectionService(config)
        return service.detect(plan.id, page_number, page.geometries)

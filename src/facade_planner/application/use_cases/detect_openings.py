"""DetectOpeningsUseCase — classify candidate boundaries as openings of a surface."""
from __future__ import annotations

from pathlib import Path

from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.opening import Opening
from facade_planner.domain.exceptions import EntityNotFoundError
from facade_planner.domain.services.opening_detection_service import (
    OpeningDetectionResult,
    OpeningDetectionService,
)
from facade_planner.infrastructure.persistence.facade_surface_repository import (
    FileFacadeSurfaceRepository,
)

Coordinate = tuple[float, float]


class DetectOpeningsUseCase:
    """Detect openings in a surface and persist them.

    Candidates may come from:
    - Raw plan page geometries (pass via candidate_boundaries)
    - Manual boundaries provided directly via CLI/API

    The detected openings are appended to the surface and saved.
    Returns (openings_added, warnings).
    """

    def __init__(self, data_dir: Path) -> None:
        self._surface_repo = FileFacadeSurfaceRepository(data_dir / "surfaces")
        self._svc = OpeningDetectionService()

    def execute(
        self,
        surface_id: str,
        candidate_boundaries: list[list[Coordinate]],
        tolerance_mm: float = 1.0,
        replace_existing: bool = False,
    ) -> OpeningDetectionResult:
        """Run detection and save the updated surface.

        Args:
            surface_id: ID of the target FacadeSurface.
            candidate_boundaries: Polygon boundary lists to evaluate.
            tolerance_mm: Inward tolerance for containment check.
            replace_existing: If True, clears existing openings first.

        Raises:
            EntityNotFoundError: if the surface does not exist.
        """
        surface = self._surface_repo.load(surface_id)

        if replace_existing:
            surface.openings.clear()

        result = self._svc.detect(surface, candidate_boundaries, tolerance_mm)

        surface.openings.extend(result.openings)
        self._surface_repo.save(surface)

        return result


def openings_from_plan_page(
    surface: FacadeSurface,
    data_dir: Path,
    max_opening_area_mm2: float | None = None,
) -> list[list[Coordinate]]:
    """Extract candidate boundaries from the plan page that contains the surface.

    Filters raw geometries to only those smaller than the surface (potential
    openings) and optionally below a size threshold.
    """
    from facade_planner.infrastructure.persistence.facade_plan_repository import (
        FileFacadePlanRepository,
    )

    plan_repo = FileFacadePlanRepository(data_dir / "plans")
    try:
        plan = plan_repo.load(surface.plan_id)
    except EntityNotFoundError:
        return []

    page = next(
        (p for p in plan.pages if p.page_number == surface.page_number), None
    )
    if page is None:
        return []

    surface_area = surface.gross_area_mm2
    candidates: list[list[Coordinate]] = []

    for geom in page.geometries:
        if not geom.is_closed:
            continue
        coords = list(geom.coordinates)
        if len(coords) < 3:
            continue
        # Rough area filter: only consider geometries smaller than the surface
        from shapely.geometry import Polygon

        try:
            poly = Polygon(coords)
            area = abs(poly.area)
        except Exception:
            continue
        if area <= 0 or area >= surface_area:
            continue
        if max_opening_area_mm2 is not None and area > max_opening_area_mm2:
            continue
        candidates.append(coords)

    return candidates

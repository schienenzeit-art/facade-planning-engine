from pydantic import BaseModel, Field, computed_field

from facade_planner.domain.enums import SurfaceStatus
from facade_planner.domain.entities.opening import Opening

Coordinate = tuple[float, float]


class FacadeSurface(BaseModel):
    id: str
    plan_id: str
    page_number: int
    boundary: list[Coordinate]
    status: SurfaceStatus = SurfaceStatus.DETECTED
    zone_id: str | None = None
    openings: list[Opening] = Field(default_factory=list)
    reject_reason: str | None = None

    def confirm(self, zone_id: str | None = None) -> None:
        self.status = SurfaceStatus.CONFIRMED
        if zone_id:
            self.zone_id = zone_id

    def reject(self, reason: str = "") -> None:
        self.status = SurfaceStatus.REJECTED
        self.reject_reason = reason

    @computed_field  # type: ignore[misc]
    @property
    def gross_area_mm2(self) -> float:
        pts = self.boundary
        n = len(pts)
        if n < 3:
            return 0.0
        area = sum(
            pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
            for i in range(n)
        )
        return abs(area) / 2

    @computed_field  # type: ignore[misc]
    @property
    def net_area_mm2(self) -> float:
        return self.gross_area_mm2 - sum(o.area_mm2 for o in self.openings)

    @property
    def bounding_box(self) -> tuple[float, float, float, float]:
        """Returns (min_x, min_y, max_x, max_y)."""
        xs = [p[0] for p in self.boundary]
        ys = [p[1] for p in self.boundary]
        return min(xs), min(ys), max(xs), max(ys)

    @property
    def width_mm(self) -> float:
        bb = self.bounding_box
        return bb[2] - bb[0]

    @property
    def height_mm(self) -> float:
        bb = self.bounding_box
        return bb[3] - bb[1]

from pydantic import BaseModel, computed_field

from facade_planner.domain.enums import OpeningType

Coordinate = tuple[float, float]


class Opening(BaseModel):
    id: str
    surface_id: str
    opening_type: OpeningType = OpeningType.OTHER
    boundary: list[Coordinate]

    @computed_field  # type: ignore[misc]
    @property
    def area_mm2(self) -> float:
        """Shoelace formula for polygon area."""
        pts = self.boundary
        n = len(pts)
        if n < 3:
            return 0.0
        area = sum(
            pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
            for i in range(n)
        )
        return abs(area) / 2

from pydantic import BaseModel, Field

from facade_planner.domain.enums import CutReason, SelectionReason


class Panel(BaseModel):
    id: str
    surface_id: str
    format_code: str
    x_mm: float
    y_mm: float
    actual_width_mm: float = Field(gt=0)
    actual_height_mm: float = Field(gt=0)
    is_cut: bool = False
    cut_reason: CutReason | None = None
    selection_reason: SelectionReason = SelectionReason.FULL_PANEL_FIT
    row: int = 0
    col: int = 0

    @property
    def area_mm2(self) -> float:
        return self.actual_width_mm * self.actual_height_mm

    @property
    def corners(self) -> list[tuple[float, float]]:
        """Clockwise from bottom-left."""
        x, y, w, h = self.x_mm, self.y_mm, self.actual_width_mm, self.actual_height_mm
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

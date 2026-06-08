from pydantic import BaseModel, Field


class PanelFormat(BaseModel):
    format_code: str
    width_mm: float = Field(gt=0)
    height_mm: float = Field(gt=0)
    thickness_mm: float | None = None
    weight_kg_m2: float | None = None
    description: str = ""
    is_active: bool = True

    @property
    def area_mm2(self) -> float:
        return self.width_mm * self.height_mm

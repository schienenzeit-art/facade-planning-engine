from datetime import datetime

from pydantic import BaseModel, Field

from facade_planner.domain.enums import PDFSource
from facade_planner.domain.value_objects.raw_geometry import RawGeometry
from facade_planner.domain.value_objects.scale_calibration import ScaleCalibration


class PlanPage(BaseModel):
    page_number: int
    width_pdf: float
    height_pdf: float
    geometries: list[RawGeometry] = Field(default_factory=list)
    calibration: ScaleCalibration | None = None
    is_calibrated: bool = False

    def apply_scale(self, calibration: ScaleCalibration) -> None:
        """Transform all geometry coordinates to mm in-place."""
        if self.is_calibrated:
            return
        factor = calibration.factor
        scaled: list[RawGeometry] = []
        for geom in self.geometries:
            scaled.append(
                geom.model_copy(
                    update={
                        "coordinates": tuple(
                            (x * factor, y * factor) for x, y in geom.coordinates
                        )
                    }
                )
            )
        self.geometries = scaled
        self.calibration = calibration
        self.is_calibrated = True

    @property
    def available_layers(self) -> list[str]:
        return sorted({g.layer for g in self.geometries if g.layer})


class FacadePlan(BaseModel):
    id: str
    name: str
    source_path: str
    pdf_source: PDFSource = PDFSource.GENERIC
    pages: list[PlanPage] = Field(default_factory=list)
    imported_at: datetime = Field(default_factory=datetime.now)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def total_geometry_count(self) -> int:
        return sum(len(p.geometries) for p in self.pages)

from pydantic import BaseModel, Field

from facade_planner.domain.enums import ScaleMethod


class ScaleCalibration(BaseModel):
    """Result of a scale calibration operation."""

    model_config = {"frozen": True}

    method: ScaleMethod
    factor: float = Field(gt=0, description="mm per PDF unit")
    description: str = ""

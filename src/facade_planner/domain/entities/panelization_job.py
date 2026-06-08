from datetime import datetime

from pydantic import BaseModel, Field

from facade_planner.domain.enums import (
    OpeningStrategy,
    PanelOrientation,
    PanelizationStatus,
)
from facade_planner.domain.value_objects.joint_config import JointConfig


class PanelizationConfig(BaseModel):
    joint_config: JointConfig = Field(default_factory=JointConfig)
    min_panel_width_mm: float = Field(default=100.0, gt=0)
    min_panel_height_mm: float = Field(default=100.0, gt=0)
    opening_strategy: OpeningStrategy = OpeningStrategy.TRIM
    orientation: PanelOrientation = PanelOrientation.HORIZONTAL
    prefer_full_panels: bool = True
    audit_format_selection_log: bool = True


class SurfacePanelizationError(BaseModel):
    surface_id: str
    error_type: str
    message: str


class PanelizationJob(BaseModel):
    id: str
    surface_ids: list[str]
    catalog_ids: list[str]
    config: PanelizationConfig = Field(default_factory=PanelizationConfig)
    status: PanelizationStatus = PanelizationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    zone_id: str | None = None

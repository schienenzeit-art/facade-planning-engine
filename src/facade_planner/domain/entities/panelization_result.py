from pydantic import BaseModel, Field, computed_field

from facade_planner.domain.entities.panel import Panel
from facade_planner.domain.entities.panelization_job import SurfacePanelizationError


class RuleViolationRecord(BaseModel):
    rule_id: str
    severity: str
    surface_id: str | None = None
    panel_id: str | None = None
    message: str
    suggestion: str = ""


class PanelizationResult(BaseModel):
    job_id: str
    panels: list[Panel] = Field(default_factory=list)
    rule_violations: list[RuleViolationRecord] = Field(default_factory=list)
    surface_errors: list[SurfacePanelizationError] = Field(default_factory=list)
    failed_surface_ids: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[misc]
    @property
    def total_panels(self) -> int:
        return len(self.panels)

    @computed_field  # type: ignore[misc]
    @property
    def cut_panels(self) -> int:
        return sum(1 for p in self.panels if p.is_cut)

    @computed_field  # type: ignore[misc]
    @property
    def full_panels(self) -> int:
        return self.total_panels - self.cut_panels

    def panels_for_surface(self, surface_id: str) -> list[Panel]:
        return [p for p in self.panels if p.surface_id == surface_id]

    def errors_for_surface(self, surface_id: str) -> list[RuleViolationRecord]:
        return [v for v in self.rule_violations if v.surface_id == surface_id]

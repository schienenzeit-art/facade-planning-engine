from pydantic import BaseModel, Field, model_validator

from facade_planner.domain.enums import RuleSeverity


class RuleViolation(BaseModel):
    model_config = {"frozen": True}

    rule_id: str
    severity: RuleSeverity
    message: str
    suggestion: str
    surface_id: str | None = None
    panel_id: str | None = None

    @model_validator(mode="after")
    def suggestion_not_empty(self) -> "RuleViolation":
        if not self.suggestion:
            raise ValueError("suggestion must not be empty")
        return self

    @property
    def is_blocking(self) -> bool:
        return self.severity == RuleSeverity.ERROR

from typing import Any

from pydantic import BaseModel, Field

from facade_planner.domain.enums import RuleCategory, RuleSeverity


class RuleDefinition(BaseModel):
    model_config = {"frozen": True}

    id: str
    name: str
    description: str
    severity: RuleSeverity
    category: RuleCategory
    parameters: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_builtin: bool = False
    suggestion: str = ""

    def with_parameters(self, new_params: dict[str, Any]) -> "RuleDefinition":
        merged = {**self.parameters, **new_params}
        return self.model_copy(update={"parameters": merged})

    def deactivated(self) -> "RuleDefinition":
        return self.model_copy(update={"is_active": False})

    def activated(self) -> "RuleDefinition":
        return self.model_copy(update={"is_active": True})

from typing import Any

from pydantic import BaseModel, Field

from facade_planner.domain.enums import RuleCategory
from facade_planner.domain.exceptions import DomainRuleError, EntityNotFoundError
from facade_planner.domain.rules.rule_definition import RuleDefinition


class RuleCatalog(BaseModel):
    id: str
    project_id: str
    _rules: dict[str, RuleDefinition] = {}

    model_config = {"arbitrary_types_allowed": True}

    # Pydantic doesn't persist private attrs by default; use a public field.
    rules: dict[str, RuleDefinition] = Field(default_factory=dict)

    def add_rule(self, rule: RuleDefinition) -> None:
        self.rules[rule.id] = rule

    def get_rule(self, rule_id: str) -> RuleDefinition:
        if rule_id not in self.rules:
            raise EntityNotFoundError("Rule", rule_id)
        return self.rules[rule_id]

    def deactivate_rule(self, rule_id: str) -> None:
        rule = self.get_rule(rule_id)
        self.rules[rule_id] = rule.deactivated()

    def activate_rule(self, rule_id: str) -> None:
        rule = self.get_rule(rule_id)
        self.rules[rule_id] = rule.activated()

    def configure_rule(self, rule_id: str, parameters: dict[str, Any]) -> None:
        rule = self.get_rule(rule_id)
        self.rules[rule_id] = rule.with_parameters(parameters)

    def remove_rule(self, rule_id: str) -> None:
        rule = self.get_rule(rule_id)
        if rule.is_builtin:
            raise DomainRuleError(
                f"Builtin-Regel '{rule_id}' kann nicht gelöscht werden. "
                "Verwende 'deactivate_rule()' um sie zu deaktivieren."
            )
        del self.rules[rule_id]

    def get_active_rules(self, category: RuleCategory | None = None) -> list[RuleDefinition]:
        result = [r for r in self.rules.values() if r.is_active]
        if category:
            result = [r for r in result if r.category == category]
        return sorted(result, key=lambda r: r.id)

    def initialize_builtin_rules(self) -> None:
        from facade_planner.domain.rules.builtin_rules import BUILTIN_RULES
        for rule in BUILTIN_RULES:
            if rule.id not in self.rules:
                self.add_rule(rule)

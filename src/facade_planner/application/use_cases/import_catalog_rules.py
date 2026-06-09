"""ImportCatalogRulesUseCase — extract rules_raw from a SupplierCatalog
into the project's RuleCatalog as custom (non-builtin) RuleDefinitions.

Mapping logic
-------------
rules_raw entry with  parameters.min_joint_width_mm      → JOINT / WARNING
rules_raw entry with  parameters.expansion_joint_interval_mm → JOINT / WARNING
All other entries                                         → TECHNICAL / INFO

Rule IDs are namespaced as  <catalog_id>:<raw_rule_id>
to avoid collisions with builtin GR-xxx rules.

Idempotent: if a rule with the same namespaced ID already exists in the
catalog, it is NOT overwritten (already imported → skip).
"""
from __future__ import annotations

from facade_planner.domain.entities.supplier_catalog import SupplierCatalog
from facade_planner.domain.enums import RuleCategory, RuleSeverity
from facade_planner.domain.rules.rule_catalog import RuleCatalog
from facade_planner.domain.rules.rule_definition import RuleDefinition


class ImportCatalogRulesUseCase:
    """Convert a SupplierCatalog's rules_raw into RuleDefinition objects.

    Usage::

        uc = ImportCatalogRulesUseCase()
        added = uc.execute(catalog, rule_catalog)
        rule_catalog_repo.save(rule_catalog)
    """

    def execute(
        self,
        catalog: SupplierCatalog,
        rule_catalog: RuleCatalog,
    ) -> list[RuleDefinition]:
        """Add extracted rules to the RuleCatalog (skips existing IDs).

        Returns:
            List of RuleDefinition objects that were newly added.
        """
        added: list[RuleDefinition] = []
        for raw in catalog.rules_raw:
            rule = _raw_to_rule_definition(raw, catalog.id)
            if rule is None:
                continue
            if rule.id not in rule_catalog.rules:
                rule_catalog.add_rule(rule)
                added.append(rule)
        return added


def _raw_to_rule_definition(raw: dict, catalog_id: str) -> RuleDefinition | None:
    """Convert a single rules_raw entry to a RuleDefinition, or None if unparseable."""
    raw_id = raw.get("id", "")
    if not raw_id:
        return None

    namespaced_id = f"{catalog_id}:{raw_id}"
    description = raw.get("description", raw_id)
    parameters: dict = raw.get("parameters", {})

    category, severity = _infer_category_severity(parameters)

    suggestion = _build_suggestion(parameters, catalog_id)

    return RuleDefinition(
        id=namespaced_id,
        name=f"[{catalog_id}] {raw_id}",
        description=description,
        severity=severity,
        category=category,
        parameters=parameters,
        is_active=True,
        is_builtin=False,
        suggestion=suggestion,
    )


def _infer_category_severity(
    parameters: dict,
) -> tuple[RuleCategory, RuleSeverity]:
    if "min_joint_width_mm" in parameters or "expansion_joint_interval_mm" in parameters:
        return RuleCategory.JOINT, RuleSeverity.WARNING
    return RuleCategory.TECHNICAL, RuleSeverity.INFO


def _build_suggestion(parameters: dict, catalog_id: str) -> str:
    parts: list[str] = []
    if "min_joint_width_mm" in parameters:
        parts.append(
            f"Mindestfugenbreite gemäss {catalog_id}: "
            f"{parameters['min_joint_width_mm']} mm."
        )
    if "expansion_joint_interval_mm" in parameters:
        parts.append(
            f"Bewegungsfuge gemäss {catalog_id}: "
            f"alle {parameters['expansion_joint_interval_mm']} mm."
        )
    return " ".join(parts) if parts else f"Vorgabe des Lieferanten {catalog_id} prüfen."

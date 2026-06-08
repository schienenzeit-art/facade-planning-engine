"""RuleEngine domain service — evaluates active rules against panelization results."""
from facade_planner.domain.entities.panel import Panel
from facade_planner.domain.entities.panel_format import PanelFormat
from facade_planner.domain.entities.panelization_job import PanelizationConfig
from facade_planner.domain.entities.panelization_result import PanelizationResult
from facade_planner.domain.rules.rule_catalog import RuleCatalog
from facade_planner.domain.rules.rule_definition import RuleDefinition
from facade_planner.domain.rules.rule_violation import RuleViolation


class RuleEngine:
    """Evaluates active rules in a RuleCatalog against panelization data."""

    def __init__(self, catalog: RuleCatalog) -> None:
        self._catalog = catalog

    # ── PUBLIC API ──────────────────────────────────────────────────────────

    def evaluate_panel(
        self,
        panel: Panel,
        format_lookup: dict[str, PanelFormat],
    ) -> list[RuleViolation]:
        """Per-panel checks: GR-001, GR-002, GR-003, GR-007."""
        active = self._active_rule_map()
        violations: list[RuleViolation] = []

        violations.extend(self._check_gr001(panel, format_lookup, active))
        violations.extend(self._check_gr002(panel, format_lookup, active))
        violations.extend(self._check_gr003(panel, active))
        violations.extend(self._check_gr007(panel, active))

        return violations

    def evaluate_result(
        self,
        result: PanelizationResult,
        format_lookup: dict[str, PanelFormat],
        config: PanelizationConfig,
    ) -> list[RuleViolation]:
        """Full result evaluation: per-panel + result-level rules."""
        active = self._active_rule_map()
        violations: list[RuleViolation] = []

        for panel in result.panels:
            violations.extend(self.evaluate_panel(panel, format_lookup))

        violations.extend(self._check_gr004(result, active))
        violations.extend(self._check_gr005(result, active))
        violations.extend(self._check_gr008(config, active))
        violations.extend(self._check_gr009(config, active))
        violations.extend(self._check_gr010(result, active))

        return violations

    # ── HELPERS ─────────────────────────────────────────────────────────────

    def _active_rule_map(self) -> dict[str, RuleDefinition]:
        return {r.id: r for r in self._catalog.get_active_rules()}

    # ── PER-PANEL CHECKS ────────────────────────────────────────────────────

    @staticmethod
    def _check_gr001(
        panel: Panel,
        format_lookup: dict[str, PanelFormat],
        active: dict[str, RuleDefinition],
    ) -> list[RuleViolation]:
        rule = active.get("GR-001")
        if rule is None:
            return []
        if not panel.format_code or panel.format_code not in format_lookup:
            return [
                RuleViolation(
                    rule_id=rule.id,
                    severity=rule.severity,
                    message=(
                        f"Panel '{panel.id}' referenziert unbekanntes Format"
                        f" '{panel.format_code}'."
                    ),
                    suggestion=rule.suggestion,
                    surface_id=panel.surface_id,
                    panel_id=panel.id,
                )
            ]
        return []

    @staticmethod
    def _check_gr002(
        panel: Panel,
        format_lookup: dict[str, PanelFormat],
        active: dict[str, RuleDefinition],
    ) -> list[RuleViolation]:
        rule = active.get("GR-002")
        if rule is None:
            return []
        fmt = format_lookup.get(panel.format_code)
        if fmt is None:
            return []  # GR-001 already caught this
        if panel.actual_width_mm > fmt.width_mm or panel.actual_height_mm > fmt.height_mm:
            return [
                RuleViolation(
                    rule_id=rule.id,
                    severity=rule.severity,
                    message=(
                        f"Panel '{panel.id}' "
                        f"({panel.actual_width_mm:.0f}×{panel.actual_height_mm:.0f}mm) "
                        f"überschreitet Rohformat '{fmt.format_code}' "
                        f"({fmt.width_mm:.0f}×{fmt.height_mm:.0f}mm)."
                    ),
                    suggestion=rule.suggestion,
                    surface_id=panel.surface_id,
                    panel_id=panel.id,
                )
            ]
        return []

    @staticmethod
    def _check_gr003(
        panel: Panel,
        active: dict[str, RuleDefinition],
    ) -> list[RuleViolation]:
        rule = active.get("GR-003")
        if rule is None:
            return []
        if panel.actual_width_mm <= 0 or panel.actual_height_mm <= 0:
            return [
                RuleViolation(
                    rule_id=rule.id,
                    severity=rule.severity,
                    message=(
                        f"Panel '{panel.id}' hat ungültige Masse:"
                        f" {panel.actual_width_mm}×{panel.actual_height_mm}mm."
                    ),
                    suggestion=rule.suggestion,
                    surface_id=panel.surface_id,
                    panel_id=panel.id,
                )
            ]
        return []

    @staticmethod
    def _check_gr007(
        panel: Panel,
        active: dict[str, RuleDefinition],
    ) -> list[RuleViolation]:
        rule = active.get("GR-007")
        if rule is None or not panel.is_cut:
            return []
        min_size: float = rule.parameters.get("min_cut_panel_width_mm", 50.0)
        if panel.actual_width_mm < min_size or panel.actual_height_mm < min_size:
            return [
                RuleViolation(
                    rule_id=rule.id,
                    severity=rule.severity,
                    message=(
                        f"Geschnittenes Panel '{panel.id}' "
                        f"({panel.actual_width_mm:.0f}×{panel.actual_height_mm:.0f}mm) "
                        f"unterschreitet Mindestmass von {min_size:.0f}mm."
                    ),
                    suggestion=rule.suggestion,
                    surface_id=panel.surface_id,
                    panel_id=panel.id,
                )
            ]
        return []

    # ── RESULT-LEVEL CHECKS ─────────────────────────────────────────────────

    @staticmethod
    def _check_gr004(
        result: PanelizationResult,
        active: dict[str, RuleDefinition],
    ) -> list[RuleViolation]:
        rule = active.get("GR-004")
        if rule is None:
            return []
        seen: set[str] = set()
        violations: list[RuleViolation] = []
        for sid in result.failed_surface_ids:
            if sid in seen:
                violations.append(
                    RuleViolation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        message=f"Flächen-ID '{sid}' tritt mehrfach in failed_surface_ids auf.",
                        suggestion=rule.suggestion,
                        surface_id=sid,
                    )
                )
            seen.add(sid)
        return violations

    @staticmethod
    def _check_gr005(
        result: PanelizationResult,
        active: dict[str, RuleDefinition],
    ) -> list[RuleViolation]:
        rule = active.get("GR-005")
        if rule is None:
            return []
        seen: set[str] = set()
        violations: list[RuleViolation] = []
        for panel in result.panels:
            if panel.id in seen:
                violations.append(
                    RuleViolation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        message=f"Panel-ID '{panel.id}' tritt mehrfach im Ergebnis auf.",
                        suggestion=rule.suggestion,
                        surface_id=panel.surface_id,
                        panel_id=panel.id,
                    )
                )
            seen.add(panel.id)
        return violations

    @staticmethod
    def _check_gr008(
        config: PanelizationConfig,
        active: dict[str, RuleDefinition],
    ) -> list[RuleViolation]:
        rule = active.get("GR-008")
        if rule is None:
            return []
        expected: float = rule.parameters.get("expansion_joint_interval_mm", 6000.0)
        actual = config.joint_config.expansion_joint_interval_mm
        if actual > expected:
            return [
                RuleViolation(
                    rule_id=rule.id,
                    severity=rule.severity,
                    message=(
                        f"Bewegungsfugen-Intervall {actual:.0f}mm überschreitet "
                        f"Empfehlung {expected:.0f}mm (SIA 331 / Swisspearl)."
                    ),
                    suggestion=rule.suggestion,
                )
            ]
        return []

    @staticmethod
    def _check_gr009(
        config: PanelizationConfig,
        active: dict[str, RuleDefinition],
    ) -> list[RuleViolation]:
        rule = active.get("GR-009")
        if rule is None:
            return []
        min_width: float = rule.parameters.get("min_joint_width_mm", 8.0)
        jc = config.joint_config
        issues: list[str] = []
        if jc.horizontal_joint_mm < min_width:
            issues.append(f"horizontal_joint_mm={jc.horizontal_joint_mm}")
        if jc.vertical_joint_mm < min_width:
            issues.append(f"vertical_joint_mm={jc.vertical_joint_mm}")
        if not issues:
            return []
        return [
            RuleViolation(
                rule_id=rule.id,
                severity=rule.severity,
                message=(
                    f"Fugenbreite unterschreitet Mindestmass {min_width:.0f}mm"
                    f" (Swisspearl): {', '.join(issues)}."
                ),
                suggestion=rule.suggestion,
            )
        ]

    @staticmethod
    def _check_gr010(
        result: PanelizationResult,
        active: dict[str, RuleDefinition],
    ) -> list[RuleViolation]:
        rule = active.get("GR-010")
        if rule is None:
            return []
        panels_by_surface: dict[str, list[Panel]] = {}
        for panel in result.panels:
            panels_by_surface.setdefault(panel.surface_id, []).append(panel)

        violations: list[RuleViolation] = []
        for surface_id, panels in panels_by_surface.items():
            for i, p1 in enumerate(panels):
                for p2 in panels[i + 1 :]:
                    if _aabb_overlap(p1, p2):
                        violations.append(
                            RuleViolation(
                                rule_id=rule.id,
                                severity=rule.severity,
                                message=(
                                    f"Panels '{p1.id}' und '{p2.id}' überlappen sich"
                                    f" auf Fläche '{surface_id}'."
                                ),
                                suggestion=rule.suggestion,
                                surface_id=surface_id,
                            )
                        )
        return violations


def _aabb_overlap(p1: Panel, p2: Panel) -> bool:
    """True if two axis-aligned rectangular panels overlap (excluding shared edges)."""
    return (
        p1.x_mm < p2.x_mm + p2.actual_width_mm
        and p1.x_mm + p1.actual_width_mm > p2.x_mm
        and p1.y_mm < p2.y_mm + p2.actual_height_mm
        and p1.y_mm + p1.actual_height_mm > p2.y_mm
    )

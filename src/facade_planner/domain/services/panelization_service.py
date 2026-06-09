"""PanelizationService — orchestrates algorithm, rule evaluation, per-surface error handling."""
from __future__ import annotations

from datetime import datetime

from facade_planner.domain.algorithms.base_panelization_algorithm import (
    BasePanelizationAlgorithm,
)
from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.panel_format import PanelFormat
from facade_planner.domain.entities.panelization_job import (
    PanelizationJob,
    PanelizationStatus,
    SurfacePanelizationError,
)
from facade_planner.domain.entities.panelization_result import (
    PanelizationResult,
    RuleViolationRecord,
)
from facade_planner.domain.exceptions import PanelizationError
from facade_planner.domain.rules.rule_catalog import RuleCatalog
from facade_planner.domain.rules.rule_engine import RuleEngine


class PanelizationService:
    """Runs the panelization algorithm over all surfaces in a job.

    Per-surface errors (PE-001..PE-004) are recorded but do NOT abort the
    remaining surfaces (fail-per-surface semantics).

    Rule evaluation (GR-001..GR-010) runs after all panels are collected.
    """

    def __init__(
        self,
        algorithm: BasePanelizationAlgorithm,
        rule_catalog: RuleCatalog,
    ) -> None:
        self._algo = algorithm
        self._rule_catalog = rule_catalog

    def panelize(
        self,
        job: PanelizationJob,
        surfaces: list[FacadeSurface],
        formats: list[PanelFormat],
    ) -> PanelizationResult:
        result = PanelizationResult(job_id=job.id)
        format_lookup = {f.format_code: f for f in formats}

        for surface in surfaces:
            try:
                panels = self._algo.panelize(surface, formats, job.config)
                result.panels.extend(panels)
            except PanelizationError as exc:
                result.surface_errors.append(
                    SurfacePanelizationError(
                        surface_id=surface.id,
                        error_type=exc.error_type,
                        message=str(exc),
                    )
                )
                result.failed_surface_ids.append(surface.id)

        # Rule evaluation over the collected panels
        engine = RuleEngine(self._rule_catalog)
        violations = engine.evaluate_result(result, format_lookup, job.config)
        result.rule_violations = [
            RuleViolationRecord(
                rule_id=v.rule_id,
                severity=v.severity.value,
                surface_id=v.surface_id,
                panel_id=v.panel_id,
                message=v.message,
                suggestion=v.suggestion,
            )
            for v in violations
        ]

        return result

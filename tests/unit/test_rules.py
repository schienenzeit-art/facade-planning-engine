"""Unit tests for EPIC-009 — Rules Engine.

Covers: RuleDefinition, RuleViolation, RuleCatalog, RuleEngine, FileRuleCatalogRepository.
"""
import uuid
from pathlib import Path

import pytest

from facade_planner.domain.enums import CutReason, RuleCategory, RuleSeverity, SelectionReason
from facade_planner.domain.entities.panel import Panel
from facade_planner.domain.entities.panel_format import PanelFormat
from facade_planner.domain.entities.panelization_job import PanelizationConfig
from facade_planner.domain.entities.panelization_result import PanelizationResult
from facade_planner.domain.exceptions import DomainRuleError, EntityNotFoundError
from facade_planner.domain.rules.builtin_rules import BUILTIN_RULES, BUILTIN_RULE_IDS
from facade_planner.domain.rules.rule_catalog import RuleCatalog
from facade_planner.domain.rules.rule_definition import RuleDefinition
from facade_planner.domain.rules.rule_engine import RuleEngine, _aabb_overlap
from facade_planner.domain.rules.rule_violation import RuleViolation
from facade_planner.domain.value_objects.joint_config import JointConfig
from facade_planner.infrastructure.persistence.rule_catalog_repository import (
    FileRuleCatalogRepository,
)


# ── FIXTURES ─────────────────────────────────────────────────────────────────

@pytest.fixture
def custom_rule() -> RuleDefinition:
    return RuleDefinition(
        id="CUSTOM-001",
        name="Test-Regel",
        description="Eine benutzerdefinierte Regel.",
        severity=RuleSeverity.WARNING,
        category=RuleCategory.GEOMETRIC,
        suggestion="Prüfe die Konfiguration.",
    )


@pytest.fixture
def empty_catalog() -> RuleCatalog:
    return RuleCatalog(id=str(uuid.uuid4()), project_id="proj-001")


@pytest.fixture
def initialized_catalog() -> RuleCatalog:
    catalog = RuleCatalog(id=str(uuid.uuid4()), project_id="proj-001")
    catalog.initialize_builtin_rules()
    return catalog


@pytest.fixture
def format_lookup() -> dict[str, PanelFormat]:
    return {
        "SW-1250x3050": PanelFormat(
            format_code="SW-1250x3050",
            width_mm=1250.0,
            height_mm=3050.0,
        )
    }


@pytest.fixture
def full_panel() -> Panel:
    return Panel(
        id="panel-001",
        surface_id="surf-001",
        format_code="SW-1250x3050",
        x_mm=0.0,
        y_mm=0.0,
        actual_width_mm=1250.0,
        actual_height_mm=3050.0,
    )


@pytest.fixture
def standard_config() -> PanelizationConfig:
    return PanelizationConfig(
        joint_config=JointConfig(
            horizontal_joint_mm=10.0,
            vertical_joint_mm=10.0,
            expansion_joint_interval_mm=6000.0,
        )
    )


# ── RULE DEFINITION ───────────────────────────────────────────────────────────

class TestRuleDefinition:
    def test_frozen(self, custom_rule: RuleDefinition) -> None:
        with pytest.raises(Exception):
            custom_rule.is_active = False  # type: ignore[misc]

    def test_with_parameters_merges(self, custom_rule: RuleDefinition) -> None:
        updated = custom_rule.with_parameters({"threshold_mm": 100})
        assert updated.parameters["threshold_mm"] == 100
        assert updated.id == custom_rule.id

    def test_deactivated_returns_copy(self, custom_rule: RuleDefinition) -> None:
        deactivated = custom_rule.deactivated()
        assert not deactivated.is_active
        assert custom_rule.is_active  # original unchanged

    def test_activated_returns_copy(self) -> None:
        rule = RuleDefinition(
            id="X-001",
            name="X",
            description="X",
            severity=RuleSeverity.INFO,
            category=RuleCategory.GEOMETRIC,
            is_active=False,
            suggestion="Fix it.",
        )
        assert rule.activated().is_active


# ── RULE VIOLATION ────────────────────────────────────────────────────────────

class TestRuleViolation:
    def test_frozen(self) -> None:
        v = RuleViolation(
            rule_id="GR-001",
            severity=RuleSeverity.ERROR,
            message="msg",
            suggestion="fix",
        )
        with pytest.raises(Exception):
            v.message = "other"  # type: ignore[misc]

    def test_is_blocking_error(self) -> None:
        v = RuleViolation(
            rule_id="GR-001",
            severity=RuleSeverity.ERROR,
            message="msg",
            suggestion="fix",
        )
        assert v.is_blocking

    def test_is_not_blocking_warning(self) -> None:
        v = RuleViolation(
            rule_id="GR-009",
            severity=RuleSeverity.WARNING,
            message="msg",
            suggestion="fix",
        )
        assert not v.is_blocking

    def test_empty_suggestion_raises(self) -> None:
        with pytest.raises(ValueError, match="suggestion"):
            RuleViolation(
                rule_id="GR-001",
                severity=RuleSeverity.ERROR,
                message="msg",
                suggestion="",
            )


# ── RULE CATALOG ──────────────────────────────────────────────────────────────

class TestRuleCatalog:
    def test_add_and_get_rule(self, empty_catalog: RuleCatalog, custom_rule: RuleDefinition) -> None:
        empty_catalog.add_rule(custom_rule)
        retrieved = empty_catalog.get_rule(custom_rule.id)
        assert retrieved.id == custom_rule.id

    def test_get_missing_rule_raises(self, empty_catalog: RuleCatalog) -> None:
        with pytest.raises(EntityNotFoundError):
            empty_catalog.get_rule("NONEXISTENT")

    def test_deactivate_rule(self, initialized_catalog: RuleCatalog) -> None:
        initialized_catalog.deactivate_rule("GR-001")
        assert not initialized_catalog.get_rule("GR-001").is_active

    def test_activate_rule(self, initialized_catalog: RuleCatalog) -> None:
        initialized_catalog.deactivate_rule("GR-001")
        initialized_catalog.activate_rule("GR-001")
        assert initialized_catalog.get_rule("GR-001").is_active

    def test_configure_rule_merges_params(self, initialized_catalog: RuleCatalog) -> None:
        initialized_catalog.configure_rule("GR-008", {"expansion_joint_interval_mm": 4000})
        rule = initialized_catalog.get_rule("GR-008")
        assert rule.parameters["expansion_joint_interval_mm"] == 4000

    def test_remove_custom_rule(self, empty_catalog: RuleCatalog, custom_rule: RuleDefinition) -> None:
        empty_catalog.add_rule(custom_rule)
        empty_catalog.remove_rule(custom_rule.id)
        with pytest.raises(EntityNotFoundError):
            empty_catalog.get_rule(custom_rule.id)

    def test_remove_builtin_rule_raises(self, initialized_catalog: RuleCatalog) -> None:
        with pytest.raises(DomainRuleError):
            initialized_catalog.remove_rule("GR-001")

    def test_get_active_rules_filters(self, initialized_catalog: RuleCatalog) -> None:
        initialized_catalog.deactivate_rule("GR-001")
        active = initialized_catalog.get_active_rules()
        assert all(r.is_active for r in active)
        assert not any(r.id == "GR-001" for r in active)

    def test_get_active_rules_by_category(self, initialized_catalog: RuleCatalog) -> None:
        joint_rules = initialized_catalog.get_active_rules(category=RuleCategory.JOINT)
        assert all(r.category == RuleCategory.JOINT for r in joint_rules)

    def test_initialize_builtin_rules_idempotent(self, initialized_catalog: RuleCatalog) -> None:
        count_before = len(initialized_catalog.rules)
        initialized_catalog.initialize_builtin_rules()
        assert len(initialized_catalog.rules) == count_before


# ── BUILTIN RULES ─────────────────────────────────────────────────────────────

class TestBuiltinRules:
    def test_all_ten_builtin_rules_present(self) -> None:
        assert len(BUILTIN_RULES) == 10

    def test_all_ids_unique(self) -> None:
        ids = [r.id for r in BUILTIN_RULES]
        assert len(ids) == len(set(ids))

    def test_all_builtin_flagged(self) -> None:
        assert all(r.is_builtin for r in BUILTIN_RULES)

    def test_all_have_suggestion(self) -> None:
        assert all(r.suggestion for r in BUILTIN_RULES)

    def test_builtin_rule_ids_set(self) -> None:
        assert BUILTIN_RULE_IDS == {r.id for r in BUILTIN_RULES}

    def test_gr_prefix_convention(self) -> None:
        assert all(r.id.startswith("GR-") for r in BUILTIN_RULES)


# ── RULE ENGINE ───────────────────────────────────────────────────────────────

class TestRuleEngine:
    def test_no_violations_for_valid_panel(
        self,
        initialized_catalog: RuleCatalog,
        full_panel: Panel,
        format_lookup: dict[str, PanelFormat],
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        violations = engine.evaluate_panel(full_panel, format_lookup)
        assert violations == []

    def test_gr001_missing_format(
        self,
        initialized_catalog: RuleCatalog,
        full_panel: Panel,
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        bad_panel = full_panel.model_copy(update={"format_code": "UNKNOWN-FORMAT"})
        violations = engine.evaluate_panel(bad_panel, {})
        gr001 = [v for v in violations if v.rule_id == "GR-001"]
        assert len(gr001) == 1
        assert gr001[0].is_blocking

    def test_gr002_panel_exceeds_format(
        self,
        initialized_catalog: RuleCatalog,
        format_lookup: dict[str, PanelFormat],
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        oversized = Panel(
            id="p-big",
            surface_id="surf-001",
            format_code="SW-1250x3050",
            x_mm=0.0,
            y_mm=0.0,
            actual_width_mm=2000.0,  # exceeds 1250mm
            actual_height_mm=3050.0,
        )
        violations = engine.evaluate_panel(oversized, format_lookup)
        gr002 = [v for v in violations if v.rule_id == "GR-002"]
        assert len(gr002) == 1

    def test_gr007_cut_panel_too_small(
        self,
        initialized_catalog: RuleCatalog,
        format_lookup: dict[str, PanelFormat],
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        tiny_cut = Panel(
            id="p-tiny",
            surface_id="surf-001",
            format_code="SW-1250x3050",
            x_mm=0.0,
            y_mm=0.0,
            actual_width_mm=30.0,  # below default 50mm threshold
            actual_height_mm=100.0,
            is_cut=True,
            cut_reason=CutReason.OPENING,
        )
        violations = engine.evaluate_panel(tiny_cut, format_lookup)
        gr007 = [v for v in violations if v.rule_id == "GR-007"]
        assert len(gr007) == 1

    def test_gr007_not_triggered_for_full_panel(
        self,
        initialized_catalog: RuleCatalog,
        format_lookup: dict[str, PanelFormat],
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        small_full = Panel(
            id="p-small",
            surface_id="surf-001",
            format_code="SW-1250x3050",
            x_mm=0.0,
            y_mm=0.0,
            actual_width_mm=30.0,
            actual_height_mm=100.0,
            is_cut=False,
        )
        violations = engine.evaluate_panel(small_full, format_lookup)
        assert not any(v.rule_id == "GR-007" for v in violations)

    def test_gr005_duplicate_panel_ids(
        self,
        initialized_catalog: RuleCatalog,
        format_lookup: dict[str, PanelFormat],
        full_panel: Panel,
        standard_config: PanelizationConfig,
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        result = PanelizationResult(
            job_id="job-001",
            panels=[full_panel, full_panel.model_copy()],
        )
        violations = engine.evaluate_result(result, format_lookup, standard_config)
        gr005 = [v for v in violations if v.rule_id == "GR-005"]
        assert len(gr005) == 1

    def test_gr008_expansion_interval_exceeded(
        self,
        initialized_catalog: RuleCatalog,
        format_lookup: dict[str, PanelFormat],
        full_panel: Panel,
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        config = PanelizationConfig(
            joint_config=JointConfig(expansion_joint_interval_mm=8000.0)
        )
        result = PanelizationResult(job_id="job-001", panels=[full_panel])
        violations = engine.evaluate_result(result, format_lookup, config)
        gr008 = [v for v in violations if v.rule_id == "GR-008"]
        assert len(gr008) == 1

    def test_gr008_within_limit_no_violation(
        self,
        initialized_catalog: RuleCatalog,
        format_lookup: dict[str, PanelFormat],
        full_panel: Panel,
        standard_config: PanelizationConfig,
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        result = PanelizationResult(job_id="job-001", panels=[full_panel])
        violations = engine.evaluate_result(result, format_lookup, standard_config)
        assert not any(v.rule_id == "GR-008" for v in violations)

    def test_gr009_joint_too_narrow(
        self,
        initialized_catalog: RuleCatalog,
        format_lookup: dict[str, PanelFormat],
        full_panel: Panel,
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        config = PanelizationConfig(
            joint_config=JointConfig(horizontal_joint_mm=5.0, vertical_joint_mm=5.0)
        )
        result = PanelizationResult(job_id="job-001", panels=[full_panel])
        violations = engine.evaluate_result(result, format_lookup, config)
        gr009 = [v for v in violations if v.rule_id == "GR-009"]
        assert len(gr009) == 1

    def test_gr010_overlapping_panels(
        self,
        initialized_catalog: RuleCatalog,
        format_lookup: dict[str, PanelFormat],
        standard_config: PanelizationConfig,
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        p1 = Panel(
            id="p-001", surface_id="surf-001", format_code="SW-1250x3050",
            x_mm=0.0, y_mm=0.0, actual_width_mm=1250.0, actual_height_mm=500.0,
        )
        p2 = Panel(
            id="p-002", surface_id="surf-001", format_code="SW-1250x3050",
            x_mm=600.0, y_mm=0.0, actual_width_mm=1250.0, actual_height_mm=500.0,
        )
        result = PanelizationResult(job_id="job-001", panels=[p1, p2])
        violations = engine.evaluate_result(result, format_lookup, standard_config)
        gr010 = [v for v in violations if v.rule_id == "GR-010"]
        assert len(gr010) == 1

    def test_gr010_adjacent_panels_no_violation(
        self,
        initialized_catalog: RuleCatalog,
        format_lookup: dict[str, PanelFormat],
        standard_config: PanelizationConfig,
    ) -> None:
        engine = RuleEngine(initialized_catalog)
        p1 = Panel(
            id="p-001", surface_id="surf-001", format_code="SW-1250x3050",
            x_mm=0.0, y_mm=0.0, actual_width_mm=1250.0, actual_height_mm=500.0,
        )
        p2 = Panel(
            id="p-002", surface_id="surf-001", format_code="SW-1250x3050",
            x_mm=1250.0, y_mm=0.0, actual_width_mm=1250.0, actual_height_mm=500.0,
        )
        result = PanelizationResult(job_id="job-001", panels=[p1, p2])
        violations = engine.evaluate_result(result, format_lookup, standard_config)
        assert not any(v.rule_id == "GR-010" for v in violations)

    def test_disabled_rule_not_evaluated(
        self,
        initialized_catalog: RuleCatalog,
        format_lookup: dict[str, PanelFormat],
    ) -> None:
        initialized_catalog.deactivate_rule("GR-001")
        engine = RuleEngine(initialized_catalog)
        bad_panel = Panel(
            id="p-bad", surface_id="surf-001", format_code="NONEXISTENT",
            x_mm=0.0, y_mm=0.0, actual_width_mm=100.0, actual_height_mm=100.0,
        )
        violations = engine.evaluate_panel(bad_panel, {})
        assert not any(v.rule_id == "GR-001" for v in violations)


# ── AABB HELPER ───────────────────────────────────────────────────────────────

class TestAABBOverlap:
    def _panel(self, x: float, y: float, w: float, h: float) -> Panel:
        return Panel(
            id=str(uuid.uuid4()),
            surface_id="surf",
            format_code="FMT",
            x_mm=x,
            y_mm=y,
            actual_width_mm=w,
            actual_height_mm=h,
        )

    def test_overlapping(self) -> None:
        assert _aabb_overlap(self._panel(0, 0, 100, 100), self._panel(50, 50, 100, 100))

    def test_adjacent_no_overlap(self) -> None:
        assert not _aabb_overlap(self._panel(0, 0, 100, 100), self._panel(100, 0, 100, 100))

    def test_separated_no_overlap(self) -> None:
        assert not _aabb_overlap(self._panel(0, 0, 100, 100), self._panel(200, 0, 100, 100))

    def test_contained_overlaps(self) -> None:
        assert _aabb_overlap(self._panel(0, 0, 1000, 1000), self._panel(100, 100, 100, 100))


# ── FILE RULE CATALOG REPOSITORY ──────────────────────────────────────────────

class TestFileRuleCatalogRepository:
    def test_load_or_create_initializes_builtin_rules(self, tmp_path: Path) -> None:
        (tmp_path / ".facadeplanner").mkdir()
        repo = FileRuleCatalogRepository(tmp_path / ".facadeplanner")
        catalog = repo.load_or_create("proj-001")
        assert len(catalog.rules) == 10

    def test_load_or_create_idempotent(self, tmp_path: Path) -> None:
        (tmp_path / ".facadeplanner").mkdir()
        repo = FileRuleCatalogRepository(tmp_path / ".facadeplanner")
        catalog1 = repo.load_or_create("proj-001")
        catalog2 = repo.load_or_create("proj-001")
        assert catalog1.id == catalog2.id

    def test_save_and_load(self, tmp_path: Path) -> None:
        (tmp_path / ".facadeplanner").mkdir()
        repo = FileRuleCatalogRepository(tmp_path / ".facadeplanner")
        catalog = repo.load_or_create("proj-001")
        catalog.deactivate_rule("GR-009")
        repo.save(catalog)
        loaded = repo.load()
        assert not loaded.get_rule("GR-009").is_active

    def test_load_missing_raises(self, tmp_path: Path) -> None:
        (tmp_path / ".facadeplanner").mkdir()
        repo = FileRuleCatalogRepository(tmp_path / ".facadeplanner")
        with pytest.raises(EntityNotFoundError):
            repo.load()

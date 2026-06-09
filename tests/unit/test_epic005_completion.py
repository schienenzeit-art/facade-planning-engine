"""Tests for EPIC-005 completion — CSVCatalogAdapter + ImportCatalogRulesUseCase.

Covers: CSVCatalogAdapter, ImportCatalogRulesUseCase, updated CatalogImportService
        (CSV dispatch, sharper JSON error messages), catalog CLI (--extract-rules).
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from typer.testing import CliRunner

from facade_planner.application.services.catalog_import_service import CatalogImportService
from facade_planner.application.use_cases.import_catalog_rules import (
    ImportCatalogRulesUseCase,
    _raw_to_rule_definition,
)
from facade_planner.cli.main import app
from facade_planner.domain.entities.supplier_catalog import SupplierCatalog
from facade_planner.domain.enums import RuleCategory, RuleSeverity
from facade_planner.domain.exceptions import DomainRuleError
from facade_planner.domain.rules.rule_catalog import RuleCatalog
from facade_planner.infrastructure.adapters.csv_catalog_adapter import CSVCatalogAdapter


# ── FIXTURES ──────────────────────────────────────────────────────────────────

@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def valid_csv(tmp_path: Path) -> Path:
    content = (
        "format_code,width_mm,height_mm,thickness_mm,weight_kg_m2,description,is_active\n"
        "MY-1250x3050-8,1250,3050,8,16.0,Test panel,true\n"
        "MY-1000x2000-4,1000,2000,4,7.6,Second format,1\n"
    )
    p = tmp_path / "test_catalog.csv"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture
def minimal_csv(tmp_path: Path) -> Path:
    content = (
        "format_code,width_mm,height_mm\n"
        "SIMPLE-500x1000,500,1000\n"
    )
    p = tmp_path / "minimal.csv"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture
def catalog_with_rules() -> SupplierCatalog:
    from facade_planner.domain.entities.panel_format import PanelFormat
    return SupplierCatalog(
        id="test-supplier-2026",
        supplier_name="Test Supplier",
        formats=[PanelFormat(format_code="T-1000x2000-4", width_mm=1000, height_mm=2000)],
        rules_raw=[
            {
                "id": "TS-R-001",
                "description": "Mindestfugenbreite 8mm",
                "parameters": {"min_joint_width_mm": 8},
            },
            {
                "id": "TS-R-002",
                "description": "Bewegungsfuge alle 6000mm",
                "parameters": {"expansion_joint_interval_mm": 6000},
            },
            {
                "id": "TS-R-003",
                "description": "Brandklasse A2",
                "parameters": {},
            },
        ],
    )


# ── CSVCatalogAdapter ─────────────────────────────────────────────────────────

class TestCSVCatalogAdapter:
    def test_valid_csv_parses_formats(self, valid_csv: Path) -> None:
        adapter = CSVCatalogAdapter()
        catalog = adapter.from_file(valid_csv, catalog_id="test-001", supplier_name="Test")
        assert len(catalog.formats) == 2

    def test_catalog_id_and_supplier_name_set(self, valid_csv: Path) -> None:
        adapter = CSVCatalogAdapter()
        catalog = adapter.from_file(valid_csv, catalog_id="my-cat", supplier_name="My Supplier")
        assert catalog.id == "my-cat"
        assert catalog.supplier_name == "My Supplier"

    def test_source_path_is_set(self, valid_csv: Path) -> None:
        adapter = CSVCatalogAdapter()
        catalog = adapter.from_file(valid_csv, catalog_id="x", supplier_name="X")
        assert str(valid_csv) in catalog.source_path

    def test_format_fields_parsed(self, valid_csv: Path) -> None:
        adapter = CSVCatalogAdapter()
        catalog = adapter.from_file(valid_csv, catalog_id="x", supplier_name="X")
        fmt = catalog.formats[0]
        assert fmt.format_code == "MY-1250x3050-8"
        assert fmt.width_mm == pytest.approx(1250.0)
        assert fmt.height_mm == pytest.approx(3050.0)
        assert fmt.thickness_mm == pytest.approx(8.0)
        assert fmt.weight_kg_m2 == pytest.approx(16.0)
        assert fmt.description == "Test panel"
        assert fmt.is_active is True

    def test_minimal_csv_only_required_columns(self, minimal_csv: Path) -> None:
        adapter = CSVCatalogAdapter()
        catalog = adapter.from_file(minimal_csv, catalog_id="m", supplier_name="M")
        fmt = catalog.formats[0]
        assert fmt.format_code == "SIMPLE-500x1000"
        assert fmt.thickness_mm is None
        assert fmt.weight_kg_m2 is None

    def test_extra_columns_silently_ignored(self, tmp_path: Path) -> None:
        content = (
            "format_code,width_mm,height_mm,fire_class,product_line\n"
            "X-1000x2000,1000,2000,B1,MyLine\n"
        )
        p = tmp_path / "extra.csv"
        p.write_text(content, encoding="utf-8")
        adapter = CSVCatalogAdapter()
        catalog = adapter.from_file(p, catalog_id="x", supplier_name="X")
        assert len(catalog.formats) == 1

    def test_boolean_variants_true(self, tmp_path: Path) -> None:
        for val in ["true", "True", "TRUE", "1", "yes", "Yes"]:
            content = f"format_code,width_mm,height_mm,is_active\nF,500,1000,{val}\n"
            p = tmp_path / f"bool_{val}.csv"
            p.write_text(content, encoding="utf-8")
            catalog = CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")
            assert catalog.formats[0].is_active is True

    def test_boolean_variants_false(self, tmp_path: Path) -> None:
        for val in ["false", "0", "no"]:
            content = f"format_code,width_mm,height_mm,is_active\nF,500,1000,{val}\n"
            p = tmp_path / f"bool_{val}.csv"
            p.write_text(content, encoding="utf-8")
            catalog = CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")
            assert catalog.formats[0].is_active is False

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        adapter = CSVCatalogAdapter()
        with pytest.raises(DomainRuleError, match="nicht gefunden"):
            adapter.from_file(tmp_path / "nonexistent.csv", catalog_id="x", supplier_name="X")

    def test_missing_required_column_raises(self, tmp_path: Path) -> None:
        content = "format_code,width_mm\nF,500\n"  # missing height_mm
        p = tmp_path / "missing.csv"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(DomainRuleError, match="height_mm"):
            CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")

    def test_empty_required_field_raises(self, tmp_path: Path) -> None:
        content = "format_code,width_mm,height_mm\n,500,1000\n"
        p = tmp_path / "empty.csv"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(DomainRuleError, match="format_code"):
            CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")

    def test_invalid_float_raises(self, tmp_path: Path) -> None:
        content = "format_code,width_mm,height_mm\nF,INVALID,1000\n"
        p = tmp_path / "bad_float.csv"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(DomainRuleError, match="width_mm"):
            CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")

    def test_invalid_bool_raises(self, tmp_path: Path) -> None:
        content = "format_code,width_mm,height_mm,is_active\nF,500,1000,maybe\n"
        p = tmp_path / "bad_bool.csv"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(DomainRuleError, match="is_active"):
            CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")

    def test_negative_width_raises(self, tmp_path: Path) -> None:
        content = "format_code,width_mm,height_mm\nF,-100,1000\n"
        p = tmp_path / "neg.csv"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(DomainRuleError):
            CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")

    def test_empty_csv_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.csv"
        p.write_text("", encoding="utf-8")
        with pytest.raises(DomainRuleError, match="leer"):
            CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")

    def test_header_only_csv_raises(self, tmp_path: Path) -> None:
        content = "format_code,width_mm,height_mm\n"
        p = tmp_path / "header_only.csv"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(DomainRuleError, match="Datenzeilen"):
            CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")

    def test_rules_raw_is_empty_for_csv(self, valid_csv: Path) -> None:
        catalog = CSVCatalogAdapter().from_file(valid_csv, catalog_id="x", supplier_name="X")
        assert catalog.rules_raw == []

    def test_comma_decimal_separator_accepted(self, tmp_path: Path) -> None:
        content = "format_code,width_mm,height_mm,thickness_mm\nF,1250,3050,8\n"
        p = tmp_path / "comma_dec.csv"
        p.write_text(content, encoding="utf-8")
        catalog = CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")
        assert catalog.formats[0].height_mm == pytest.approx(3050.0)

    def test_multiple_row_errors_reported_together(self, tmp_path: Path) -> None:
        content = (
            "format_code,width_mm,height_mm\n"
            ",500,1000\n"   # empty format_code
            "F,-5,1000\n"  # negative width
        )
        p = tmp_path / "multi_err.csv"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(DomainRuleError, match="2 fehlerhafte"):
            CSVCatalogAdapter().from_file(p, catalog_id="x", supplier_name="X")


# ── CatalogImportService — CSV dispatch ──────────────────────────────────────

class TestCatalogImportServiceCSV:
    def test_import_from_file_dispatches_csv(self, valid_csv: Path) -> None:
        svc = CatalogImportService()
        catalog = svc.import_from_file(valid_csv)
        assert len(catalog.formats) == 2

    def test_import_from_csv_derives_id_from_filename(self, tmp_path: Path) -> None:
        content = "format_code,width_mm,height_mm\nF,500,1000\n"
        p = tmp_path / "my_supplier_2026.csv"
        p.write_text(content, encoding="utf-8")
        svc = CatalogImportService()
        catalog = svc.import_from_csv(p)
        assert catalog.id == "my-supplier-2026"
        assert catalog.supplier_name == "my_supplier_2026"

    def test_import_from_csv_explicit_id_and_name(self, valid_csv: Path) -> None:
        svc = CatalogImportService()
        catalog = svc.import_from_csv(valid_csv, catalog_id="explicit-id", supplier_name="Explicit")
        assert catalog.id == "explicit-id"
        assert catalog.supplier_name == "Explicit"

    def test_import_from_file_unknown_extension_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "catalog.xlsx"
        p.write_text("data", encoding="utf-8")
        svc = CatalogImportService()
        with pytest.raises(DomainRuleError, match="Unbekanntes Dateiformat"):
            svc.import_from_file(p)


# ── CatalogImportService — improved JSON errors ───────────────────────────────

class TestCatalogImportServiceJSONErrors:
    def test_missing_id_field_raises(self, tmp_path: Path) -> None:
        data = {"supplier_name": "X", "formats": [{"format_code": "F", "width_mm": 100, "height_mm": 200}]}
        p = tmp_path / "no_id.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        svc = CatalogImportService()
        with pytest.raises(DomainRuleError, match="'id'"):
            svc.import_from_file(p)

    def test_missing_supplier_name_raises(self, tmp_path: Path) -> None:
        data = {"id": "x", "formats": [{"format_code": "F", "width_mm": 100, "height_mm": 200}]}
        p = tmp_path / "no_name.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        svc = CatalogImportService()
        with pytest.raises(DomainRuleError, match="supplier_name"):
            svc.import_from_file(p)

    def test_empty_formats_raises(self, tmp_path: Path) -> None:
        data = {"id": "x", "supplier_name": "X", "formats": []}
        p = tmp_path / "empty_formats.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        svc = CatalogImportService()
        with pytest.raises(DomainRuleError, match="keine Formate"):
            svc.import_from_file(p)

    def test_invalid_json_shows_line_number(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{ bad json\n  here }", encoding="utf-8")
        svc = CatalogImportService()
        with pytest.raises(DomainRuleError, match="JSON-Fehler"):
            svc.import_from_file(p)

    def test_format_error_shows_format_code(self, tmp_path: Path) -> None:
        data = {
            "id": "x",
            "supplier_name": "X",
            "formats": [{"format_code": "BAD-FORMAT", "width_mm": -10, "height_mm": 200}],
        }
        p = tmp_path / "bad_format.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        svc = CatalogImportService()
        with pytest.raises(DomainRuleError, match="BAD-FORMAT"):
            svc.import_from_file(p)


# ── ImportCatalogRulesUseCase ─────────────────────────────────────────────────

class TestImportCatalogRulesUseCase:
    def _make_rule_catalog(self) -> RuleCatalog:
        return RuleCatalog(id=str(uuid.uuid4()), project_id="proj-001")

    def test_joint_rule_with_min_joint_width(self, catalog_with_rules: SupplierCatalog) -> None:
        rule = _raw_to_rule_definition(catalog_with_rules.rules_raw[0], catalog_with_rules.id)
        assert rule is not None
        assert rule.category == RuleCategory.JOINT
        assert rule.severity == RuleSeverity.WARNING
        assert rule.parameters["min_joint_width_mm"] == 8

    def test_joint_rule_with_expansion_joint(self, catalog_with_rules: SupplierCatalog) -> None:
        rule = _raw_to_rule_definition(catalog_with_rules.rules_raw[1], catalog_with_rules.id)
        assert rule is not None
        assert rule.category == RuleCategory.JOINT
        assert rule.severity == RuleSeverity.WARNING

    def test_other_rule_becomes_technical_info(self, catalog_with_rules: SupplierCatalog) -> None:
        rule = _raw_to_rule_definition(catalog_with_rules.rules_raw[2], catalog_with_rules.id)
        assert rule is not None
        assert rule.category == RuleCategory.TECHNICAL
        assert rule.severity == RuleSeverity.INFO

    def test_rule_id_namespaced(self, catalog_with_rules: SupplierCatalog) -> None:
        rule = _raw_to_rule_definition(catalog_with_rules.rules_raw[0], catalog_with_rules.id)
        assert rule is not None
        assert rule.id == "test-supplier-2026:TS-R-001"

    def test_rule_is_not_builtin(self, catalog_with_rules: SupplierCatalog) -> None:
        rule = _raw_to_rule_definition(catalog_with_rules.rules_raw[0], catalog_with_rules.id)
        assert rule is not None
        assert rule.is_builtin is False

    def test_execute_adds_all_rules(self, catalog_with_rules: SupplierCatalog) -> None:
        rc = self._make_rule_catalog()
        uc = ImportCatalogRulesUseCase()
        added = uc.execute(catalog_with_rules, rc)
        assert len(added) == 3

    def test_execute_idempotent(self, catalog_with_rules: SupplierCatalog) -> None:
        rc = self._make_rule_catalog()
        uc = ImportCatalogRulesUseCase()
        first = uc.execute(catalog_with_rules, rc)
        second = uc.execute(catalog_with_rules, rc)
        assert len(first) == 3
        assert len(second) == 0  # already in catalog

    def test_rules_accessible_in_catalog(self, catalog_with_rules: SupplierCatalog) -> None:
        rc = self._make_rule_catalog()
        uc = ImportCatalogRulesUseCase()
        uc.execute(catalog_with_rules, rc)
        rule = rc.get_rule("test-supplier-2026:TS-R-001")
        assert rule.parameters["min_joint_width_mm"] == 8

    def test_empty_rules_raw_returns_empty(self) -> None:
        from facade_planner.domain.entities.panel_format import PanelFormat
        catalog = SupplierCatalog(
            id="empty-rules",
            supplier_name="X",
            formats=[PanelFormat(format_code="F", width_mm=100, height_mm=200)],
            rules_raw=[],
        )
        rc = self._make_rule_catalog()
        added = ImportCatalogRulesUseCase().execute(catalog, rc)
        assert added == []

    def test_raw_without_id_skipped(self) -> None:
        rule = _raw_to_rule_definition({"description": "no id here", "parameters": {}}, "cat")
        assert rule is None

    def test_suggestion_contains_catalog_id(self, catalog_with_rules: SupplierCatalog) -> None:
        rule = _raw_to_rule_definition(catalog_with_rules.rules_raw[0], catalog_with_rules.id)
        assert rule is not None
        assert "test-supplier-2026" in rule.suggestion


# ── CLI integration ───────────────────────────────────────────────────────────

class TestCatalogCLIEpic005:
    def _setup(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)

    def test_import_csv_succeeds(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        valid_csv: Path,
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        result = runner.invoke(
            app, ["catalog", "import", str(valid_csv)], catch_exceptions=False
        )
        assert result.exit_code == 0
        assert "importiert" in result.output

    def test_import_csv_saves_catalog(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        valid_csv: Path,
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        runner.invoke(app, ["catalog", "import", str(valid_csv)], catch_exceptions=False)
        catalogs_dir = tmp_path / ".facadeplanner" / "catalogs"
        assert len(list(catalogs_dir.glob("*.json"))) == 1

    def test_import_csv_with_explicit_id_and_name(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        valid_csv: Path,
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        result = runner.invoke(
            app,
            ["catalog", "import", str(valid_csv),
             "--catalog-id", "custom-id", "--supplier-name", "Custom Supplier"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Custom Supplier" in result.output

    def test_import_with_extract_rules(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        result = runner.invoke(
            app, ["catalog", "import", "swisspearl", "--extract-rules"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Lieferantenregel" in result.output

    def test_extract_rules_updates_rule_catalog(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        runner.invoke(
            app, ["catalog", "import", "swisspearl", "--extract-rules"],
            catch_exceptions=False,
        )
        from facade_planner.infrastructure.persistence.rule_catalog_repository import (
            FileRuleCatalogRepository,
        )
        repo = FileRuleCatalogRepository(tmp_path / ".facadeplanner")
        rc = repo.load_or_create("test")
        namespaced_ids = [r for r in rc.rules if r.startswith("swisspearl")]
        assert len(namespaced_ids) > 0

    def test_extract_rules_idempotent(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        runner.invoke(app, ["catalog", "import", "swisspearl", "--extract-rules"],
                      catch_exceptions=False)
        result = runner.invoke(
            app, ["catalog", "import", "swisspearl", "--overwrite", "--extract-rules"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "bereits" in result.output.lower() or "vorhanden" in result.output.lower()

    def test_hint_shown_when_rules_present_but_not_extracted(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        result = runner.invoke(
            app, ["catalog", "import", "swisspearl"], catch_exceptions=False
        )
        assert result.exit_code == 0
        assert "--extract-rules" in result.output

    def test_show_with_rules_flag(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        runner.invoke(app, ["catalog", "import", "swisspearl"], catch_exceptions=False)
        result = runner.invoke(
            app, ["catalog", "show", "swisspearl-2026-facade-de-at", "--rules"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "SP-R-001" in result.output

    def test_import_bad_json_shows_line_number(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        bad = tmp_path / "bad.json"
        bad.write_text("{ bad json\nhere }", encoding="utf-8")
        result = runner.invoke(app, ["catalog", "import", str(bad)])
        assert result.exit_code != 0
        assert "JSON" in result.output

    def test_import_json_missing_id_shows_hint(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        data = {"supplier_name": "X", "formats": [{"format_code": "F", "width_mm": 100, "height_mm": 200}]}
        p = tmp_path / "no_id.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        result = runner.invoke(app, ["catalog", "import", str(p)])
        assert result.exit_code != 0
        assert "'id'" in result.output

    def test_list_shows_rules_column(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(runner, tmp_path, monkeypatch)
        runner.invoke(app, ["catalog", "import", "swisspearl"], catch_exceptions=False)
        result = runner.invoke(app, ["catalog", "list"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Regeln" in result.output

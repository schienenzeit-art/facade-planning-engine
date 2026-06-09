"""Unit tests for catalog import infrastructure (EPIC-006 / Catalog Management).

Covers: CatalogImportService, FileSupplierCatalogRepository, catalog CLI commands.
"""
import json
import uuid
from pathlib import Path

import pytest
from typer.testing import CliRunner

from facade_planner.application.services.catalog_import_service import (
    BUNDLED_CATALOGS,
    CatalogImportService,
)
from facade_planner.cli.main import app
from facade_planner.domain.entities.supplier_catalog import SupplierCatalog
from facade_planner.domain.exceptions import DomainRuleError, EntityNotFoundError
from facade_planner.infrastructure.persistence.supplier_catalog_repository import (
    FileSupplierCatalogRepository,
)


# ── FIXTURES ─────────────────────────────────────────────────────────────────

@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def minimal_catalog_json(tmp_path: Path) -> Path:
    """A minimal valid catalog JSON file."""
    data = {
        "id": "test-catalog-001",
        "supplier_name": "Test Supplier",
        "source_path": "",
        "formats": [
            {
                "format_code": "TEST-1000x2000-4",
                "width_mm": 1000,
                "height_mm": 2000,
                "thickness_mm": 4,
                "weight_kg_m2": 5.5,
                "description": "Test format",
                "is_active": True,
                # Extra fields that PanelFormat doesn't know — must be silently ignored
                "product_line": "Test Line",
                "fire_class": "B2",
                "mounting": ["horizontal"],
            }
        ],
        "rules_raw": [],
        # Extra top-level fields that SupplierCatalog doesn't know — also ignored
        "notes": ["Some note"],
        "source_document": "test.pdf",
    }
    p = tmp_path / "test_catalog.json"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


@pytest.fixture
def catalog_with_invalid_format(tmp_path: Path) -> Path:
    """A catalog JSON with one invalid format (missing required width_mm)."""
    data = {
        "id": "bad-catalog",
        "supplier_name": "Bad Supplier",
        "formats": [
            {
                "format_code": "BAD-FORMAT",
                # missing width_mm and height_mm
                "thickness_mm": 4,
            }
        ],
        "rules_raw": [],
    }
    p = tmp_path / "bad_catalog.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ── CATALOG IMPORT SERVICE ────────────────────────────────────────────────────

class TestCatalogImportService:
    def test_available_bundled_returns_all_four(self) -> None:
        svc = CatalogImportService()
        available = svc.available_bundled()
        assert "swisspearl" in available
        assert "alucobond-a2" in available
        assert "alucobond-plus" in available
        assert "alucobond-standard" in available

    def test_import_bundled_swisspearl(self) -> None:
        svc = CatalogImportService()
        catalog = svc.import_bundled("swisspearl")
        assert catalog.supplier_name == "Swisspearl"
        assert len(catalog.formats) > 0
        assert catalog.id == "swisspearl-2026-facade-de-at"

    def test_import_bundled_alucobond_a2(self) -> None:
        svc = CatalogImportService()
        catalog = svc.import_bundled("alucobond-a2")
        assert catalog.supplier_name == "ALUCOBOND"
        assert len(catalog.formats) > 0

    def test_import_bundled_alucobond_plus(self) -> None:
        svc = CatalogImportService()
        catalog = svc.import_bundled("alucobond-plus")
        assert len(catalog.formats) > 0

    def test_import_bundled_alucobond_standard(self) -> None:
        svc = CatalogImportService()
        catalog = svc.import_bundled("alucobond-standard")
        assert len(catalog.formats) > 0

    def test_import_bundled_unknown_raises(self) -> None:
        svc = CatalogImportService()
        with pytest.raises(DomainRuleError, match="Unbekannter Katalog-Name"):
            svc.import_bundled("nonexistent")

    def test_import_from_file_parses_formats(self, minimal_catalog_json: Path) -> None:
        svc = CatalogImportService()
        catalog = svc.import_from_file(minimal_catalog_json)
        assert catalog.id == "test-catalog-001"
        assert catalog.supplier_name == "Test Supplier"
        assert len(catalog.formats) == 1
        assert catalog.formats[0].format_code == "TEST-1000x2000-4"
        assert catalog.formats[0].width_mm == 1000.0

    def test_import_from_file_ignores_extra_format_fields(self, minimal_catalog_json: Path) -> None:
        """product_line, fire_class, mounting etc. are not in PanelFormat but must not raise."""
        svc = CatalogImportService()
        catalog = svc.import_from_file(minimal_catalog_json)
        assert len(catalog.formats) == 1

    def test_import_from_file_missing_file_raises(self, tmp_path: Path) -> None:
        svc = CatalogImportService()
        with pytest.raises(DomainRuleError, match="nicht gefunden"):
            svc.import_from_file(tmp_path / "nonexistent.json")

    def test_import_from_file_invalid_json_raises(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ not valid json }", encoding="utf-8")
        svc = CatalogImportService()
        with pytest.raises(DomainRuleError, match="JSON"):
            svc.import_from_file(bad_file)

    def test_import_from_file_invalid_format_raises(self, catalog_with_invalid_format: Path) -> None:
        svc = CatalogImportService()
        with pytest.raises(DomainRuleError, match="ungueltiges Format"):
            svc.import_from_file(catalog_with_invalid_format)

    def test_import_sets_imported_at_to_now(self, minimal_catalog_json: Path) -> None:
        from datetime import datetime, timezone
        svc = CatalogImportService()
        before = datetime.now()
        catalog = svc.import_from_file(minimal_catalog_json)
        after = datetime.now()
        assert before <= catalog.imported_at <= after

    def test_swisspearl_has_rules_raw(self) -> None:
        svc = CatalogImportService()
        catalog = svc.import_bundled("swisspearl")
        assert len(catalog.rules_raw) > 0

    def test_swisspearl_all_formats_have_dimensions(self) -> None:
        svc = CatalogImportService()
        catalog = svc.import_bundled("swisspearl")
        for fmt in catalog.formats:
            assert fmt.width_mm > 0
            assert fmt.height_mm > 0

    def test_swisspearl_all_formats_have_thickness(self) -> None:
        svc = CatalogImportService()
        catalog = svc.import_bundled("swisspearl")
        for fmt in catalog.formats:
            assert fmt.thickness_mm is not None and fmt.thickness_mm > 0

    def test_alucobond_a2_all_formats_have_weight(self) -> None:
        svc = CatalogImportService()
        catalog = svc.import_bundled("alucobond-a2")
        for fmt in catalog.formats:
            assert fmt.weight_kg_m2 is not None and fmt.weight_kg_m2 > 0


# ── FILE SUPPLIER CATALOG REPOSITORY ─────────────────────────────────────────

class TestFileSupplierCatalogRepository:
    def _make_catalog(self, catalog_id: str = "cat-001") -> SupplierCatalog:
        from facade_planner.domain.entities.panel_format import PanelFormat
        return SupplierCatalog(
            id=catalog_id,
            supplier_name="Test Supplier",
            formats=[
                PanelFormat(
                    format_code="T-1000x2000-4",
                    width_mm=1000,
                    height_mm=2000,
                    thickness_mm=4,
                )
            ],
        )

    def test_save_creates_file(self, tmp_path: Path) -> None:
        repo = FileSupplierCatalogRepository(tmp_path)
        catalog = self._make_catalog()
        repo.save(catalog)
        assert (tmp_path / "cat-001.json").exists()

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        repo = FileSupplierCatalogRepository(tmp_path)
        original = self._make_catalog()
        repo.save(original)
        loaded = repo.load("cat-001")
        assert loaded.id == original.id
        assert loaded.supplier_name == original.supplier_name
        assert len(loaded.formats) == 1
        assert loaded.formats[0].format_code == "T-1000x2000-4"

    def test_load_missing_raises(self, tmp_path: Path) -> None:
        repo = FileSupplierCatalogRepository(tmp_path)
        with pytest.raises(EntityNotFoundError):
            repo.load("nonexistent")

    def test_exists_false_before_save(self, tmp_path: Path) -> None:
        repo = FileSupplierCatalogRepository(tmp_path)
        assert not repo.exists("cat-001")

    def test_exists_true_after_save(self, tmp_path: Path) -> None:
        repo = FileSupplierCatalogRepository(tmp_path)
        repo.save(self._make_catalog())
        assert repo.exists("cat-001")

    def test_list_all_empty_dir(self, tmp_path: Path) -> None:
        repo = FileSupplierCatalogRepository(tmp_path / "nonexistent")
        assert repo.list_all() == []

    def test_list_all_returns_all_saved(self, tmp_path: Path) -> None:
        repo = FileSupplierCatalogRepository(tmp_path)
        repo.save(self._make_catalog("cat-001"))
        repo.save(self._make_catalog("cat-002"))
        catalogs = repo.list_all()
        assert len(catalogs) == 2
        ids = {c.id for c in catalogs}
        assert "cat-001" in ids and "cat-002" in ids

    def test_delete_removes_file(self, tmp_path: Path) -> None:
        repo = FileSupplierCatalogRepository(tmp_path)
        repo.save(self._make_catalog())
        repo.delete("cat-001")
        assert not repo.exists("cat-001")

    def test_delete_missing_raises(self, tmp_path: Path) -> None:
        repo = FileSupplierCatalogRepository(tmp_path)
        with pytest.raises(EntityNotFoundError):
            repo.delete("nonexistent")


# ── CLI COMMANDS ──────────────────────────────────────────────────────────────

class TestCatalogCLI:
    def test_available_command(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["catalog", "available"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "swisspearl" in result.output
        assert "alucobond-a2" in result.output

    def test_import_bundled_requires_project(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["catalog", "import", "swisspearl"])
        assert result.exit_code != 0

    def test_import_bundled_swisspearl(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        result = runner.invoke(app, ["catalog", "import", "swisspearl"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Swisspearl" in result.output

    def test_import_creates_catalog_file(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        runner.invoke(app, ["catalog", "import", "alucobond-a2"], catch_exceptions=False)
        assert (tmp_path / ".facadeplanner" / "catalogs" / "alucobond-a2.json").exists()

    def test_import_duplicate_blocked(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        runner.invoke(app, ["catalog", "import", "swisspearl"], catch_exceptions=False)
        result = runner.invoke(app, ["catalog", "import", "swisspearl"])
        assert result.exit_code != 0
        assert "bereits importiert" in result.output

    def test_import_overwrite_flag(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        runner.invoke(app, ["catalog", "import", "swisspearl"], catch_exceptions=False)
        result = runner.invoke(
            app, ["catalog", "import", "swisspearl", "--overwrite"], catch_exceptions=False
        )
        assert result.exit_code == 0

    def test_list_empty(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        result = runner.invoke(app, ["catalog", "list"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Keine Kataloge" in result.output

    def test_list_shows_imported(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        runner.invoke(app, ["catalog", "import", "swisspearl"], catch_exceptions=False)
        result = runner.invoke(app, ["catalog", "list"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Swisspearl" in result.output

    def test_show_catalog(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        runner.invoke(app, ["catalog", "import", "alucobond-a2"], catch_exceptions=False)
        result = runner.invoke(
            app, ["catalog", "show", "alucobond-a2"], catch_exceptions=False
        )
        assert result.exit_code == 0
        assert "ACB-A2" in result.output

    def test_import_from_custom_file(
        self,
        runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        minimal_catalog_json: Path,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["project", "create", "test"], catch_exceptions=False)
        result = runner.invoke(
            app, ["catalog", "import", str(minimal_catalog_json)], catch_exceptions=False
        )
        assert result.exit_code == 0
        assert "Test Supplier" in result.output

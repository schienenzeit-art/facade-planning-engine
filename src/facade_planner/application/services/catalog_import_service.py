"""CatalogImportService — loads supplier catalogs from JSON or CSV files.

Bundled catalogs live in data/catalogs/ relative to the project root.
Custom catalogs can be imported from any JSON or CSV file path.

JSON format is a superset of SupplierCatalog: extra keys (notes, product_line,
fire_class, mounting, fachweite_mm, source_document) are silently ignored.

CSV format: see CSVCatalogAdapter for schema documentation.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from facade_planner.domain.entities.panel_format import PanelFormat
from facade_planner.domain.entities.supplier_catalog import SupplierCatalog
from facade_planner.domain.exceptions import DomainRuleError

# Resolve bundled catalog directory relative to this file:
# service -> services -> application -> facade_planner -> src -> project_root -> data/catalogs
_BUNDLED_DIR = Path(__file__).parents[4] / "data" / "catalogs"

BUNDLED_CATALOGS: dict[str, str] = {
    "swisspearl": "swisspearl_2026_facade_DE-AT.json",
    "alucobond-a2": "alucobond_a2.json",
    "alucobond-plus": "alucobond_plus.json",
    "alucobond-standard": "alucobond_standard.json",
}


class CatalogImportService:
    """Parses catalog JSON/CSV files and returns validated SupplierCatalog objects."""

    def available_bundled(self) -> list[str]:
        """Return names of all bundled catalogs (usable as shorthand in import_bundled)."""
        return sorted(BUNDLED_CATALOGS.keys())

    def import_bundled(self, name: str) -> SupplierCatalog:
        """Import a bundled catalog by short name (e.g. 'swisspearl', 'alucobond-a2').

        Raises:
            DomainRuleError: if the name is not recognized.
        """
        if name not in BUNDLED_CATALOGS:
            available = ", ".join(sorted(BUNDLED_CATALOGS.keys()))
            raise DomainRuleError(
                f"Unbekannter Katalog-Name '{name}'. Verfuegbar: {available}"
            )
        return self.import_from_file(_BUNDLED_DIR / BUNDLED_CATALOGS[name])

    def import_from_file(self, path: Path) -> SupplierCatalog:
        """Parse a JSON or CSV catalog file and return a SupplierCatalog.

        Dispatches by file extension: .json -> JSON parser, .csv -> CSVCatalogAdapter.
        For CSV files the catalog_id and supplier_name are derived from the filename stem.

        Raises:
            DomainRuleError: if the file cannot be read, parsed, or is invalid.
        """
        if not path.exists():
            raise DomainRuleError(
                f"Katalog-Datei nicht gefunden: {path}\n"
                "Tipp: Pfad pruefen oder 'facade catalog available' fuer Bundled-Kataloge."
            )

        suffix = path.suffix.lower()
        if suffix == ".csv":
            return self.import_from_csv(path)
        if suffix == ".json":
            return self._import_json(path)

        raise DomainRuleError(
            f"Unbekanntes Dateiformat '{suffix}': {path}\n"
            "Unterstuetzte Formate: .json, .csv"
        )

    def import_from_csv(
        self,
        path: Path,
        catalog_id: str = "",
        supplier_name: str = "",
    ) -> SupplierCatalog:
        """Parse a CSV catalog file.

        catalog_id and supplier_name default to the filename stem when omitted.
        """
        from facade_planner.infrastructure.adapters.csv_catalog_adapter import (
            CSVCatalogAdapter,
        )

        derived_id = catalog_id or path.stem.lower().replace(" ", "-").replace("_", "-")
        derived_name = supplier_name or path.stem
        adapter = CSVCatalogAdapter()
        return adapter.from_file(path, catalog_id=derived_id, supplier_name=derived_name)

    def _import_json(self, path: Path) -> SupplierCatalog:
        """Internal: parse a JSON catalog file."""
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DomainRuleError(
                f"Katalog-Datei ist kein gueltiges JSON: {path}\n"
                f"JSON-Fehler in Zeile {exc.lineno}, Spalte {exc.colno}: {exc.msg}"
            ) from exc
        except UnicodeDecodeError as exc:
            raise DomainRuleError(
                f"Katalog-Datei ist nicht UTF-8 kodiert: {path}"
            ) from exc
        except Exception as exc:
            raise DomainRuleError(
                f"Fehler beim Lesen der Katalog-Datei: {path}\n{exc}"
            ) from exc

        return self._parse_raw(raw, source_path=str(path))

    @staticmethod
    def _parse_raw(raw: dict, source_path: str = "") -> SupplierCatalog:
        """Build a SupplierCatalog from a raw dict, ignoring unknown keys."""
        if not isinstance(raw, dict):
            raise DomainRuleError(
                "Katalog-Datei muss ein JSON-Objekt sein (kein Array oder Primitiv)."
            )

        catalog_id = raw.get("id", "")
        if not catalog_id:
            raise DomainRuleError(
                "Katalog-Datei fehlt das Pflichtfeld 'id'.\n"
                "Beispiel: { \"id\": \"mein-katalog-2026\", ... }"
            )

        supplier_name = raw.get("supplier_name", "")
        if not supplier_name:
            raise DomainRuleError(
                f"Katalog '{catalog_id}' fehlt das Pflichtfeld 'supplier_name'."
            )

        formats: list[PanelFormat] = []
        parse_errors: list[str] = []

        for i, fmt_data in enumerate(raw.get("formats", [])):
            fc = fmt_data.get("format_code", f"UNBEKANNT-{i}")
            known = {
                "format_code": fc,
                "width_mm": fmt_data.get("width_mm"),
                "height_mm": fmt_data.get("height_mm"),
                "thickness_mm": fmt_data.get("thickness_mm"),
                "weight_kg_m2": fmt_data.get("weight_kg_m2"),
                "description": fmt_data.get("description", ""),
                "is_active": fmt_data.get("is_active", True),
            }
            try:
                formats.append(PanelFormat.model_validate(known))
            except ValidationError as exc:
                field_errors = "; ".join(
                    f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()
                )
                parse_errors.append(f"  Format #{i+1} '{fc}': {field_errors}")

        if parse_errors:
            raise DomainRuleError(
                f"Katalog '{catalog_id}' enthaelt {len(parse_errors)} ungueltiges Format(e):\n"
                + "\n".join(parse_errors)
            )

        if not formats:
            raise DomainRuleError(
                f"Katalog '{catalog_id}' enthaelt keine Formate. "
                "Das Feld 'formats' muss mindestens einen Eintrag haben."
            )

        return SupplierCatalog(
            id=catalog_id,
            supplier_name=supplier_name,
            formats=formats,
            rules_raw=raw.get("rules_raw", []),
            imported_at=datetime.now(),
            source_path=source_path or raw.get("source_path", ""),
        )

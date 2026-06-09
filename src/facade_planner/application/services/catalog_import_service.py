"""CatalogImportService — loads supplier catalogs from JSON files.

Bundled catalogs live in data/catalogs/ relative to the project root.
Custom catalogs can be imported from any JSON file path.

JSON format is a superset of SupplierCatalog: extra keys (product_line,
fire_class, mounting, fachweite_mm, notes, source_document) are silently
ignored by Pydantic during validation.
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
# service → services → application → facade_planner → src → project_root → data/catalogs
_BUNDLED_DIR = Path(__file__).parents[4] / "data" / "catalogs"

BUNDLED_CATALOGS: dict[str, str] = {
    "swisspearl": "swisspearl_2026_facade_DE-AT.json",
    "alucobond-a2": "alucobond_a2.json",
    "alucobond-plus": "alucobond_plus.json",
    "alucobond-standard": "alucobond_standard.json",
}


class CatalogImportService:
    """Parses catalog JSON files and returns validated SupplierCatalog objects."""

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
                f"Unbekannter Katalog-Name '{name}'. Verfügbar: {available}"
            )
        return self.import_from_file(_BUNDLED_DIR / BUNDLED_CATALOGS[name])

    def import_from_file(self, path: Path) -> SupplierCatalog:
        """Parse a JSON catalog file and return a SupplierCatalog.

        The JSON may contain extra keys (notes, product_line, fire_class, etc.)
        beyond what SupplierCatalog stores — they are silently discarded.

        Raises:
            DomainRuleError: if the file cannot be read or parsed.
        """
        if not path.exists():
            raise DomainRuleError(f"Katalog-Datei nicht gefunden: {path}")

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise DomainRuleError(f"Katalog-Datei ist kein gültiges JSON: {exc}") from exc

        return self._parse_raw(raw, source_path=str(path))

    @staticmethod
    def _parse_raw(raw: dict, source_path: str = "") -> SupplierCatalog:
        """Build a SupplierCatalog from a raw dict, ignoring unknown keys."""
        formats: list[PanelFormat] = []
        parse_errors: list[str] = []

        for i, fmt_data in enumerate(raw.get("formats", [])):
            # Extract only the fields PanelFormat knows about
            known = {
                "format_code": fmt_data.get("format_code", f"UNKNOWN-{i}"),
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
                parse_errors.append(
                    f"Format #{i} ({known['format_code']}): {exc.error_count()} Fehler"
                )

        if parse_errors:
            raise DomainRuleError(
                f"Katalog enthält {len(parse_errors)} ungültige Format(e):\n"
                + "\n".join(parse_errors)
            )

        return SupplierCatalog(
            id=raw.get("id", ""),
            supplier_name=raw.get("supplier_name", ""),
            formats=formats,
            rules_raw=raw.get("rules_raw", []),
            imported_at=datetime.now(),
            source_path=source_path or raw.get("source_path", ""),
        )

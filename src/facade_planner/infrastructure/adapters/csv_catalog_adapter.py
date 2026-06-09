"""CSVCatalogAdapter — import panel formats from a CSV file.

CSV Schema v1.0
---------------
Header row is mandatory. Delimiter: comma. Encoding: UTF-8.

Required columns  : format_code, width_mm, height_mm
Optional columns  : thickness_mm, weight_kg_m2, description, is_active
Extra columns     : silently ignored

Boolean (is_active): true / false / 1 / 0 / yes / no  (case-insensitive)

Example
-------
format_code,width_mm,height_mm,thickness_mm,weight_kg_m2,description,is_active
MY-1250x3050-8,1250,3050,8,16.0,My panel format,true
"""
from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ValidationError

from facade_planner.domain.entities.panel_format import PanelFormat
from facade_planner.domain.entities.supplier_catalog import SupplierCatalog
from facade_planner.domain.exceptions import DomainRuleError

# Columns that map directly to PanelFormat fields
_REQUIRED_COLUMNS: frozenset[str] = frozenset({"format_code", "width_mm", "height_mm"})
_OPTIONAL_COLUMNS: frozenset[str] = frozenset(
    {"thickness_mm", "weight_kg_m2", "description", "is_active"}
)
_ALL_KNOWN_COLUMNS: frozenset[str] = _REQUIRED_COLUMNS | _OPTIONAL_COLUMNS

_BOOL_TRUE = {"true", "1", "yes", "ja"}
_BOOL_FALSE = {"false", "0", "no", "nein"}


class CSVCatalogAdapter:
    """Parse a CSV file and return a SupplierCatalog."""

    def from_file(
        self,
        path: Path,
        catalog_id: str,
        supplier_name: str,
    ) -> SupplierCatalog:
        """Read a CSV file and build a SupplierCatalog.

        Args:
            path: Path to the CSV file (UTF-8, comma-delimited).
            catalog_id: Catalog identifier (used as catalog ID in the project).
            supplier_name: Human-readable supplier name.

        Raises:
            DomainRuleError: on missing file, encoding errors, missing columns,
                             or invalid cell values.
        """
        if not path.exists():
            raise DomainRuleError(f"CSV-Datei nicht gefunden: {path}")

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise DomainRuleError(
                f"CSV-Datei ist nicht UTF-8 kodiert: {path}\n"
                "Bitte die Datei als UTF-8 (ohne BOM) speichern."
            ) from exc

        reader = csv.DictReader(text.splitlines())

        if reader.fieldnames is None:
            raise DomainRuleError(f"CSV-Datei ist leer oder hat keine Kopfzeile: {path}")

        missing = _REQUIRED_COLUMNS - {c.strip() for c in reader.fieldnames}
        if missing:
            raise DomainRuleError(
                f"CSV-Datei hat fehlende Pflicht-Spalten: {sorted(missing)}\n"
                f"Vorhandene Spalten: {list(reader.fieldnames)}\n"
                f"Benötigt: format_code, width_mm, height_mm"
            )

        formats: list[PanelFormat] = []
        parse_errors: list[str] = []

        for row_num, row in enumerate(reader, start=2):
            stripped = {k.strip(): v.strip() for k, v in row.items() if k is not None}
            try:
                fmt = _parse_row(stripped, row_num)
                formats.append(fmt)
            except DomainRuleError as exc:
                parse_errors.append(str(exc))

        if parse_errors:
            raise DomainRuleError(
                f"CSV enthält {len(parse_errors)} fehlerhafte Zeile(n):\n"
                + "\n".join(f"  {e}" for e in parse_errors)
            )

        if not formats:
            raise DomainRuleError(
                f"CSV-Datei enthält keine Datenzeilen (nur Kopfzeile?): {path}"
            )

        return SupplierCatalog(
            id=catalog_id,
            supplier_name=supplier_name,
            formats=formats,
            rules_raw=[],
            source_path=str(path),
        )


def _parse_row(row: dict[str, str], row_num: int) -> PanelFormat:
    """Convert a stripped CSV row dict into a PanelFormat."""
    try:
        raw: dict = {
            "format_code": _require_str(row, "format_code", row_num),
            "width_mm": _require_float(row, "width_mm", row_num),
            "height_mm": _require_float(row, "height_mm", row_num),
        }
        if row.get("thickness_mm", ""):
            raw["thickness_mm"] = _parse_float(row["thickness_mm"], "thickness_mm", row_num)
        if row.get("weight_kg_m2", ""):
            raw["weight_kg_m2"] = _parse_float(row["weight_kg_m2"], "weight_kg_m2", row_num)
        if row.get("description", ""):
            raw["description"] = row["description"]
        if row.get("is_active", ""):
            raw["is_active"] = _parse_bool(row["is_active"], row_num)

        return PanelFormat.model_validate(raw)

    except DomainRuleError:
        raise
    except ValidationError as exc:
        raise DomainRuleError(
            f"Zeile {row_num}: Pydantic-Validierungsfehler — {exc.error_count()} Fehler: "
            + "; ".join(str(e["msg"]) for e in exc.errors())
        ) from exc


def _require_str(row: dict, col: str, row_num: int) -> str:
    val = row.get(col, "").strip()
    if not val:
        raise DomainRuleError(f"Zeile {row_num}: Pflichtfeld '{col}' ist leer.")
    return val


def _require_float(row: dict, col: str, row_num: int) -> float:
    val = row.get(col, "").strip()
    if not val:
        raise DomainRuleError(f"Zeile {row_num}: Pflichtfeld '{col}' ist leer.")
    return _parse_float(val, col, row_num)


def _parse_float(val: str, col: str, row_num: int) -> float:
    try:
        return float(val.replace(",", "."))
    except ValueError:
        raise DomainRuleError(
            f"Zeile {row_num}: Spalte '{col}' — kein gültiger Zahlenwert: '{val}'"
        )


def _parse_bool(val: str, row_num: int) -> bool:
    lower = val.lower()
    if lower in _BOOL_TRUE:
        return True
    if lower in _BOOL_FALSE:
        return False
    raise DomainRuleError(
        f"Zeile {row_num}: Spalte 'is_active' — ungültiger Wahrheitswert: '{val}'. "
        "Erlaubt: true/false/1/0/yes/no"
    )

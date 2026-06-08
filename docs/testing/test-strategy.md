# Teststrategie
## Facade Planning Engine — MVP

**Version:** 1.0  
**Status:** Draft  
**Datum:** 2026-06-08  

---

## 1. Teststrategie-Übersicht

### Testing-Pyramide

```
                    ╔═══════════╗
                    ║   E2E     ║  ~ 5%  — vollständige Workflows
                    ╠═══════════╣
                  ╔═══════════════╗
                  ║  Integration  ║  ~ 25% — Adapter + Use Cases
                  ╠═══════════════╣
              ╔═════════════════════╗
              ║      Unit Tests      ║  ~ 70% — Domänenlogik
              ╚══════════════════════╝
```

**Ziel-Coverage:** ≥ 80% für `domain/` und `application/`, ≥ 60% für `infrastructure/`

---

## 2. Unit Tests

**Scope:** `facade_engine/domain/` und `facade_engine/application/`  
**Ziel:** Schnelle, isolierte Tests der Geschäftslogik  
**Charakteristik:** Kein Dateisystem, kein I/O, keine externen Bibliotheken (ausser shapely)  
**Laufzeit:** < 5 Sekunden für die gesamte Unit-Test-Suite  

### 2.1 Domain — Value Objects

**Datei:** `tests/unit/domain/test_value_objects.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_scale_factor_100` | Scale(1, 100).factor() == 0.01 |
| `test_scale_invalid_zero_denominator` | Scale(1, 0) wirft ValueError |
| `test_point2d_distance` | Distanz zwischen zwei Punkten korrekt |
| `test_polygon_area_rectangle` | Rechteckige Polygon-Fläche korrekt |
| `test_polygon_is_closed` | Geschlossenes vs. offenes Polygon |
| `test_polygon_contains_point` | Point-in-Polygon korrekt |
| `test_bounding_box_from_polygon` | BoundingBox aus Polygon korrekt |
| `test_panel_id_valid_format` | PA-001-042 wird akzeptiert |
| `test_panel_id_invalid_format` | PA-1 wirft ValidationError |
| `test_surface_id_valid_format` | FA-001 wird akzeptiert |

### 2.2 Domain — FacadeSurface

**Datei:** `tests/unit/domain/test_facade_surface.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_surface_net_area_without_openings` | Nettofläche == Bruttofläche wenn keine Öffnungen |
| `test_surface_net_area_with_openings` | Nettofläche = Brutto - Öffnungen |
| `test_surface_opening_must_be_inside_boundary` | Öffnung ausserhalb wirft DomainError |
| `test_surface_confirm_status_change` | Status DETECTED → CONFIRMED |
| `test_surface_reject_status_change` | Status DETECTED → REJECTED |
| `test_surface_id_uniqueness` | Zwei Surfaces mit gleicher ID nicht möglich |

### 2.3 Domain — GeometryService

**Datei:** `tests/unit/domain/test_geometry_service.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_apply_scale_to_geometries` | Koordinaten werden korrekt skaliert |
| `test_close_nearly_closed_polygon` | Polygon mit kleinem Gap wird geschlossen |
| `test_polygon_subtraction` | Öffnung wird aus Fläche ausgeschnitten |
| `test_detect_overlapping_polygons` | Überlappende Polygone erkannt |
| `test_bounding_box_intersection` | Schnittpunkt zweier BoundingBoxen |

### 2.4 Domain — FormatSelectionService

**Datei:** `tests/unit/domain/test_format_selection.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_select_exact_fit_format` | Format das genau passt wird gewählt |
| `test_select_smallest_fitting_format` | Kleinstmögliches passendes Format |
| `test_no_format_fits_returns_none` | Kein passendes Format → None |
| `test_prefer_full_panel_format` | Vollplatte bevorzugt gegenüber Zuschnitt |
| `test_format_violates_gr002` | Panel > Rohplatte wird verhindert |
| `test_format_from_correct_catalog` | Nur Formate aus aktivem Katalog |

### 2.5 Domain — PanelizationService / GridAlgorithm

**Datei:** `tests/unit/domain/test_panelization_service.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_panelize_simple_rectangle` | Rechteck → korrekte Panel-Anzahl |
| `test_panelize_with_joint_width` | Fugen werden in Panel-Positionen berücksichtigt |
| `test_panelize_full_coverage` | Alle Panels bedecken die gesamte Fläche |
| `test_panelize_no_overlaps` | Keine zwei Panels überlappen sich |
| `test_panelize_opening_excluded` | Panel überdeckt keine Öffnungsfläche |
| `test_panelize_respects_min_width` | Randpanele ≥ Mindestbreite |
| `test_panelize_assigns_unique_ids` | Alle Panel-IDs eindeutig |
| `test_panelize_all_panels_within_surface` | Kein Panel ausserhalb Fassadenfläche |
| `test_panelize_gr001_all_panels_have_format` | Alle Panels haben Format-Referenz |
| `test_panelize_gr002_panel_not_larger_than_format` | Kein Panel grösser als Rohplatte |
| `test_panelize_no_available_formats` | Kein Format verfügbar → PanelizationError |
| `test_panelize_horizontal_orientation` | Horizontale Ausrichtung korrekt |
| `test_panelize_vertical_orientation` | Vertikale Ausrichtung korrekt |

### 2.6 Domain — ValidationService

**Datei:** `tests/unit/domain/test_validation_service.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_validate_gr001` | Panel ohne Format → WARNING |
| `test_validate_gr002` | Panel > Rohplatte → WARNING |
| `test_validate_gr003` | Maße nicht in mm → ERROR |
| `test_validate_no_overlaps` | Überlappende Panels → WARNING |
| `test_validate_boundary` | Panel ausserhalb Boundary → ERROR |
| `test_validate_valid_result` | Gültiges Ergebnis → keine Warnungen |

### 2.7 Application — Use Cases (mit Mock-Adaptern)

**Datei:** `tests/unit/application/test_import_plan_usecase.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_import_plan_success` | Use Case erzeugt FacadePlan und speichert | 
| `test_import_plan_file_not_found` | Datei nicht vorhanden → klare Fehlermeldung |
| `test_import_plan_invalid_scale` | Maßstab 0:100 → ValidationError |
| `test_import_plan_calls_parser` | Parser-Port wird korrekt aufgerufen |
| `test_import_plan_calls_repository` | Repository-Port wird korrekt aufgerufen |

---

## 3. Integration Tests

**Scope:** Adapter + Repository + Use Cases mit echten Dateien  
**Charakteristik:** Dateisystem-Zugriff erlaubt, echte Bibliotheken (pdfminer, ezdxf)  
**Laufzeit:** < 30 Sekunden  
**Testdaten:** `fixtures/` Verzeichnis

### 3.1 PDF-Import-Adapter

**Datei:** `tests/integration/test_pdf_import.py`

| Testfall | Testdatei | Erwartetes Ergebnis |
|---------|-----------|-------------------|
| `test_import_simple_facade_pdf` | `fixtures/pdf/simple_facade.pdf` | Korrekte Anzahl Geometrien |
| `test_import_facade_with_windows` | `fixtures/pdf/facade_with_windows.pdf` | Geometrien inkl. Öffnungen |
| `test_import_multipage_pdf` | `fixtures/pdf/multi_page.pdf` | Alle Seiten verarbeitet |
| `test_import_raster_pdf_raises_error` | `fixtures/pdf/raster_scan.pdf` | ImportError mit klarer Meldung |
| `test_coordinates_after_scaling` | `fixtures/pdf/simple_facade.pdf` | Koordinaten in mm korrekt |
| `test_large_pdf_performance` | `fixtures/pdf/large_plan.pdf` | Import < 30 Sekunden |

### 3.2 Katalog-Import-Adapter

**Datei:** `tests/integration/test_catalog_import.py`

| Testfall | Testdatei | Erwartetes Ergebnis |
|---------|-----------|-------------------|
| `test_import_json_catalog` | `fixtures/catalogs/supplier_a.json` | Alle Formate geladen |
| `test_import_csv_catalog` | `fixtures/catalogs/supplier_b.csv` | Alle Formate geladen |
| `test_import_catalog_validates_formats` | `fixtures/catalogs/invalid_catalog.json` | ValidationError |
| `test_catalog_mm_values` | `fixtures/catalogs/supplier_a.json` | Alle Maße in mm |

### 3.3 File-Repository

**Datei:** `tests/integration/test_file_repository.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_save_and_load_facade_plan` | Plan wird gespeichert und korrekt geladen |
| `test_save_and_load_surface` | Surface mit Openings wird korrekt gespeichert |
| `test_save_and_load_panelization_job` | Job + Result wird korrekt gespeichert |
| `test_load_nonexistent_raises_error` | Nicht-existente ID → klare Fehlermeldung |
| `test_schema_version_in_files` | Alle Dateien enthalten `schema_version` |

### 3.4 DXF-Export-Adapter

**Datei:** `tests/integration/test_dxf_export.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_dxf_file_created` | DXF-Datei wird erzeugt |
| `test_dxf_opens_with_ezdxf` | Erzeugtes DXF kann von ezdxf gelesen werden |
| `test_dxf_has_correct_layers` | Layer pro FacadeSurface vorhanden |
| `test_dxf_has_all_panels` | Alle Panels als Rechtecke vorhanden |
| `test_dxf_has_panel_id_texts` | Panel-IDs als Text vorhanden |
| `test_dxf_units_mm` | DXF-Einheit ist mm |
| `test_dxf_version_ac1027` | DXF-Version ist AC1027 |

---

## 4. End-to-End Tests

**Scope:** Vollständiger Workflow via CLI  
**Charakteristik:** Black-Box — nur CLI-Befehle, keine internen Aufrufe  
**Laufzeit:** < 2 Minuten  

### 4.1 Vollständiger Workflow

**Datei:** `tests/e2e/test_full_workflow.py`

```
Test: test_complete_workflow_simple_facade

GIVEN: simple_facade.pdf (bekannte Testdatei)
       supplier_a.json (bekannte Formate)

WHEN:
  1. facade project create "test-project"
  2. facade plan import simple_facade.pdf --scale 1:100
  3. facade surface detect --plan <plan_id>
  4. facade surface confirm FA-001
  5. facade catalog import supplier_a.json
  6. facade panelize run --surface FA-001 --catalog CAT-001 --joint-width 10
  7. facade export dxf --job <job_id> --output test_output.dxf
  8. facade export report --job <job_id>

THEN:
  - Alle Befehle Exit-Code 0
  - DXF-Datei existiert und ist lesbar
  - Report-Datei existiert
  - Panel-Anzahl entspricht bekanntem Expected-Output
  - Keine Fehler-Warnungen
```

**Datei:** `tests/e2e/test_full_workflow.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_complete_workflow_simple_facade` | Vollständiger Workflow (wie oben) |
| `test_workflow_with_openings` | Workflow mit Fenstern/Türen |
| `test_workflow_multiple_surfaces` | Mehrere Flächen gleichzeitig |
| `test_workflow_invalid_pdf_error_message` | Klare Fehlermeldung bei ungültigem Input |

### 4.2 CLI-Befehle

**Datei:** `tests/e2e/test_cli_commands.py`

| Testfall | Beschreibung |
|---------|-------------|
| `test_all_commands_have_help` | Alle Befehle haben --help |
| `test_exit_code_0_on_success` | Erfolg → Exit-Code 0 |
| `test_exit_code_nonzero_on_error` | Fehler → Exit-Code ≠ 0 |
| `test_error_message_human_readable` | Fehlermeldungen ohne Stack Trace |

---

## 5. Testdatenstrategie

### 5.1 Testdaten-Kategorien

| Kategorie | Dateipfad | Beschreibung | Erstellt von |
|-----------|-----------|-------------|-------------|
| simple_facade.pdf | `fixtures/pdf/simple_facade.pdf` | Rechteckige Fassade 6000×3000mm, 1:100, kein Öffnungen | Manuell mit Illustrator/LibreOffice |
| facade_with_windows.pdf | `fixtures/pdf/facade_with_windows.pdf` | Fassade mit 2 Fenstern, 1:50 | Manuell |
| multi_page.pdf | `fixtures/pdf/multi_page.pdf` | 2-seitiger Plan (2 Ansichten) | Manuell |
| raster_scan.pdf | `fixtures/pdf/raster_scan.pdf` | Gescanntes PDF (rasterbasiert) | Scan eines Ausdrucks |
| large_plan.pdf | `fixtures/pdf/large_plan.pdf` | Grosser Plan >50 MB | Generiert |
| supplier_a.json | `fixtures/catalogs/supplier_a.json` | 5 Formate (3 Standard, 2 Sonderformat) | Manuell |
| supplier_b.csv | `fixtures/catalogs/supplier_b.csv` | CSV-Format mit 10 Formaten | Manuell |
| invalid_catalog.json | `fixtures/catalogs/invalid_catalog.json` | Ungültige Formate (width=0) | Manuell |
| expected_simple_panels.json | `fixtures/expected/simple_panels.json` | Erwartete Panels für simple_facade.pdf | Generiert nach Sprint 2 |

### 5.2 Testdaten-Erstellungsregeln

1. **Bekannte Masse:** Alle Testdaten haben dokumentierte, exakte Masse (z.B. Fassade genau 6000×3000mm)
2. **Reproduzierbarkeit:** Testdaten werden im Repository versioniert
3. **Keine echten Kundendaten:** Alle Testpläne sind synthetisch erstellt
4. **Skalierung explizit:** Jede Test-PDF hat ein dokumentiertes Maßstabsverhältnis
5. **Expected Output:** Für Regressionstests werden erwartete Outputs als JSON gespeichert

### 5.3 Testdaten-Generierungsskript

```
fixtures/
  generate_test_data.py   ← Skript zur Erzeugung synthetischer Test-PDFs
  README.md               ← Beschreibung aller Testdaten
```

---

## 6. CI/CD-Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml

on: [push, pull_request]

jobs:
  test:
    runs-on: [ubuntu-latest, windows-latest, macos-latest]  # Cross-Platform
    steps:
      - lint: ruff check + ruff format --check
      - typecheck: mypy src/
      - dependency-check: import-linter
      - unit-tests: pytest tests/unit/ -v --cov=facade_engine --cov-fail-under=80
      - integration-tests: pytest tests/integration/ -v
      - e2e-tests: pytest tests/e2e/ -v
      - coverage-report: Upload to Codecov
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - ruff (lint + format)
  - mypy (Typen)
  - import-linter (Dependency Rules)
  - pytest (Unit-Tests bei Commit, schnell)
```

---

## 7. Testabdeckungs-Ziele

| Modul | Ziel-Coverage | Priorität |
|-------|--------------|-----------|
| `domain/value_objects/` | 95% | Kritisch |
| `domain/entities/` | 90% | Kritisch |
| `domain/services/` | 90% | Kritisch |
| `domain/algorithms/` | 85% | Kritisch |
| `application/use_cases/` | 80% | Hoch |
| `infrastructure/pdf/` | 70% | Mittel |
| `infrastructure/export/` | 70% | Mittel |
| `infrastructure/persistence/` | 65% | Mittel |
| `cli/` | 60% | Niedrig |

---

## 8. Qualitätsgates

Pull Requests können nicht gemerged werden wenn:
- [ ] Unit-Test-Coverage < 80% in `domain/`
- [ ] mypy-Fehler vorhanden
- [ ] ruff-Linting-Fehler vorhanden
- [ ] Dependency-Rules verletzt (import-linter)
- [ ] E2E-Tests fehlschlagen

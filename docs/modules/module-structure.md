# Modulstruktur
## Facade Planning Engine — MVP

**Version:** 1.0  
**Status:** Draft  
**Datum:** 2026-06-08  

---

## 1. Python-Paketstruktur

```
facade-planning-engine/
│
├── pyproject.toml                  ← Projektmetadaten, Abhängigkeiten, Tools
├── README.md
├── CHANGELOG.md
├── .env.example
│
├── src/
│   └── facade_engine/              ← Hauptpaket
│       ├── __init__.py
│       │
│       ├── cli/                    ← CLI-Schicht (Einstiegspunkte)
│       │   ├── __init__.py
│       │   ├── main.py             ← CLI-App-Definition (typer)
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── project.py      ← facade project create/list/info
│       │   │   ├── plan.py         ← facade plan import/list/show
│       │   │   ├── surface.py      ← facade surface detect/list/confirm/reject
│       │   │   ├── catalog.py      ← facade catalog import/list/show
│       │   │   ├── panelize.py     ← facade panelize run/list/show
│       │   │   └── export.py       ← facade export dxf/report
│       │   └── formatters.py       ← Tabellenausgabe, Fehlerformatierung
│       │
│       ├── application/            ← Use Cases (Orchestrierung)
│       │   ├── __init__.py
│       │   ├── use_cases/
│       │   │   ├── __init__.py
│       │   │   ├── import_plan.py
│       │   │   ├── detect_surfaces.py
│       │   │   ├── confirm_surface.py
│       │   │   ├── import_catalog.py
│       │   │   ├── run_panelization.py
│       │   │   └── export_result.py
│       │   ├── ports/              ← Abstrakte Interfaces (Ports)
│       │   │   ├── __init__.py
│       │   │   ├── plan_import_port.py
│       │   │   ├── catalog_import_port.py
│       │   │   ├── export_port.py
│       │   │   └── repository_ports.py
│       │   └── dto/                ← Data Transfer Objects (Input/Output der Use Cases)
│       │       ├── __init__.py
│       │       ├── import_dto.py
│       │       ├── surface_dto.py
│       │       ├── panelization_dto.py
│       │       └── export_dto.py
│       │
│       ├── domain/                 ← Domänenlogik (KERN — keine Infrastrukturabhängigkeiten)
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   ├── facade_plan.py
│       │   │   ├── facade_surface.py
│       │   │   ├── opening.py
│       │   │   ├── panel.py
│       │   │   ├── panelization_job.py
│       │   │   └── supplier_catalog.py
│       │   ├── value_objects/
│       │   │   ├── __init__.py
│       │   │   ├── scale.py
│       │   │   ├── point2d.py
│       │   │   ├── polygon.py
│       │   │   ├── bounding_box.py
│       │   │   ├── panel_id.py
│       │   │   ├── surface_id.py
│       │   │   └── panel_format.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── geometry_service.py
│       │   │   ├── surface_detection_service.py
│       │   │   ├── panelization_service.py
│       │   │   ├── format_selection_service.py
│       │   │   └── validation_service.py
│       │   ├── algorithms/
│       │   │   ├── __init__.py
│       │   │   ├── base_algorithm.py   ← AbstractBaseClass für Algorithmen
│       │   │   └── grid_panelization.py ← Grid-basierter Panelisierungs-Algorithmus
│       │   └── exceptions.py           ← Domänen-spezifische Exceptions
│       │
│       └── infrastructure/         ← Adapter (Infrastruktur-Implementierungen)
│           ├── __init__.py
│           ├── pdf/
│           │   ├── __init__.py
│           │   ├── pdf_import_adapter.py   ← Implementiert PlanImportPort
│           │   ├── pdfminer_parser.py       ← pdfminer.six Wrapper
│           │   └── geometry_mapper.py       ← Koordinaten → Domänenobjekte
│           ├── catalog/
│           │   ├── __init__.py
│           │   ├── json_catalog_adapter.py  ← JSON-Katalog-Import
│           │   └── csv_catalog_adapter.py   ← CSV-Katalog-Import
│           ├── persistence/
│           │   ├── __init__.py
│           │   ├── file_repository.py       ← Implementiert alle Repository-Ports
│           │   ├── json_serializer.py       ← Pydantic → JSON
│           │   └── project_context.py       ← Projektverzeichnis-Verwaltung
│           └── export/
│               ├── __init__.py
│               ├── dxf_export_adapter.py    ← Implementiert ExportPort (ezdxf)
│               └── report_exporter.py       ← Textbericht
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 ← Pytest-Fixtures
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_facade_surface.py
│   │   │   ├── test_panel.py
│   │   │   ├── test_geometry_service.py
│   │   │   ├── test_panelization_service.py
│   │   │   ├── test_format_selection.py
│   │   │   ├── test_validation_service.py
│   │   │   └── test_value_objects.py
│   │   └── application/
│   │       ├── test_import_plan_usecase.py
│   │       ├── test_panelize_usecase.py
│   │       └── test_export_usecase.py
│   ├── integration/
│   │   ├── test_pdf_import.py      ← Echte PDF-Dateien
│   │   ├── test_catalog_import.py
│   │   ├── test_file_repository.py
│   │   └── test_dxf_export.py
│   └── e2e/
│       ├── test_full_workflow.py   ← PDF → Panelisierung → DXF
│       └── test_cli_commands.py    ← CLI-Befehle als Black-Box
│
├── fixtures/                       ← Testdaten
│   ├── pdf/
│   │   ├── simple_facade.pdf       ← Einfache rechteckige Fassade
│   │   ├── facade_with_windows.pdf ← Fassade mit Öffnungen
│   │   └── multi_page.pdf          ← Mehrseitiger Plan
│   ├── catalogs/
│   │   ├── supplier_a.json
│   │   └── supplier_b.csv
│   └── expected/
│       └── simple_facade_panels.json  ← Expected output für Regression-Tests
│
└── docs/
    └── (SDLC-Dokumentation)
```

---

## 2. Verantwortlichkeiten je Modul

### `facade_engine/cli/`
- **Was:** Kommandozeilenschnittstelle — einziger Einstiegspunkt für Nutzer
- **Erlaubt:** Argument-Parsing, Ausgabe-Formatierung, Fehlerausgabe
- **Verboten:** Geschäftslogik, direkte Datenbankzugriffe, direkte Bibliotheksaufrufe
- **Abhängigkeiten:** → `application/use_cases/`
- **Teststrategie:** CLI-Tests über `typer.testing.CliRunner`

### `facade_engine/application/`
- **Was:** Use Cases — orchestriert Domain + Infrastructure
- **Erlaubt:** Use-Case-Flows, Fehlerbehandlung, Logging
- **Verboten:** Geschäftslogik (gehört in Domain), direkte UI-Logik
- **Abhängigkeiten:** → `domain/`, via Ports → `infrastructure/`
- **Teststrategie:** Unit-Tests mit Mock-Implementierungen der Ports

### `facade_engine/application/ports/`
- **Was:** Abstrakte Interfaces (ABCs) — definieren was die Infrastruktur leisten muss
- **Erlaubt:** Nur Interface-Definitionen (ABC, Protocol)
- **Verboten:** Implementierungen, Imports von Infrastruktur-Bibliotheken
- **Abhängigkeiten:** → `domain/` (für Typen)

### `facade_engine/domain/`
- **Was:** Geschäftslogik — reines Python, keine externen Abhängigkeiten
- **Erlaubt:** Python stdlib, `shapely` (Geometrie), `pydantic` (Validierung)
- **Verboten:** Imports von `infrastructure/`, `application/`, `cli/`; keine I/O-Operationen
- **Abhängigkeiten:** Python stdlib, shapely, pydantic
- **Teststrategie:** Unit-Tests ohne Mocks (direkte Instanziierung)

### `facade_engine/infrastructure/pdf/`
- **Was:** PDF-Parsing und Geometrie-Extraktion
- **Erlaubt:** pdfminer.six, pymupdf, shapely
- **Verboten:** Domain-Logik; muss Port-Interface implementieren
- **Abhängigkeiten:** → `application/ports/`, → `domain/value_objects/`

### `facade_engine/infrastructure/persistence/`
- **Was:** Dateibasierte Persistenz aller Domänenobjekte
- **Erlaubt:** JSON, pathlib, pydantic für Serialisierung
- **Verboten:** Direkte Domänenlogik
- **Abhängigkeiten:** → `application/ports/`, → `domain/entities/`

### `facade_engine/infrastructure/export/`
- **Was:** DXF-Export und Textberichte
- **Erlaubt:** ezdxf, jinja2 (für Berichte optional)
- **Verboten:** Domänenlogik
- **Abhängigkeiten:** → `application/ports/`, → `domain/entities/`

---

## 3. Dependency Rules

### Erlaubte Abhängigkeitsrichtungen

```
CLI ──▶ Application ──▶ Domain
                ├──▶ (via Ports) Infrastructure
Infrastructure ──▶ Domain (für Typen)
Infrastructure ──▶ Application/Ports (Interface implementieren)

VERBOTEN:
Domain ──✗──▶ Infrastructure
Domain ──✗──▶ Application
Domain ──✗──▶ CLI
Application ──✗──▶ Infrastructure (direkt, nur via Ports)
```

### Import-Prüfung (Enforcement)

```toml
# pyproject.toml — dependency boundaries via import-linter
[tool.importlinter]
root_packages = ["facade_engine"]

[[tool.importlinter.contracts]]
name = "Domain must not import infrastructure"
type = "forbidden"
source_modules = ["facade_engine.domain"]
forbidden_modules = ["facade_engine.infrastructure", "facade_engine.cli"]

[[tool.importlinter.contracts]]
name = "Application must not import infrastructure directly"  
type = "forbidden"
source_modules = ["facade_engine.application.use_cases"]
forbidden_modules = ["facade_engine.infrastructure"]
```

---

## 4. CLI-Befehlsstruktur

```
facade [OPTIONS] COMMAND [ARGS]

  project
    create <name> [--path PATH]     Neues Projekt erstellen
    info                             Aktuelles Projekt anzeigen

  plan
    import <file> --scale 1:100     PDF importieren
    list                             Importierte Pläne auflisten
    show <plan-id>                   Plan-Details anzeigen

  surface
    detect --plan <plan-id>          Fassadenflächen erkennen
    list [--plan <plan-id>]          Flächen auflisten
    confirm <surface-id>             Fläche bestätigen
    reject <surface-id>              Fläche verwerfen
    show <surface-id>                Fläche anzeigen

  catalog
    import <file>                    Lieferantenkatalog importieren
    list                             Kataloge auflisten
    show <catalog-id>                Formate eines Katalogs anzeigen

  panelize
    run --surface <id>... --catalog <id>...  Panelisierung starten
        [--joint-width FLOAT]
        [--orientation horizontal|vertical|auto]
        [--min-width FLOAT]
        [--min-height FLOAT]
    list                             Jobs auflisten
    show <job-id>                    Ergebnis anzeigen

  export
    dxf <job-id> [--output PATH]    DXF exportieren
    report <job-id> [--output PATH] Textbericht exportieren
```

---

## 5. Konfiguration

```toml
# facade.toml (Projektkonfiguration, optional)
[project]
name = "Mein Fassadenprojekt"
units = "mm"

[defaults]
joint_width_mm = 10.0
panel_orientation = "auto"
min_panel_width_mm = 100.0
min_panel_height_mm = 100.0

[export.dxf]
version = "AC1027"
layer_prefix = "FACADE_"
```

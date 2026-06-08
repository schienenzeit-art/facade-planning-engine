# Systemarchitektur
## Facade Planning Engine — MVP

**Version:** 1.0  
**Status:** Draft  
**Datum:** 2026-06-08  
**Notation:** C4 Model (https://c4model.com)

---

## C4 Level 1 — System Context Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         SYSTEM CONTEXT                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

 ┌───────────────────┐          ┌──────────────────────────────────┐
 │   FASSADENPLANER  │          │                                  │
 │   (Hauptnutzer)   │          │     FACADE PLANNING ENGINE       │
 │                   │          │     (Software System)            │
 │  - Plant Fassaden │ ────────▶│                                  │
 │  - Prüft Pläne    │  CLI     │  Automatisiert die technische    │
 │  - Exportiert DXF │◀──────── │  Fassadenplanung: PDF-Import,    │
 │                   │          │  Geometrieextraktion,            │
 └───────────────────┘          │  Panelisierung, DXF-Export       │
                                │                                  │
                                └──────────────────────────────────┘
                                         │              │
                                         │              │
                                         ▼              ▼
                              ┌──────────────┐  ┌──────────────────┐
                              │   PDF-Pläne  │  │  Lieferanten-    │
                              │  (Dateien)   │  │  kataloge        │
                              │              │  │  (JSON/CSV)      │
                              │  Extern:     │  │                  │
                              │  AutoCAD,    │  │  Extern:         │
                              │  Revit,      │  │  Manuell         │
                              │  Illustrator │  │  gepflegt        │
                              └──────────────┘  └──────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │    AutoCAD /         │
                              │    BricsCAD           │
                              │    (DXF-Empfänger)   │
                              │                      │
                              │  Extern: CAD-        │
                              │  Techniker öffnet    │
                              │  exportiertes DXF    │
                              └──────────────────────┘
```

### Systemgrenzen

| Element | Typ | Beschreibung |
|---------|-----|-------------|
| Facade Planning Engine | Software System (intern) | Das zu entwickelnde System |
| Fassadenplaner | Person (Hauptnutzer) | Bedient CLI, liefert PDFs |
| PDF-Pläne | Externes System / Dateien | Input-Dokumente |
| Lieferantenkataloge | Externes System / Dateien | Plattenformate |
| AutoCAD / BricsCAD | Externes System | Empfängt DXF-Exporte |

---

## C4 Level 2 — Container Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                       CONTAINER DIAGRAM                                     ║
║                       Facade Planning Engine                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

 ┌─────────────────────────────────────────────────────────────────────────┐
 │                     FACADE PLANNING ENGINE                              │
 │                                                                         │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                       CLI LAYER                                  │  │
 │  │                  [Python / Click / Typer]                        │  │
 │  │                                                                  │  │
 │  │  $ facade import plan.pdf                                        │  │
 │  │  $ facade surface detect --plan <id>                             │  │
 │  │  $ facade panelize --surface <id> --catalog <id>                 │  │
 │  │  $ facade export dxf --job <id> --output plan.dxf                │  │
 │  └──────────────────────────────────────────────────────────────────┘  │
 │                              │                                          │
 │                              ▼                                          │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                   APPLICATION LAYER                              │  │
 │  │              [Use Cases / Application Services]                  │  │
 │  │                                                                  │  │
 │  │  ImportPlanUseCase    DetectSurfacesUseCase                      │  │
 │  │  PanelizeUseCase      ExportDxfUseCase                           │  │
 │  │  ManageCatalogUseCase CreateProjectUseCase                       │  │
 │  └──────────────────────────────────────────────────────────────────┘  │
 │                              │                                          │
 │                              ▼                                          │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                    DOMAIN LAYER                                  │  │
 │  │              [Entities, Value Objects, Services]                 │  │
 │  │                                                                  │  │
 │  │  FacadeSurface   Panel   PanelFormat   SupplierCatalog          │  │
 │  │  PanelizationService   ValidationService   FormatSelector       │  │
 │  └──────────────────────────────────────────────────────────────────┘  │
 │              │                    │                    │                │
 │              ▼                    ▼                    ▼                │
 │  ┌───────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
 │  │  IMPORT ADAPTER   │  │  STORAGE ADAPTER│  │  EXPORT ADAPTER     │  │
 │  │  [Infrastructure] │  │  [Infrastructure│  │  [Infrastructure]   │  │
 │  │                   │  │                 │  │                     │  │
 │  │  PDFParser        │  │  FileRepository │  │  DXFExporter        │  │
 │  │  (pdfminer/pymupdf│  │  JSONSerializer │  │  (ezdxf)            │  │
 │  │  GeometryMapper   │  │                 │  │  ReportExporter     │  │
 │  └───────────────────┘  └─────────────────┘  └─────────────────────┘  │
 │              │                    │                    │                │
 └──────────────┼────────────────────┼────────────────────┼────────────────┘
                │                    │                    │
                ▼                    ▼                    ▼
        ┌──────────────┐    ┌──────────────────┐   ┌──────────────┐
        │  PDF Files   │    │  Projekt-        │   │  DXF-Dateien │
        │  (Dateisystem│    │  Verzeichnis     │   │  Reports     │
        │  Input)      │    │  (Dateisystem)   │   │  (Dateisystem│
        └──────────────┘    └──────────────────┘   └──────────────┘
```

### Container-Beschreibungen

| Container | Technologie | Beschreibung |
|-----------|------------|-------------|
| CLI Layer | Python, Click/Typer | Kommandozeilenschnittstelle, Benutzerinteraktion, Output-Formatierung |
| Application Layer | Python | Use Cases, Orchestrierung von Domain Services und Adaptern |
| Domain Layer | Python, reines Python (keine Frameworks) | Geschäftslogik, Entitäten, Value Objects, Domain Services |
| Import Adapter | Python, pdfminer.six / pymupdf | PDF-Parsing, Geometrieextraktion, Koordinatentransformation |
| Storage Adapter | Python, json | Dateibasierte Persistenz aller Domänenobjekte |
| Export Adapter | Python, ezdxf | DXF-Erzeugung, Textreport-Erzeugung |

---

## C4 Level 3 — Component Diagram (Domain + Application)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                   COMPONENT DIAGRAM — DOMAIN & APPLICATION                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

APPLICATION LAYER
─────────────────────────────────────────────────────────────────────────────
  ┌─────────────────────┐  ┌──────────────────────┐  ┌───────────────────┐
  │  ImportPlanUseCase  │  │ DetectSurfacesUseCase│  │ ManageCatalogUC   │
  │                     │  │                      │  │                   │
  │ 1. Validate input   │  │ 1. Load plan         │  │ 1. Parse CSV/JSON │
  │ 2. Parse PDF        │  │ 2. Get geometries     │  │ 2. Validate fmts  │
  │ 3. Apply scale      │  │ 3. Detect surfaces   │  │ 3. Store catalog  │
  │ 4. Store plan       │  │ 4. Present to user   │  │                   │
  │ 5. Return plan_id   │  │ 5. Confirm/reject    │  │                   │
  └──────────┬──────────┘  └──────────┬───────────┘  └────────┬──────────┘
             │                        │                        │
             ▼                        ▼                        ▼
  ┌─────────────────────┐  ┌──────────────────────┐  ┌───────────────────┐
  │  PanelizeUseCase    │  │  ExportDxfUseCase    │  │  Shared:          │
  │                     │  │                      │  │  ProjectContext   │
  │ 1. Load surfaces    │  │ 1. Load job result   │  │  (project path,  │
  │ 2. Load catalogs    │  │ 2. Validate complete │  │   repositories)   │
  │ 3. Create job       │  │ 3. Export DXF        │  │                   │
  │ 4. Run panelization │  │ 4. Export report     │  │                   │
  │ 5. Store result     │  │ 5. Return paths      │  │                   │
  └──────────┬──────────┘  └──────────────────────┘  └───────────────────┘
             │
             ▼
DOMAIN LAYER
─────────────────────────────────────────────────────────────────────────────
  ┌─────────────────────────────────────────────────────────────────────┐
  │                    PANELIZATION SERVICE                              │
  │                                                                     │
  │  ┌─────────────────────────┐   ┌─────────────────────────────────┐ │
  │  │  GridPanelizationAlgo   │   │      FormatSelectionService     │ │
  │  │                         │   │                                 │ │
  │  │  - Generates grid       │   │  - Selects best format          │ │
  │  │  - Handles openings     │   │  - Prefers full panels          │ │
  │  │  - Applies joints       │   │  - Validates GR-001, GR-002     │ │
  │  │  - Assigns panel IDs    │   │                                 │ │
  │  └─────────────────────────┘   └─────────────────────────────────┘ │
  │                                                                     │
  │  ┌─────────────────────────┐   ┌─────────────────────────────────┐ │
  │  │  ValidationService      │   │  GeometryService                │ │
  │  │                         │   │                                 │ │
  │  │  - Validates BR rules   │   │  - Polygon operations           │ │
  │  │  - Checks overlaps      │   │  - Intersection, subtraction    │ │
  │  │  - Checks boundaries    │   │  - Area calculation             │ │
  │  │  - Emits warnings       │   │  - Coordinate transforms        │ │
  │  └─────────────────────────┘   └─────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────────────┘
  
  ┌────────────────────────┐   ┌────────────────────┐   ┌─────────────────┐
  │    FacadeSurface       │   │      Panel         │   │  PanelFormat    │
  │    (Aggregat Root)     │   │    (Entity)        │   │  (Value Object) │
  └────────────────────────┘   └────────────────────┘   └─────────────────┘

INFRASTRUCTURE LAYER (Ports & Adapters)
─────────────────────────────────────────────────────────────────────────────
  ┌────────────────────┐  ┌────────────────────┐  ┌──────────────────────┐
  │  PDFImportAdapter  │  │  FileRepository    │  │  DXFExportAdapter    │
  │  (implements:      │  │  (implements:      │  │  (implements:        │
  │  PlanImportPort)   │  │  PlanRepository,   │  │  ExportPort)         │
  │                    │  │  SurfaceRepository,│  │                      │
  │  pdfminer.six      │  │  JobRepository,    │  │  ezdxf library       │
  │  or pymupdf        │  │  CatalogRepository)│  │                      │
  └────────────────────┘  └────────────────────┘  └──────────────────────┘
```

---

## Datenflüsse

### Datenfluss 1: PDF-Import und Geometrieextraktion

```
Nutzer
  │
  │ $ facade import input.pdf --scale 1:100
  ▼
CLI Layer
  │  validiert Argumente
  ▼
ImportPlanUseCase
  │  erstellt FacadePlan-Objekt
  │
  ├──▶ PDFImportAdapter.parse(file_path)
  │         │ pdfminer extrahiert Vektordaten
  │         │ RawGeometry-Liste wird erzeugt
  │         ▼
  │    GeometryMapper.apply_scale(raw_geometries, scale)
  │         │ Koordinaten werden in mm konvertiert
  │         ▼
  │    return List[RawGeometry]
  │
  ├──▶ FileRepository.save_plan(plan)
  │         │ project/<plan_id>.json
  │         │ project/plans/<plan_id>_geometries.json
  │
  ▼
CLI: "Plan imported: <plan_id> | Pages: 1 | Geometries: 847"
```

### Datenfluss 2: Panelisierung

```
Nutzer
  │
  │ $ facade panelize --surface FA-001 FA-002 --catalog CAT-001
  ▼
CLI Layer
  │
  ▼
PanelizeUseCase
  │
  ├──▶ SurfaceRepository.load(surface_ids)
  │         │ FacadeSurface-Objekte laden
  │
  ├──▶ CatalogRepository.load(catalog_ids)
  │         │ PanelFormat-Listen laden
  │
  ├──▶ PanelizationService.panelize(surfaces, formats, config)
  │         │
  │         ├── ForEach surface:
  │         │     GridPanelizationAlgo.run(surface, formats, config)
  │         │       │
  │         │       ├── Erstelle Grid basierend auf grösstem Format
  │         │       ├── Schneide Öffnungen aus
  │         │       ├── Weise Formate zu (FormatSelectionService)
  │         │       ├── Vergebe PanelIds
  │         │       └── Prüfe Invarianten (ValidationService)
  │         │
  │         └── return PanelizationResult
  │
  ├──▶ ValidationService.validate_result(result)
  │         │ GR-001, GR-002, Überlappungen prüfen
  │         │ PlanningWarnings erzeugen
  │
  ├──▶ JobRepository.save(job)
  │
  ▼
CLI: "Panelization complete: 142 panels (98 full, 44 cut) | Warnings: 2"
```

### Datenfluss 3: DXF-Export

```
Nutzer
  │
  │ $ facade export dxf --job JOB-001 --output ./output/facade.dxf
  ▼
CLI Layer
  ▼
ExportDxfUseCase
  │
  ├──▶ JobRepository.load(job_id)
  │         │ PanelizationResult laden
  │
  ├──▶ SurfaceRepository.load(surface_ids)
  │
  ├──▶ DXFExportAdapter.export(result, surfaces, output_path)
  │         │
  │         ├── DXF-Dokument erstellen (AC1027)
  │         ├── Pro FacadeSurface: Layer anlegen
  │         ├── Pro Panel: Rectangle + Text-Label
  │         ├── Maßeinheit mm setzen
  │         └── Datei schreiben
  │
  ├──▶ ReportExporter.export(result, report_path)
  │         │ Textbericht mit Zusammenfassung
  │
  ▼
CLI: "Export complete: facade.dxf (142 panels) | Report: facade_report.txt"
```

---

## Architekturprinzipien

### Hexagonale Architektur (Ports & Adapters)

```
                    ┌─────────────────────────────────────┐
                    │           DOMÄNENKERN               │
                    │                                     │
  PDF-Files ──▶ [PDFAdapter] ──▶ [PlanImportPort]        │
  CSV-Files ──▶ [CSVAdapter] ──▶ [CatalogImportPort]     │
                    │          Domain Logic               │
                    │     [ExportPort] ──▶ [DXFAdapter] ──▶ DXF-Files
                    │     [StoragePort] ──▶ [FileAdapter] ──▶ JSON-Files
                    │                                     │
                    └─────────────────────────────────────┘
```

**Dependency Rule:** Alle Abhängigkeiten zeigen nach innen. Der Domänenkern hat keine Kenntnisse von Adaptern oder Infrastruktur.

### Dependency Injection

Application-Layer erhält Adapter-Instanzen über Konstruktor-Injektion (kein Service-Locator). Tests erhalten Mock-Implementierungen der Ports.

---

## Technologieentscheidungen (Übersicht)

| Schicht | Bibliothek | Begründung |
|---------|-----------|-----------|
| CLI | `typer` | Modernes Python CLI mit Type Hints |
| PDF-Parsing | `pdfminer.six` (primär) / `pymupdf` (fallback) | Open Source, Vektorgeometrie-Zugriff |
| Geometrie | `shapely` | Robuste 2D-Geometrieoperationen, gut getestet |
| DXF-Export | `ezdxf` | Vollständige DXF-Implementierung, aktiv gepflegt |
| Serialisierung | `pydantic` | Validierung + JSON-Serialisierung der Domänenobjekte |
| Testing | `pytest` + `pytest-cov` | Standard Python Testing |
| Code-Qualität | `ruff` + `mypy` | Schnell, modernes Tooling |

> **Detailbegründungen:** siehe [ADR-Dokumente](../adr/)

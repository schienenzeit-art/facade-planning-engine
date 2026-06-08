# Epics Overview — GitHub Structure
## Facade Planning Engine — MVP

**Version:** 1.0  
**Datum:** 2026-06-08  

---

## EPIC-001 | Project Foundation

**Beschreibung:**  
Stabiles Entwicklungsfundament etablieren: Package-Struktur, CI/CD, Qualitätsgates, Architektur-Scaffolding und ADR-002 Spike (PDF-Bibliothek). Kein Feature-Code.

**Enthaltene Features:**
- Python-Paketstruktur (src-Layout, pyproject.toml, dependency groups)
- GitHub Actions CI (lint + typecheck + test + coverage)
- Pre-commit hooks (ruff, mypy, import-linter)
- Domain Entity Stubs mit Pydantic (alle Entitäten, leere Validierung)
- Port-Interfaces (ABCs) für alle Adapter
- Typer CLI-Skeleton (alle Befehlsgruppen, "not implemented")
- Test-Infrastruktur (pytest, conftest.py, Coverage-Config)
- ADR-002 Spike: pdfminer.six vs. pymupdf Evaluation

**Abhängigkeiten:** keine

**Priorität:** Critical (Blocker für alle anderen Epics)

**Labels:** `type: chore`, `scope: mvp`, `priority: critical`

---

## EPIC-002 | PDF Geometry Extraction

**Beschreibung:**  
PDF-Dateien aus AutoCAD, Revit und ArchiCAD werden in normalisierte Domänen-Geometrieobjekte (RawGeometry) transformiert. Umfasst Generator-Erkennung, bibliotheksbasiertes Parsing, Generator-spezifische Normalisierung und Persistenz.

**Enthaltene Features:**
- PDFSourceDetector (identifiziert Generator aus PDF-Metadaten)
- PDFImportAdapter (Bibliothek-spezifisches PDF-Parsing)
- AutoCADPDFNormalizer (Koordinatensystem-Normalisierung)
- RevitPDFNormalizer (inkl. layerlos-Fallback)
- ArchiCADPDFNormalizer + GenericPDFNormalizer (mit WARNING)
- GeometryMapper (Pfade → RawGeometry Value Objects mit Layer-Attributen)
- FacadePlan + PlanPage Repository (JSON-Dateibasiert)
- CLI: `facade plan import`, `facade plan layers`, `facade plan list/show`

**Abhängigkeiten:** EPIC-001

**Priorität:** High (Kritischer Pfad)

**Labels:** `type: feature`, `domain: import`, `scope: mvp`, `priority: high`

---

## EPIC-003 | Facade Surface Detection

**Beschreibung:**  
Aus normalisierten, skalierten Geometrien werden FacadeSurfaces identifiziert. Umfasst Polygon-Erkennung, Layer-Filterung, Bestätigungs-Workflow und die FacadeZone-Entität. Öffnungs-Erkennung ist in EPIC-008 (aber Öffnungen als Holes werden hier modelliert).

**Enthaltene Features:**
- GeometryService (Shapely-basierte Polygon-Operationen)
- SurfaceDetectionService (geschlossene Polygone, Toleranz-Parameter)
- FacadeSurface Entity mit Brutto-/Nettofläche und Status-Workflow
- FacadeZone Entity + Repository
- FacadeSurface Repository (JSON-Dateibasiert)
- CLI: `facade surface detect/list/show`
- CLI: `facade surface confirm/reject` (mit `--zone` Option)
- CLI: `facade zone create/list/assign`

**Abhängigkeiten:** EPIC-001, EPIC-002, EPIC-004

**Priorität:** High (Kritischer Pfad)

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: high`

---

## EPIC-004 | Scale Calibration System

**Beschreibung:**  
Präzise Maßstabsdefinition für jeden importierten Plan. Zwei-Punkte-Kalibrierung (primär) und Direkteingabe (sekundär). Skalierungsfaktor wird auf alle Geometrien angewendet und im Audit-Trail dokumentiert.

**Enthaltene Features:**
- Scale + ScaleCalibration Value Objects
- TwoPointCalibration Use Case (p1, p2, real_distance_mm → factor)
- DirectScaleInput Use Case (1:100 → factor)
- Scale-Anwendung auf PlanPage-Geometrien
- Validierung (p1 ≠ p2, distance > 0, Warnung bei Neu-Kalibrierung)
- CLI: `facade plan scale` mit beiden Modi

**Abhängigkeiten:** EPIC-001, EPIC-002

**Priorität:** High (Kritischer Pfad, Voraussetzung für EPIC-003)

**Labels:** `type: feature`, `domain: import`, `scope: mvp`, `priority: high`

---

## EPIC-005 | Supplier Format Management

**Beschreibung:**  
Lieferantenkataloge (JSON und CSV) importieren, validieren und verwalten. Enthält Lieferantenformat-Entitäten und die Integration mit dem Rules Engine (Lieferantenregeln werden beim Import in den RuleCatalog übernommen).

**Enthaltene Features:**
- JSON-Katalog-Schema v1.0 (mit Lieferantenregeln)
- JSONCatalogAdapter (Import + JSON-Schema-Validierung)
- CSVCatalogAdapter (Import + Spalten-Validierung)
- SupplierCatalog + PanelFormat Entities
- Lieferantenregel-Extraktion → projektweiter RuleCatalog
- Catalog-Repository (JSON-Dateibasiert)
- CLI: `facade catalog import/list/show`

**Abhängigkeiten:** EPIC-001, EPIC-009 (RuleCatalog muss existieren)

**Priorität:** High (Voraussetzung für EPIC-006)

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: high`

---

## EPIC-006 | Panelization Engine (Core)

**Beschreibung:**  
Das Herzstück des Systems. Grid-basierte Panelisierung mit JointConfig, Bewegungsfugen, Öffnungsausschluss und Rules Engine Integration. Umfasst Strategy-Pattern für Algorithmen und vollständiges Job-/Result-Management.

**Enthaltene Features:**
- BasePanelizationAlgorithm ABC (Strategy Pattern)
- PanelizationConfig mit vollständiger JointConfig
- FormatSelectionService (GR-001, GR-002, bevorzugt Vollplatten)
- GridPanelizationAlgorithm (Basis-Rechteck-Coverage)
- JointConfig-Integration (horizontale + vertikale Fugen)
- Bewegungsfugen-Logik (GR-008, konfigurierbar)
- OpeningExclusionHandler (TRIM + DROP, GR-007)
- PanelizationError-Handling (PE-001..PE-004, Fail-Per-Surface)
- PanelizationService (orchestriert Algo + RuleEngine)
- PanelizationJob + PanelizationResult + Repository
- FacadeZone-basierte Panelisierung mit Config-Override
- CLI: `facade panelize run/list/show`

**Abhängigkeiten:** EPIC-003, EPIC-005, EPIC-008, EPIC-009

**Priorität:** Critical (Kern-MVP-Feature)

**Labels:** `type: feature`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: critical`

---

## EPIC-007 | DXF Export System

**Beschreibung:**  
PanelizationResult wird als valides DXF-Dokument (AC1027) exportiert, das in AutoCAD 2013+ und BricsCAD direkt verwendbar ist. Layer-Struktur, LWPOLYLINE-Panels, MTEXT-Labels und korrekte mm-Einheit.

**Enthaltene Features:**
- DXF-Dokument-Grundstruktur (AC1027, INSUNITS=4)
- Layer-Struktur pro FacadeSurface (PANELS, BOUNDARY, OPENINGS, LABELS)
- Panel-Rechtecke als LWPOLYLINE
- Panel-IDs als MTEXT (Unicode-sicher)
- Flächen-Boundaries + Öffnungen als LWPOLYLINE
- DXFExportAdapter (implementiert ExportPort)
- CLI: `facade export dxf --job <id> --output <path>`

**Abhängigkeiten:** EPIC-006

**Priorität:** High (MVP-Output)

**Labels:** `type: feature`, `domain: export`, `scope: mvp`, `priority: high`

---

## EPIC-008 | Opening Handling System

**Beschreibung:**  
Vollständige Öffnungsbehandlung: Erkennung von Öffnungen (Fenster, Türen, Lüftung) als Holes in FacadeSurfaces, und Ausschluss aus der Panelisierung. Enthält TRIM und DROP Strategien sowie GR-006/GR-007.

**Enthaltene Features:**
- Opening Entity (Typ-Enum: WINDOW, DOOR, VENT, OTHER)
- Opening-Detection-Algorithmus (Polygon-in-Polygon, Toleranz)
- TRIM-Strategie (Panel wird an Öffnungsrand zugeschnitten)
- DROP-Strategie (Panel wird entfernt wenn Öffnung überlappt)
- GR-006: Mindestrandabstand Panel zu Öffnung
- GR-007: Mindestpanelgrösse nach Öffnungsschnitt
- Opening-Visualisierung im DXF (eigener Layer)

**Abhängigkeiten:** EPIC-003, EPIC-009

**Priorität:** High (Fachlich zwingend)

**Labels:** `type: feature`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: high`

---

## EPIC-009 | Rule Engine / Rules Catalog

**Beschreibung:**  
Eigenständige Rules-Engine-Teildomäne. RuleDefinition (konfigurierbar), RuleCatalog (projekt-weit), RuleEngine (Domain Service), alle Builtin-Regeln GR-001..GR-010, Lieferantenregel-Import und CLI-Verwaltung.

**Enthaltene Features:**
- RuleDefinition Value Object (id, severity, category, parameters, is_active)
- RuleCatalog Entity + Repository
- RuleViolation Value Object (mit suggestion)
- RuleEngine Domain Service (evaluate panel/surface/result)
- Builtin Rules GR-001..GR-005 (Geometrie + Format)
- Builtin Rules GR-006..GR-010 (Technical + Joint)
- Supplier Rule Import Integration (mit EPIC-005)
- CLI: `facade rules list/disable/configure`

**Abhängigkeiten:** EPIC-001 (Grundstruktur; kann sehr früh parallel entwickelt werden)

**Priorität:** High (Voraussetzung für EPIC-006)

**Labels:** `type: feature`, `domain: planning`, `rules`, `scope: mvp`, `priority: high`

---

## EPIC-010 | Audit & Traceability System

**Beschreibung:**  
Vollständiger Audit-Trail für jede Panelisierungsoperation. Audit-JSON mit config_snapshot, scale_calibration, format_selection_log und rule_violations. Prozessreport als menschenlesbarer Text.

**Enthaltene Features:**
- AuditLogger Service (append-only JSONL pro Job)
- Vollständiges Audit-JSON (Schema v1.0 aus GAP-010)
- Config-Snapshot (alle PanelizationConfig-Parameter)
- ScaleCalibration-Eintrag im Audit
- FormatSelection-Log pro Panel (konfigurierbar on/off)
- RuleViolation-Log im Audit
- ProcessReport Textexporter
- CLI: `facade export report --job <id>`

**Abhängigkeiten:** EPIC-004, EPIC-006, EPIC-009

**Priorität:** Medium-High (Nachvollziehbarkeit ist SHOULD-Anforderung)

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: medium`

---

## Epic-Dependency-Graph

```
EPIC-001 (Foundation)
    │
    ├──▶ EPIC-002 (PDF Extraction)
    │         │
    │         └──▶ EPIC-004 (Scale)
    │                   │
    │                   └──▶ EPIC-003 (Surface Detection)
    │                              │
    ├──▶ EPIC-009 (Rules Engine)   │
    │         │                    │
    │         └──▶ EPIC-005 (Supplier) ──▶ EPIC-006 (Panelization) ──▶ EPIC-007 (DXF Export)
    │                                           ▲                           │
    └──▶ EPIC-008 (Openings) ──────────────────┘                           │
                                                                            ▼
                                                                      EPIC-010 (Audit)
```

## Parallelisierungsmöglichkeiten

| Parallelgruppe | Epics | Bedingung |
|----------------|-------|-----------|
| Gruppe A | EPIC-001 allein | Start sofort |
| Gruppe B | EPIC-002 + EPIC-009 | Nach EPIC-001 |
| Gruppe C | EPIC-004 + EPIC-008 | Nach EPIC-002 |
| Gruppe D | EPIC-003 + EPIC-005 | Nach EPIC-004 |
| Gruppe E | EPIC-006 | Nach EPIC-003, EPIC-005, EPIC-008, EPIC-009 |
| Gruppe F | EPIC-007 + EPIC-010 | Nach EPIC-006 |

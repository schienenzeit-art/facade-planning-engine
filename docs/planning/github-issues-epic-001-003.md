# GitHub Issues — EPIC-001 bis EPIC-003
## Facade Planning Engine

**Format:** Direkt in GitHub Issues übertragbar.  
**Konvention:** Alle Acceptance Criteria sind mit `pytest` oder manueller CLI-Prüfung testbar.

---

# EPIC-001: Project Foundation

---

## ISSUE-001 | Set up Python package structure with src-layout

**Labels:** `type: chore`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 0  
**Story Points:** 2

**Beschreibung:**  
Das Python-Paket `facade_engine` wird mit src-Layout, pyproject.toml und allen Abhängigkeitsgruppen eingerichtet. Keine Business-Logik — nur Paket-Infrastruktur.

**Acceptance Criteria:**
- [ ] `pip install -e ".[dev]"` läuft ohne Fehler auf Python 3.11+
- [ ] `facade --version` gibt eine Versionsnummer aus (z.B. 0.0.1-dev)
- [ ] Paketstruktur entspricht exakt [docs/modules/module-structure.md](../modules/module-structure.md)
- [ ] `pyproject.toml` definiert prod + dev dependency groups
- [ ] `.python-version` Datei mit 3.11 ist vorhanden

**Subtasks:**
- [ ] `pyproject.toml` erstellen mit `[project]`, `[project.optional-dependencies]`, `[tool.ruff]`, `[tool.mypy]`
- [ ] `src/facade_engine/__init__.py` + `src/facade_engine/cli/main.py` (stub)
- [ ] Alle Unterverzeichnisse aus Modulstruktur als leere `__init__.py`
- [ ] `requirements/prod.txt` + `requirements/dev.txt` ableiten
- [ ] Smoke-Test: `python -c "import facade_engine; print(facade_engine.__version__)"`

---

## ISSUE-002 | Configure GitHub Actions CI pipeline

**Labels:** `type: chore`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 0  
**Story Points:** 3

**Beschreibung:**  
GitHub Actions Workflow für Lint, Typecheck, Tests und Coverage-Report. Läuft auf push und pull_request auf develop und main. Matrix: ubuntu, windows, macos.

**Acceptance Criteria:**
- [ ] CI läuft bei jedem Push auf develop und bei jedem PR auf main
- [ ] Jobs: `lint` (ruff check + ruff format --check), `typecheck` (mypy src/), `test` (pytest + coverage)
- [ ] PR auf main kann nur gemergt werden wenn alle Jobs grün
- [ ] Coverage-Report wird als Artifact hochgeladen
- [ ] Matrix: ubuntu-latest (Pflicht) + windows-latest + macos-latest (SHOULD)

**Subtasks:**
- [ ] `.github/workflows/ci.yml` erstellen
- [ ] `ruff`-Job mit `ruff check src/ tests/` + `ruff format --check src/ tests/`
- [ ] `mypy`-Job mit `mypy src/facade_engine --ignore-missing-imports`
- [ ] `pytest`-Job mit `pytest tests/ --cov=facade_engine --cov-fail-under=0` (threshold wird erhöht)
- [ ] Branch-Schutzregeln in GitHub Repository-Settings dokumentieren (README-Hinweis)

---

## ISSUE-003 | Configure pre-commit hooks (ruff, mypy, import-linter)

**Labels:** `type: chore`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 0  
**Story Points:** 2

**Beschreibung:**  
Pre-commit-Hooks erzwingen Code-Qualität und Architektur-Grenzen lokal vor jedem Commit. Import-linter verhindert Dependency-Rule-Verletzungen (Domain darf nicht Infrastructure importieren).

**Acceptance Criteria:**
- [ ] `pre-commit install` richtet alle Hooks ein
- [ ] Commit schlägt fehl wenn ruff-Fehler vorhanden
- [ ] Commit schlägt fehl wenn mypy-Fehler vorhanden
- [ ] Commit schlägt fehl wenn import-linter Domain→Infrastructure-Import erkennt
- [ ] `pre-commit run --all-files` läuft auf leerem Projekt durch

**Subtasks:**
- [ ] `.pre-commit-config.yaml` erstellen mit ruff, mypy, import-linter
- [ ] `.importlinter` Konfiguration: Contracts für Domain→Infrastructure und Application→Infrastructure
- [ ] `pre-commit` in dev-dependencies aufnehmen
- [ ] CONTRIBUTING.md: Einrichtungsanleitung `pre-commit install`
- [ ] Test: Commit mit `from facade_engine.infrastructure import x` in domain/ → Fehler erwartet

---

## ISSUE-004 | Implement domain entity stubs with Pydantic validation

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 0  
**Story Points:** 5

**Beschreibung:**  
Alle Domänen-Entitäten und Value Objects aus dem Domänenmodell als Pydantic-Modelle implementieren — mit vollständiger Feldvalidierung, aber ohne Business-Logik. Dies ist das Schema-Fundament für alle anderen Epics.

**Acceptance Criteria:**
- [ ] Alle Entitäten aus [docs/domain/domain-model.md](../domain/domain-model.md) als Pydantic-Klassen vorhanden
- [ ] Feldvalidierung funktioniert: `PanelFormat(width_mm=0)` wirft `ValidationError`
- [ ] `FacadeSurfaceId("FA-001")` akzeptiert; `FacadeSurfaceId("X")` wirft Fehler
- [ ] `PanelId("PA-001-042")` akzeptiert; `PanelId("invalid")` wirft Fehler
- [ ] `Scale(numerator=1, denominator=0)` wirft Fehler
- [ ] mypy hat 0 Fehler auf allen Entities

**Subtasks:**
- [ ] Value Objects: `Scale`, `Point2D`, `Polygon`, `BoundingBox`, `PanelId`, `FacadeSurfaceId`, `FacadeZoneId`, `RuleId`, `JointConfig`, `ScaleCalibration`
- [ ] Entitäten: `FacadePlan`, `PlanPage`, `FacadeSurface`, `Opening`, `FacadeZone`, `Panel`, `SupplierCatalog`, `PanelFormat`
- [ ] Rules-Entitäten: `RuleDefinition`, `RuleCatalog`, `RuleViolation`, `PanelizationError`
- [ ] Job-Entitäten: `PanelizationJob`, `PanelizationConfig`, `PanelizationResult`
- [ ] Enumerationen: `FileType`, `SurfaceStatus`, `JobStatus`, `Orientation`, `CutReason`, `RuleSeverity`, `RuleCategory`, `PanelizationErrorType`, `OpeningType`

---

## ISSUE-005 | Implement port interfaces (ABCs) for all adapters

**Labels:** `type: chore`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 0  
**Story Points:** 2

**Beschreibung:**  
Alle Port-Interfaces (abstrakte Basisklassen) aus `application/ports/` definieren. Diese Interfaces sind die Verträge zwischen Application-Layer und Infrastructure-Adaptern.

**Acceptance Criteria:**
- [ ] Alle Ports sind `ABC`-Klassen mit `@abstractmethod` Signaturen
- [ ] `PlanImportPort`, `CatalogImportPort`, `ExportPort` vorhanden
- [ ] Repository-Ports: `FacadePlanRepository`, `FacadeSurfaceRepository`, `FacadeZoneRepository`, `SupplierCatalogRepository`, `PanelizationJobRepository`, `RuleCatalogRepository`
- [ ] Import-linter bestätigt: Ports haben keine Infrastructure-Imports
- [ ] mypy hat 0 Fehler auf allen Port-Definitionen

**Subtasks:**
- [ ] `application/ports/plan_import_port.py` — `parse(path: Path) -> List[RawGeometry]`
- [ ] `application/ports/catalog_import_port.py` — `import_catalog(path: Path) -> SupplierCatalog`
- [ ] `application/ports/export_port.py` — `export_dxf(result: PanelizationResult, path: Path) -> None`
- [ ] `application/ports/repository_ports.py` — alle Repository-ABCs
- [ ] Alle Ports mit vollständigen Type-Hints und Docstrings

---

## ISSUE-006 | Create Typer CLI skeleton with all command groups

**Labels:** `type: feature`, `domain: cli`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 0  
**Story Points:** 3

**Beschreibung:**  
Das CLI-Gerüst mit allen Befehlsgruppen aus der MVP-Definition einrichten. Alle Befehle geben "not yet implemented" zurück. Exit-Codes sind standardkonform (0=Erfolg, 1+=Fehler).

**Acceptance Criteria:**
- [ ] `facade --help` zeigt alle Befehlsgruppen: project, plan, surface, zone, catalog, rules, panelize, export
- [ ] Jede Befehlsgruppe hat `--help` mit Beschreibung
- [ ] Jeder Befehl gibt aktuell `NotImplementedError`-ähnliche Meldung aus (nicht Stack Trace)
- [ ] `facade plan import nonexistent.pdf` gibt Exit-Code 1
- [ ] `facade --version` gibt Version aus

**Subtasks:**
- [ ] `cli/main.py` — Typer-App mit allen Befehlsgruppen als Sub-Apps
- [ ] `cli/commands/project.py`, `plan.py`, `surface.py`, `zone.py`, `catalog.py`, `rules.py`, `panelize.py`, `export.py`
- [ ] `cli/formatters.py` — Tabellen-Helper (Rich-Tabellen für Listen-Ausgaben)
- [ ] `cli/error_handler.py` — zentraler Fehler-Handler (Exception → benutzerfreundliche Meldung + Exit-Code 1)
- [ ] Eintrag in `pyproject.toml`: `[project.scripts] facade = "facade_engine.cli.main:app"`

---

## ISSUE-007 | Set up test infrastructure and sample fixtures

**Labels:** `type: test`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 0  
**Story Points:** 3

**Beschreibung:**  
Test-Infrastruktur aufsetzen: conftest.py mit Fixtures, Verzeichnisstruktur für Tests, initiale Testdaten. Die Fixtures `simple_facade.pdf` und `supplier_a.json` werden erstellt/beschafft.

**Acceptance Criteria:**
- [ ] `pytest tests/unit/` läuft ohne Fehler (0 Tests = 0 Failures)
- [ ] `conftest.py` enthält Fixtures: `tmp_project_dir`, `simple_facade_pdf_path`, `supplier_a_catalog_path`
- [ ] `fixtures/pdf/simple_facade.pdf` ist eine valide vektorbasierte AutoCAD-PDF (bekannte Geometrie)
- [ ] `fixtures/catalogs/supplier_a.json` enthält mind. 3 Formate + mind. 1 Lieferantenregel
- [ ] `fixtures/README.md` beschreibt alle Testdaten mit exakten Maßen

**Subtasks:**
- [ ] `tests/conftest.py` mit projektweiten pytest-Fixtures
- [ ] `tests/unit/`, `tests/integration/`, `tests/e2e/` Verzeichnisstruktur
- [ ] `fixtures/pdf/simple_facade.pdf` erstellen (Rechteck 6000×3000mm, Maßstab 1:100)
- [ ] `fixtures/catalogs/supplier_a.json` erstellen (Swisspearl-ähnliches Format)
- [ ] `fixtures/catalogs/supplier_b.csv` erstellen
- [ ] `fixtures/README.md` mit exakten bekannten Maßen aller Testdaten

---

## ISSUE-008 | ADR-002 Spike: PDF library evaluation (pdfminer.six vs pymupdf)

**Labels:** `type: spike`, `domain: import`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 0  
**Story Points:** 5

**Beschreibung:**  
Technischer Spike zur Entscheidung der PDF-Bibliothek. Beide Bibliotheken werden auf identischen Testdaten evaluiert. Ergebnis: aktualisiertes ADR-002 mit Status "Accepted".

**Acceptance Criteria:**
- [ ] Beide Bibliotheken installiert und auf `fixtures/pdf/simple_facade.pdf` getestet
- [ ] Koordinatengenauigkeit gemessen: Abweichung in mm dokumentiert
- [ ] Performance gemessen: Import-Zeit für simple_facade.pdf
- [ ] Lizenzfrage für pymupdf geklärt (kommerziell oder nur Open Source?)
- [ ] ADR-002 Status wird auf "Accepted" gesetzt mit Begründung
- [ ] Entscheidung: Eine Bibliothek ist als primär definiert

**Subtasks:**
- [ ] `spike/pdf_library_comparison.py` Testskript (in Branch, nicht in main)
- [ ] Bibliothek A (pdfminer.six): Pfade/Koordinaten aus simple_facade.pdf extrahieren
- [ ] Bibliothek B (pymupdf): Pfade/Koordinaten aus simple_facade.pdf extrahieren
- [ ] Koordinatenvergleich: beide Bibliotheken vs. bekannte Referenzkoordinaten
- [ ] Performance-Test: Laufzeit beide Bibliotheken auf simple_facade.pdf
- [ ] Ergebnis in ADR-002 dokumentieren; ADR-002 Status → Accepted

---

# EPIC-002: PDF Geometry Extraction

---

## ISSUE-011 | Implement PDFSourceDetector

**Labels:** `type: feature`, `domain: import`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 3

**Beschreibung:**  
PDFSourceDetector liest PDF-Metadaten (/Producer, /Creator, /Application) und identifiziert den Generator (AUTOCAD, REVIT, ARCHICAD, UNKNOWN). Gibt WARNING bei unbekanntem Generator.

**Acceptance Criteria:**
- [ ] AutoCAD-PDF → `PDFGenerator.AUTOCAD`
- [ ] Revit-PDF → `PDFGenerator.REVIT`
- [ ] ArchiCAD-PDF → `PDFGenerator.ARCHICAD`
- [ ] Unbekannte PDF → `PDFGenerator.UNKNOWN` + WARNING im Log
- [ ] Leere PDF-Metadaten → `PDFGenerator.UNKNOWN` (kein Fehler)
- [ ] Unit-Tests für alle 4 Fälle

**Subtasks:**
- [ ] `PDFGenerator` Enum in `domain/value_objects/`
- [ ] `PDFSourceDetector` in `infrastructure/pdf/pdf_source_detector.py`
- [ ] Metadaten-Parsing: `/Producer`, `/Creator`, `/Application` Felder
- [ ] Heuristiken: "Autodesk" → AUTOCAD; "Revit" → REVIT; "ArchiCAD" → ARCHICAD
- [ ] Unit-Tests mit gemockten PDF-Metadaten

---

## ISSUE-012 | Implement PDFImportAdapter with chosen library

**Labels:** `type: feature`, `domain: import`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 1  
**Story Points:** 8

**Beschreibung:**  
PDFImportAdapter implementiert `PlanImportPort` und extrahiert Pfad-Geometrien (Linien, Polylines, Polygone) aus PDF-Seiten via der in ADR-002 gewählten Bibliothek.

**Acceptance Criteria:**
- [ ] Implementiert `PlanImportPort` vollständig
- [ ] Extrahiert Linien, Polylines und geschlossene Polygone aus simple_facade.pdf
- [ ] Layer-Attribut wird für jede Geometrie gespeichert
- [ ] Rasterbild-PDFs werfen `UnsupportedPDFError` mit klarer Meldung
- [ ] Mehrseitige PDFs: alle Seiten werden extrahiert
- [ ] Performance: simple_facade.pdf (< 2.000 Geometrien) in < 5 Sekunden

**Subtasks:**
- [ ] `infrastructure/pdf/pdf_import_adapter.py` — implementiert `PlanImportPort`
- [ ] `infrastructure/pdf/pdfminer_parser.py` ODER `infrastructure/pdf/pymupdf_parser.py` (nach ADR-002)
- [ ] Rasterbilderkennung: wenn keine Vektordaten gefunden → `UnsupportedPDFError`
- [ ] Pfad-Rekonstruktion: Segmente zu Polylines/Polygonen zusammensetzen
- [ ] Integration-Test mit `fixtures/pdf/simple_facade.pdf`

---

## ISSUE-013 | Implement AutoCADPDFNormalizer

**Labels:** `type: feature`, `domain: import`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 5

**Beschreibung:**  
AutoCADPDFNormalizer transformiert AutoCAD-spezifische Koordinatensysteme in das Domänen-Koordinatensystem. Filtert Schriftfeld-Layer (TITLEBLK, BORDER) heraus.

**Acceptance Criteria:**
- [ ] AutoCAD-PDF mit bekannten Koordinaten → normalisierte Koordinaten ±1mm korrekt
- [ ] Schriftfeld-Geometrien (Layer "TITLEBLK" oder "BORDER") werden gefiltert
- [ ] Koordinatentransformation ist invertierbar (kein Informationsverlust)
- [ ] Unit-Tests mit synthetischen AutoCAD-Koordinaten
- [ ] Integration-Test mit `fixtures/pdf/autocad_facade_simple.pdf`

**Subtasks:**
- [ ] `PDFNormalizerStrategy` ABC in `infrastructure/pdf/normalizer_base.py`
- [ ] `AutoCADPDFNormalizer` in `infrastructure/pdf/autocad_normalizer.py`
- [ ] Koordinatentransformation: PDF-Seitenkoordinaten → lokales 2D-System (Ursprung links unten)
- [ ] Layer-Filter: konfigurierbare Liste auszuschliessender Layer
- [ ] Unit-Tests: 10+ Koordinatentransformationen mit Expected-Output

---

## ISSUE-014 | Implement RevitPDFNormalizer and ArchiCADPDFNormalizer

**Labels:** `type: feature`, `domain: import`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 5

**Beschreibung:**  
RevitPDFNormalizer (inkl. Fallback für layerlose Revit-PDFs) und ArchiCADPDFNormalizer. GenericPDFNormalizer für unbekannte Generatoren mit WARNING.

**Acceptance Criteria:**
- [ ] Revit-PDF (mit Layern) → korrekte Koordinaten
- [ ] Revit-PDF (ohne Layer) → WARNING + Best-Effort-Geometrie (alle Geometrien auf "DEFAULT")
- [ ] ArchiCAD-PDF → korrekte Koordinaten
- [ ] GenericPDFNormalizer → WARNING: "Generator unbekannt, Qualität nicht garantiert"
- [ ] Integration-Tests für alle 3 Generatoren mit Fixtures

**Subtasks:**
- [ ] `RevitPDFNormalizer` in `infrastructure/pdf/revit_normalizer.py`
- [ ] Revit layerlos-Fallback: Farb-/Linientyp-basierte Pseudo-Layer ("DEFAULT", "THIN", "THICK")
- [ ] `ArchiCADPDFNormalizer` in `infrastructure/pdf/archicad_normalizer.py`
- [ ] `GenericPDFNormalizer` in `infrastructure/pdf/generic_normalizer.py`
- [ ] Normalizer-Factory in `infrastructure/pdf/normalizer_factory.py` (wählt Normalizer anhand PDFGenerator)

---

## ISSUE-015 | Implement GeometryMapper

**Labels:** `type: feature`, `domain: import`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 5

**Beschreibung:**  
GeometryMapper transformiert normalisierte Pfad-Rohdaten in typisierte `RawGeometry` Value Objects der Domäne. Bestimmt Geometrietyp (LINE, POLYLINE, POLYGON) und setzt Layer-Attribut.

**Acceptance Criteria:**
- [ ] Geschlossene Pfade → `RawGeometry(geometry_type=POLYGON, is_closed=True)`
- [ ] Offene Mehrpunkt-Pfade → `RawGeometry(geometry_type=POLYLINE, is_closed=False)`
- [ ] Zweipunkt-Pfade → `RawGeometry(geometry_type=LINE)`
- [ ] `layer`-Attribut ist gesetzt (oder "DEFAULT" wenn kein Layer)
- [ ] Unit-Tests für alle Geometrietypen

**Subtasks:**
- [ ] `RawGeometry` Value Object in `domain/value_objects/raw_geometry.py`
- [ ] `GeometryMapper` in `infrastructure/pdf/geometry_mapper.py`
- [ ] Polygon-Schliessen-Heuristik: Endpunkt ≈ Startpunkt (Toleranz: 0.5mm) → automatisch schliessen
- [ ] Degenerierte Geometrien filtern: Polygone mit < 3 Punkten werden verworfen
- [ ] Unit-Tests: 15+ Geometrie-Mapping-Fälle

---

## ISSUE-016 | Implement FacadePlan and PlanPage repository

**Labels:** `type: feature`, `domain: infrastructure`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 3

**Beschreibung:**  
Dateibasiertes Repository für FacadePlan und PlanPage. Speichert Plan-Metadaten und Geometrien in separaten JSON-Dateien (Geometrien können gross werden).

**Acceptance Criteria:**
- [ ] `FacadePlanRepository.save(plan)` → schreibt `<project>/plans/<plan_id>.json`
- [ ] `FacadePlanRepository.load(plan_id)` → lädt identisches Objekt
- [ ] Geometrien werden in `<project>/plans/<plan_id>_geometries.json` gespeichert (getrennt für Performance)
- [ ] `FacadePlanRepository.list_all()` → gibt alle Plan-IDs zurück
- [ ] `schema_version: "1.0"` in allen Dateien
- [ ] Integration-Tests: save + load + verify identity

**Subtasks:**
- [ ] `FileRepository` Basisklasse in `infrastructure/persistence/file_repository.py`
- [ ] `FacadePlanFileRepository` in `infrastructure/persistence/plan_repository.py`
- [ ] `ProjectContext` in `infrastructure/persistence/project_context.py` (verwaltet Projektpfade)
- [ ] JSON-Serialisierung via Pydantic `.model_dump_json()` + `.model_validate_json()`
- [ ] Integration-Tests: roundtrip save→load für FacadePlan mit 1000 Geometrien

---

## ISSUE-017 | Implement CLI commands: facade plan import and facade plan layers

**Labels:** `type: feature`, `domain: cli`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 3

**Beschreibung:**  
CLI-Befehle für PDF-Import und Layer-Listing. `facade plan import` orchestriert PDFSourceDetector, PDFImportAdapter, GeometryMapper und Repository. `facade plan layers` zeigt Layer-Statistik.

**Acceptance Criteria:**
- [ ] `facade plan import simple_facade.pdf --scale 1:100` → Plan-ID + Statistik in Tabellenform
- [ ] `facade plan import nonexistent.pdf` → Exit-Code 1 + klare Fehlermeldung (kein Stack Trace)
- [ ] `facade plan import raster.pdf` → Exit-Code 1 + "Datei enthält keine Vektordaten"
- [ ] `facade plan layers <plan-id>` → Tabelle: Layer, Geometrie-Anzahl, Typ-Verteilung
- [ ] `--help` für beide Befehle zeigt vollständige Beschreibung + Parameter

**Subtasks:**
- [ ] `ImportPlanUseCase` in `application/use_cases/import_plan.py`
- [ ] CLI-Befehl `facade plan import` in `cli/commands/plan.py`
- [ ] CLI-Befehl `facade plan layers` in `cli/commands/plan.py`
- [ ] Rich-Tabellenausgabe für Geometrie-Statistik
- [ ] Fehlerbehandlung in `cli/error_handler.py`: UnsupportedPDFError → benutzerfreundliche Meldung

---

## ISSUE-018 | Implement CLI commands: facade plan list and facade plan show

**Labels:** `type: feature`, `domain: cli`, `scope: mvp`, `priority: medium`  
**Milestone:** Sprint 1  
**Story Points:** 2

**Beschreibung:**  
Listenansicht aller importierten Pläne und Detailansicht eines einzelnen Plans.

**Acceptance Criteria:**
- [ ] `facade plan list` → Tabelle: ID, Dateiname, Generator, Seiten, Geometrien, Datum
- [ ] `facade plan show <id>` → Detailansicht: alle Felder, Scale-Status, Seiten-Liste
- [ ] `facade plan show nonexistent-id` → Exit-Code 1 + "Plan nicht gefunden: <id>"
- [ ] Leeres Projekt: `facade plan list` → "Keine Pläne vorhanden" (kein Fehler, Exit-Code 0)

**Subtasks:**
- [ ] `ListPlansUseCase` + `GetPlanUseCase` in `application/use_cases/`
- [ ] CLI-Befehle in `cli/commands/plan.py`
- [ ] Rich-Panel für Detailansicht (Box-Format)
- [ ] E2E-Test: import → list → show Workflow

---

## ISSUE-019 | Write integration tests for PDF import (all 3 generators)

**Labels:** `type: test`, `domain: import`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 5

**Beschreibung:**  
Integration-Tests für PDF-Import mit echten PDF-Dateien aller 3 unterstützten Generatoren. Prüft Koordinatengenauigkeit, Layer-Erkennung und Performance.

**Acceptance Criteria:**
- [ ] `test_import_autocad_pdf`: Geometrien korrekt, Koordinaten ±1mm
- [ ] `test_import_revit_pdf`: Geometrien korrekt (inkl. layerlos-Test)
- [ ] `test_import_archicad_pdf`: Geometrien korrekt
- [ ] `test_import_raster_pdf`: UnsupportedPDFError wird ausgelöst
- [ ] `test_import_performance`: simple_facade.pdf (< 2.000 Geometrien) in < 5 Sekunden

**Subtasks:**
- [ ] `tests/integration/test_pdf_import.py` erstellen
- [ ] Fixture `fixtures/pdf/autocad_facade_simple.pdf` (bekannte Geometrien)
- [ ] Fixture `fixtures/pdf/revit_facade_simple.pdf`
- [ ] Fixture `fixtures/pdf/archicad_facade_simple.pdf`
- [ ] Fixture `fixtures/pdf/raster_scan.pdf` (für Negativ-Test)

---

# EPIC-003: Facade Surface Detection

---

## ISSUE-021 | Implement GeometryService with Shapely operations

**Labels:** `type: feature`, `domain: planning`, `geometry`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 5

**Beschreibung:**  
GeometryService kapselt alle Shapely-Operationen. Domänen-Polygone werden intern in Shapely-Objekte konvertiert. Service ist der einzige Ort im System wo Shapely direkt verwendet wird.

**Acceptance Criteria:**
- [ ] `area(polygon) -> float` — korrekt in mm²
- [ ] `contains(outer, inner) -> bool` — korrekt für Punkt-in-Polygon und Polygon-in-Polygon
- [ ] `difference(polygon, hole) -> Polygon` — Öffnung aus Fläche ausschneiden
- [ ] `intersects(a, b) -> bool` — Überlappungsprüfung
- [ ] `close_polygon(points, tolerance_mm) -> Polygon` — schliesst Lücken bis tolerance_mm
- [ ] Shapely-Imports nur in `geometry_service.py` (import-linter prüft das)
- [ ] Unit-Tests: 20+ Geometrieoperationen mit bekannten Expected-Values

**Subtasks:**
- [ ] `domain/services/geometry_service.py` implementieren
- [ ] Private `_to_shapely(polygon: Polygon) -> ShapelyPolygon` Hilfsfunktion
- [ ] Private `_from_shapely(shape: ShapelyPolygon) -> Polygon` Hilfsfunktion
- [ ] `close_polygon`: iterativ Punkte verbinden bis Lücke ≤ tolerance_mm
- [ ] Unit-Tests: Fläche Rechteck, Fläche mit Loch, Überlappung, Enthaltensein

---

## ISSUE-022 | Implement SurfaceDetectionService

**Labels:** `type: feature`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 8

**Beschreibung:**  
SurfaceDetectionService analysiert RawGeometries einer PlanPage und erzeugt FacadeSurface-Kandidaten aus geschlossenen Polygonen. Unterstützt Layer-Filter. Vergibt FacadeSurfaceIds (FA-001, FA-002, ...).

**Acceptance Criteria:**
- [ ] Alle geschlossenen Polygone auf gewähltem Layer → FacadeSurface-Kandidaten
- [ ] FacadeSurface-IDs sind sequenziell (FA-001, FA-002, ...) und innerhalb des Projekts eindeutig
- [ ] Duplikate (identische Boundaries) werden dedupliziert
- [ ] Polygone mit < Mindestfläche (konfigurierbar, default 10.000 mm² = 100×100mm) werden gefiltert
- [ ] Layer-Filter: wenn `layer_filter` übergeben, nur Geometrien dieses Layers
- [ ] Unit-Tests: 3 Flächen in einfachem Plan korrekt erkannt

**Subtasks:**
- [ ] `domain/services/surface_detection_service.py`
- [ ] FacadeSurfaceId-Generator: `FacadeSurfaceIdGenerator` (counter-basiert, projekt-weit)
- [ ] Mindestflächen-Filter: Polygon.area < min_surface_area_mm2 → REJECTED (mit Warnung)
- [ ] Duplikat-Erkennung: Boundary-Hash-Vergleich
- [ ] Integration-Test: `simple_facade.pdf` → mind. 1 FacadeSurface erkannt

---

## ISSUE-023 | Implement Opening detection algorithm

**Labels:** `type: feature`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 8

**Beschreibung:**  
Öffnungen (Fenster, Türen, etc.) werden als Polygone erkannt, die vollständig innerhalb einer FacadeSurface-Boundary liegen. Sie werden als `Opening`-Objekte der Surface zugeordnet.

**Acceptance Criteria:**
- [ ] Polygon vollständig innerhalb Surface-Boundary → `Opening` mit `surface_id`
- [ ] Polygon teilweise ausserhalb → kein Opening (Warnung: "Teilweise ausserhalb Boundary")
- [ ] Öffnung, die Öffnung enthält → nur äussere Öffnung (keine Hierarchie im MVP)
- [ ] `FacadeSurface.openings` enthält korrekte Opening-Liste
- [ ] `FacadeSurface.net_area_mm2` = gross_area − sum(opening.area) korrekt
- [ ] Unit-Tests: Surface mit 3 Fenstern, korrekte Nettofläche

**Subtasks:**
- [ ] Opening-Detection in `SurfaceDetectionService.detect_openings(surface, geometries)`
- [ ] Enthaltensein-Prüfung via `GeometryService.contains(surface.boundary, candidate)`
- [ ] Öffnungstyp-Heuristik: gross Polygon → OTHER; kleines Polygon → WINDOW (konfigurierbar)
- [ ] Nettoflächen-Berechnung in `FacadeSurface` als computed property
- [ ] Unit-Tests mit `fixtures/pdf/facade_with_windows.pdf`

---

## ISSUE-024 | Implement FacadeZone entity and repository

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: medium`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
FacadeZone als organisatorisches Konstrukt implementieren. Enthält Referenzen auf FacadeSurfaces (keine eigene Geometrie). Repository für JSON-Persistenz.

**Acceptance Criteria:**
- [ ] `FacadeZone(id=FacadeZoneId("FZ-001"), name="Nordfassade")` erstellt korrekt
- [ ] `zone.add_surface(surface_id)` — FacadeSurface kann zugewiesen werden
- [ ] `zone.add_surface(already_in_other_zone)` → `DomainError: Surface bereits in anderer Zone`
- [ ] `FacadeZoneRepository.save(zone)` + `load(zone_id)` — identisch geladen
- [ ] `FacadeZone` ohne Surfaces ist erlaubt (pending-Status)

**Subtasks:**
- [ ] `domain/entities/facade_zone.py` — FacadeZone mit add/remove surface Methoden
- [ ] FacadeZoneId-Generator (FZ-001, FZ-002, ...)
- [ ] `infrastructure/persistence/zone_repository.py` — `FacadeZoneFileRepository`
- [ ] Constraint: FacadeSurface in max. 1 Zone (geprüft beim Hinzufügen)
- [ ] Unit-Tests: Zone erstellen, Surface zuweisen, Constraint-Verletzung

---

## ISSUE-025 | Implement surface confirmation workflow

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
Bestätigungs-Workflow für FacadeSurfaces: DETECTED → CONFIRMED oder REJECTED. Bestätigte Surfaces können einer Zone zugewiesen werden. Nur CONFIRMED-Surfaces werden panelisiert.

**Acceptance Criteria:**
- [ ] `surface.confirm()` → Status CONFIRMED; persistiert
- [ ] `surface.reject(reason="...")` → Status REJECTED; reason gespeichert
- [ ] CONFIRMED-Surface kann nicht erneut rejected werden ohne explizite `force=True`
- [ ] `facade surface confirm FA-001 --zone FZ-001` → Zone-Zuweisung gleichzeitig
- [ ] `PanelizationService` wirft `ValidationError` wenn Surface nicht CONFIRMED ist

**Subtasks:**
- [ ] Status-Übergangs-Logik in `FacadeSurface`
- [ ] `ConfirmSurfaceUseCase` in `application/use_cases/confirm_surface.py`
- [ ] CLI-Befehl `facade surface confirm/reject` mit --zone Option
- [ ] CLI-Befehl `facade surface list` mit Status-Filterung (--status confirmed)
- [ ] E2E-Test: detect → confirm → panelize-Prerequisit-Check

---

## ISSUE-026 | Implement CLI commands: facade surface and facade zone

**Labels:** `type: feature`, `domain: cli`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
Vollständige CLI-Befehle für Surface Detection Workflow und FacadeZone Management.

**Acceptance Criteria:**
- [ ] `facade surface detect --plan <id> --layer "A-FASSADE"` → N Flächen erkannt
- [ ] `facade surface detect --plan <id>` (kein Layer) → alle Layer werden angeboten
- [ ] `facade surface list --plan <id>` → Tabelle: ID, Status, Fläche, Öffnungen
- [ ] `facade surface show FA-001` → vollständige Detailansicht
- [ ] `facade zone create "Nordfassade"` → FZ-001 erstellt
- [ ] `facade zone list` → alle Zonen mit Surface-Anzahl

**Subtasks:**
- [ ] `DetectSurfacesUseCase` in `application/use_cases/detect_surfaces.py`
- [ ] CLI-Befehle in `cli/commands/surface.py`
- [ ] CLI-Befehle in `cli/commands/zone.py`
- [ ] Interaktiver Layer-Auswahlmodus (wenn kein `--layer` angegeben): Liste + Eingabe
- [ ] Rich-Output: Flächen als farbige Tabelle (CONFIRMED=grün, DETECTED=gelb, REJECTED=rot)

---

## ISSUE-027 | Write unit tests for surface detection and geometry service

**Labels:** `type: test`, `domain: planning`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 5

**Beschreibung:**  
Vollständige Unit-Test-Suite für GeometryService und SurfaceDetectionService mit synthetischen Testdaten (keine echten PDFs).

**Acceptance Criteria:**
- [ ] Coverage `domain/services/geometry_service.py` ≥ 90%
- [ ] Coverage `domain/services/surface_detection_service.py` ≥ 85%
- [ ] Alle Edge Cases: leere Geometrie-Liste, identische Polygone, Toleranz-Grenzfälle
- [ ] Performance-Test: 10.000 Geometrien in < 5 Sekunden verarbeitet

**Subtasks:**
- [ ] `tests/unit/domain/test_geometry_service.py` — 20+ Tests
- [ ] `tests/unit/domain/test_surface_detection_service.py` — 15+ Tests
- [ ] Parametrisierte Tests für Toleranz-Grenzfälle (gap = 0mm, 0.4mm, 0.5mm, 1mm)
- [ ] Negative Tests: was passiert wenn keine Geometrien vorhanden?
- [ ] Performance-Fixture: 10.000 synthetische Geometrien

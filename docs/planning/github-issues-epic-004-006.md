# GitHub Issues — EPIC-004 bis EPIC-006
## Facade Planning Engine

---

# EPIC-004: Scale Calibration System

---

## ISSUE-031 | Implement Scale and ScaleCalibration value objects

**Labels:** `type: feature`, `domain: import`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 2

**Beschreibung:**  
`Scale` (Maßstab als Bruch) und `ScaleCalibration` (vollständige Kalibrierungsdaten für Audit) als immutable Value Objects.

**Acceptance Criteria:**
- [ ] `Scale(numerator=1, denominator=100)` → `factor = 0.01`
- [ ] `Scale(numerator=1, denominator=0)` → `ValidationError`
- [ ] `Scale(numerator=0, denominator=100)` → `ValidationError`
- [ ] `ScaleCalibration` enthält: method (TWO_POINT / DIRECT), reference_points, real_distance_mm, calculated_factor, timestamp
- [ ] Beide sind immutable (`frozen=True` oder `@dataclass(frozen=True)`)

**Subtasks:**
- [ ] `domain/value_objects/scale.py` — `Scale` mit factor-Property
- [ ] `domain/value_objects/scale_calibration.py` — `ScaleCalibration`
- [ ] `CalibrationMethod` Enum: `TWO_POINT`, `DIRECT`
- [ ] Unit-Tests: 10 Fälle inkl. Grenzwerte (1:1, 1:1000, 2:100)

---

## ISSUE-032 | Implement TwoPointCalibration use case

**Labels:** `type: feature`, `domain: import`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 3

**Beschreibung:**  
Use Case für Zwei-Punkte-Kalibrierung: zwei Koordinaten aus dem Plan + bekannte Realdistanz → Skalierungsfaktor berechnen und auf alle Geometrien der PlanPage anwenden.

**Acceptance Criteria:**
- [ ] `TwoPointCalibrationUseCase.execute(plan_id, p1, p2, real_distance_mm)` → Plan wird mit Scale gespeichert
- [ ] `p1 == p2` → `CalibrationError: Punkte müssen verschieden sein`
- [ ] `real_distance_mm <= 0` → `CalibrationError: Distanz muss > 0 sein`
- [ ] Alle Geometrien der PlanPage werden neu mit Skalierungsfaktor gespeichert
- [ ] Neu-Kalibrierung eines bereits skalierten Plans → `ScaleOverrideWarning` (kein Fehler)
- [ ] `ScaleCalibration` wird im Plan gespeichert

**Subtasks:**
- [ ] `application/use_cases/calibrate_scale.py` — `TwoPointCalibrationUseCase`
- [ ] Faktor-Berechnung: `pixel_distance = Point2D.distance(p1, p2)` → `factor = real_distance_mm / pixel_distance`
- [ ] Geometrien-Update: alle RawGeometry-Koordinaten × factor
- [ ] Plan-Update: `plan.scale = Scale(...)` + `plan.scale_calibration = ScaleCalibration(...)`
- [ ] Warnung-Logik bei Neu-Kalibrierung (wenn `plan.scale` bereits gesetzt)

---

## ISSUE-033 | Implement DirectScaleInput use case and CLI command

**Labels:** `type: feature`, `domain: import`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 2

**Beschreibung:**  
Direkteingabe des Maßstabs (z.B. 1:100) als Alternative zur Zwei-Punkte-Kalibrierung. Erfordert, dass die Maßeinheit der PDF-Koordinaten bekannt ist (typisch: 1 PDF-Einheit = 1 mm bei 1:1).

**Acceptance Criteria:**
- [ ] `facade plan scale <id> --scale 1:100` → Scale-Faktor 0.01 angewendet
- [ ] `facade plan scale <id> --scale 1:50` → Scale-Faktor 0.02 angewendet
- [ ] `facade plan scale <id> --p1 0,0 --p2 150,0 --real-mm 1500` → Faktor berechnet und angewendet
- [ ] `facade plan scale <id>` (ohne Parameter) → interaktiver Modus: wähle Methode
- [ ] `--help` zeigt beide Optionen mit Beispielen

**Subtasks:**
- [ ] `application/use_cases/calibrate_scale.py` — `DirectScaleInputUseCase` ergänzen
- [ ] CLI-Befehl `facade plan scale` in `cli/commands/plan.py` mit beiden Optionen
- [ ] Eingabe-Parsing: "1:100" → `Scale(1, 100)`
- [ ] Fehlerbehandlung: "1:0", "abc:100", "0:100" → klare Fehlermeldung
- [ ] Unit-Tests für Parsing: 8+ Fälle

---

## ISSUE-034 | Write unit tests for scale calibration accuracy

**Labels:** `type: test`, `domain: import`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 3

**Beschreibung:**  
Präzisions-Tests für die Skalierungsberechnung. NFR-R-001 definiert: Maßabweichung ≤ 1mm bei bekanntem Eingabemaßstab. Diese Tests müssen das erzwingen.

**Acceptance Criteria:**
- [ ] Rechteck 100×50mm bei Maßstab 1:100 → nach Kalibrierung 100.000mm × 50.000mm (±0.001mm)
- [ ] Zwei-Punkte-Kalibrierung mit Distanz 1500mm → Faktor auf 6 Dezimalstellen genau
- [ ] 1000 skalierte Koordinaten: keine Koordinate weicht mehr als 0.5mm ab
- [ ] Parametrisierter Test: Maßstäbe 1:20, 1:50, 1:100, 1:200, 1:500 alle korrekt

**Subtasks:**
- [ ] `tests/unit/domain/test_scale_calibration.py`
- [ ] Parametrisierte Tests: `@pytest.mark.parametrize("scale, expected_factor", [...])`
- [ ] Präzisions-Test: `assert abs(result - expected) < 0.001`
- [ ] Zwei-Punkte-Test: bekannte Geometrie → kalibrieren → Maße prüfen
- [ ] Round-trip-Test: Skalieren + Rückskalieren = Original

---

# EPIC-005: Supplier Format Management

---

## ISSUE-041 | Define and validate JSON catalog schema v1.0

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 2

**Beschreibung:**  
JSON-Schema für Lieferantenkataloge definieren, dokumentieren und als `jsonschema`-Validator implementieren. Schema v1.0 ist stabil für MVP.

**Acceptance Criteria:**
- [ ] JSON-Schema-Datei in `src/facade_engine/infrastructure/catalog/schema/catalog_v1.json`
- [ ] Schema validiert Pflichtfelder: `supplier`, `formats` (Array, min. 1)
- [ ] Format-Objekt: `format_code` (str), `width_mm` (float > 0), `height_mm` (float > 0)
- [ ] Optionales `rules`-Array mit Regelstruktur (id, severity, category, parameters)
- [ ] `supplier_a.json` Fixture ist valide gegen das Schema
- [ ] `invalid_catalog.json` Fixture schlägt Validierung fehl

**Subtasks:**
- [ ] `catalog_v1.json` JSON-Schema schreiben
- [ ] `schema_validator.py` mit `jsonschema.validate()`
- [ ] `fixtures/catalogs/supplier_a.json` erstellen/aktualisieren (Swisspearl-Beispiel)
- [ ] `fixtures/catalogs/invalid_catalog.json` erstellen (width_mm=0)
- [ ] Unit-Tests: 5 valide + 5 invalide Kataloge gegen Schema

---

## ISSUE-042 | Implement JSONCatalogAdapter

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 1  
**Story Points:** 3

**Beschreibung:**  
JSONCatalogAdapter importiert JSON-Katalogdateien, validiert gegen Schema v1.0 und erzeugt `SupplierCatalog`-Domänenobjekte. Implementiert `CatalogImportPort`.

**Acceptance Criteria:**
- [ ] Implementiert `CatalogImportPort`
- [ ] `supplier_a.json` → `SupplierCatalog` mit korrekten PanelFormats
- [ ] `invalid_catalog.json` (width_mm=0) → `CatalogValidationError` mit Feldname
- [ ] Datei nicht gefunden → `FileNotFoundError` mit Pfad in Meldung
- [ ] Ungültiges JSON → `CatalogParseError` mit Zeilennummer

**Subtasks:**
- [ ] `infrastructure/catalog/json_catalog_adapter.py` — implementiert `CatalogImportPort`
- [ ] Schema-Validierung vor Domänenobjekt-Konstruktion
- [ ] Lieferantenregeln-Parsing: `rules` Array → `List[RuleDefinition]`
- [ ] `SupplierCatalog` mit PanelFormats und Rules aufbauen
- [ ] Integration-Test mit `fixtures/catalogs/supplier_a.json`

---

## ISSUE-043 | Implement CSVCatalogAdapter and catalog repository

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: medium`  
**Milestone:** Sprint 1  
**Story Points:** 3

**Beschreibung:**  
CSVCatalogAdapter für tabellarische Katalogformate (Spalten: format_code, width_mm, height_mm, optional material). Catalog-Repository für JSON-Persistenz.

**Acceptance Criteria:**
- [ ] CSV mit Kopfzeile `format_code,width_mm,height_mm` → SupplierCatalog
- [ ] Fehlende Pflicht-Spalte → `CatalogValidationError: Spalte 'width_mm' fehlt`
- [ ] `SupplierCatalogRepository.save(catalog)` + `load(catalog_id)` identisch
- [ ] `CatalogRepository.list_all()` → alle gespeicherten Katalog-IDs

**Subtasks:**
- [ ] `infrastructure/catalog/csv_catalog_adapter.py`
- [ ] CSV-Parsing: `csv.DictReader` mit Header-Validierung
- [ ] CSV ohne Lieferantenregeln (Rules-Array = leer)
- [ ] `infrastructure/persistence/catalog_repository.py`
- [ ] Integration-Tests für CSV + Repository-Roundtrip

---

## ISSUE-044 | Implement CLI commands for catalog management

**Labels:** `type: feature`, `domain: cli`, `scope: mvp`, `priority: medium`  
**Milestone:** Sprint 1  
**Story Points:** 2

**Beschreibung:**  
Vollständige CLI-Befehle für Katalog-Import, -Listing und -Detailansicht.

**Acceptance Criteria:**
- [ ] `facade catalog import supplier_a.json` → "Katalog importiert: CAT-001 | Formate: 5 | Regeln: 2"
- [ ] `facade catalog import formats.csv` → korrekt importiert
- [ ] `facade catalog list` → Tabelle: ID, Lieferant, Formate, Regeln, Datum
- [ ] `facade catalog show CAT-001` → alle Formate als Tabelle; Regeln aufgelistet
- [ ] `facade catalog import nonexistent.json` → Exit-Code 1 + Fehlermeldung

**Subtasks:**
- [ ] `ImportCatalogUseCase` in `application/use_cases/import_catalog.py`
- [ ] CLI-Befehle in `cli/commands/catalog.py`
- [ ] Auto-Erkennung Dateiformat (JSON/CSV) über Dateiendung
- [ ] E2E-Test: catalog import → list → show

---

## ISSUE-045 | Implement supplier rule extraction into RuleCatalog

**Labels:** `type: feature`, `domain: planning`, `rules`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
Beim Import eines Lieferantenkatalogs werden enthaltene Regeln automatisch in den projektweiten RuleCatalog übernommen. Duplikate (gleiche rule_id) werden überschrieben.

**Acceptance Criteria:**
- [ ] Katalog mit 2 Lieferantenregeln → `facade rules list` zeigt diese Regeln nach Import
- [ ] Lieferantenregeln haben `is_builtin=False`, Kategorie `SUPPLIER`
- [ ] Gleiche rule_id beim Re-Import → bestehende Regel wird überschrieben (mit Log)
- [ ] Löschen eines Katalogs → zugehörige Lieferantenregeln werden deaktiviert (nicht gelöscht)

**Subtasks:**
- [ ] `ImportCatalogUseCase` erweitern: nach Catalog-Save → Regeln in RuleCatalog schreiben
- [ ] `RuleCatalogRepository.upsert_rule(rule)` Methode
- [ ] Cascade-Deaktivierung: Regel-Source-Tracking (`source_catalog_id`)
- [ ] Unit-Tests: Import → RuleCatalog-Check; Re-Import → Überschreibung

---

# EPIC-006: Panelization Engine (Core)

---

## ISSUE-051 | Implement BasePanelizationAlgorithm and PanelizationConfig

**Labels:** `type: feature`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
Strategy-Pattern für Panelisierungs-Algorithmen: `BasePanelizationAlgorithm` ABC mit klar definiertem Input/Output-Interface. `PanelizationConfig` mit vollständiger `JointConfig`.

**Acceptance Criteria:**
- [ ] `BasePanelizationAlgorithm.execute(surface, formats, config) -> List[Panel]` ist die einzige abstrakte Methode
- [ ] Austausch eines Algorithmus erfordert keine Änderung am `PanelizationService`
- [ ] `PanelizationConfig` enthält vollständige `JointConfig` (horizontal_joint, vertical_joint, expansion_joint_interval, expansion_joint_width)
- [ ] `JointConfig.horizontal_joint_mm < 8` → `RuleViolation(GR-009, WARNING)` (nicht Exception)
- [ ] `PanelizationConfig` mit Default-Werten: joint=10mm, expansion_interval=6000mm, orientation=AUTO

**Subtasks:**
- [ ] `domain/algorithms/base_algorithm.py` — `BasePanelizationAlgorithm` ABC
- [ ] `domain/value_objects/panelization_config.py` — `PanelizationConfig` mit `JointConfig`
- [ ] `domain/value_objects/joint_config.py` — `JointConfig` mit Validierung
- [ ] Einheitliche Signatur: `execute(surface: FacadeSurface, formats: List[PanelFormat], config: PanelizationConfig) -> List[Panel]`
- [ ] Unit-Tests: Config-Validierung (JointConfig Grenzwerte)

---

## ISSUE-052 | Implement FormatSelectionService

**Labels:** `type: feature`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 2  
**Story Points:** 5

**Beschreibung:**  
FormatSelectionService wählt das optimale PanelFormat für eine gegebene benötigte Fläche. Vollplatten werden bevorzugt. GR-001 und GR-002 werden erzwungen.

**Acceptance Criteria:**
- [ ] Passendes Format vorhanden + passt exakt → vollständige Platte gewählt
- [ ] Mehrere passende Formate → kleinstes passendes gewählt (Verschnittminimierung)
- [ ] Kein Format passt → `None` zurück (→ `PanelizationError PE-001` im Caller)
- [ ] Ausgewähltes Format > Rohplatte → `DomainError` (GR-002-Verletzung, sollte nie passieren)
- [ ] Format aus nicht-aktivem Katalog → wird ignoriert
- [ ] Unit-Tests: 10+ Auswahl-Szenarien

**Subtasks:**
- [ ] `domain/services/format_selection_service.py`
- [ ] Vollplatten-Präferenz: wenn benötigte Fläche ≤ Format → bevorzuge kleinsten vollständigen Fit
- [ ] Zuschnitt-Berechnung: `actual_width = min(required_width, format.width_mm)`
- [ ] `is_cut = actual_width < format.width_mm or actual_height < format.height_mm`
- [ ] Unit-Tests mit parametrisierten Szenarien

---

## ISSUE-053 | Implement GridPanelizationAlgorithm — base rectangle coverage

**Labels:** `type: feature`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 2  
**Story Points:** 13

**Beschreibung:**  
Kern-Algorithmus: Grid-basierte Panelisierung einer rechteckigen Fassadenfläche. Erzeugt ein regelmässiges Grid aus Panels basierend auf dem grössten verfügbaren Format. MVP: nur rechteckige Flächen.

**Acceptance Criteria:**
- [ ] Rechteck 6000×3000mm, Format 1250×600mm, Fuge 10mm → exakte Panel-Anzahl korrekt berechnet
- [ ] Alle Panels liegen vollständig innerhalb der Surface-Boundary
- [ ] Kein Panel überlappt ein anderes (geometrische Invariante)
- [ ] Gesamtfläche (Panels + Fugen) ≤ Surface-Gross-Area
- [ ] Randpanele haben `is_cut=True, cut_reason=EDGE` und korrekte Restmaße
- [ ] Vollplatten haben `is_cut=False`
- [ ] Jedes Panel hat eindeutige `PanelId` (PA-NNN-NNN)
- [ ] Jedes Panel hat `PanelFormat`-Referenz

**Subtasks:**
- [ ] `domain/algorithms/grid_panelization.py` — `GridPanelizationAlgorithm(BasePanelizationAlgorithm)`
- [ ] Grid-Berechnung: `cols = ceil(width / (format_width + joint_h))`, `rows = ceil(height / (format_height + joint_v))`
- [ ] Panel-Positionen: x = col × (format_width + joint_h), y = row × (format_height + joint_v)
- [ ] Randpanel-Maße: last_col_width = surface_width - (cols-1) × (format_width + joint_h)
- [ ] PanelId-Generierung: `PA-{surface_num:03d}-{panel_num:03d}`
- [ ] Unit-Tests: 5 Rechteck-Szenarien mit unterschiedlichen Maßen und Formaten

---

## ISSUE-054 | Implement joint and expansion joint placement

**Labels:** `type: feature`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 5

**Beschreibung:**  
JointConfig-Integration in den Grid-Algorithmus: horizontale und vertikale Fugen zwischen Panels; Bewegungsfugen (GR-008) alle `expansion_joint_interval_mm` als breitere Fugen.

**Acceptance Criteria:**
- [ ] `joint_h=10mm, joint_v=8mm` → Panels haben exakt diese Abstände
- [ ] Bewegungsfuge alle 6000mm (konfigurierbar) → Grid wird an dieser Position unterbrochen
- [ ] Bewegungsfuge-Breite = `expansion_joint_width_mm` (default 15mm)
- [ ] Bewegungsfuge fällt auf Öffnungsmitte → Bewegungsfuge verschoben an nächste Panelgrenze
- [ ] GR-009: wenn `horizontal_joint_mm < 8` → `RuleViolation(WARNING)` generiert (Panelisierung läuft weiter)

**Subtasks:**
- [ ] Bewegungsfugen-Positionsberechnung: `expansion_positions = [i * interval for i in range(1, n)]`
- [ ] Grid-Positions-Anpassung: Panels nach Bewegungsfuge verschoben
- [ ] Kollisions-Check: Bewegungsfuge auf Öffnung → nächste gültige Position suchen
- [ ] Integration in `GridPanelizationAlgorithm`
- [ ] Unit-Tests: Bewegungsfuge bei 6000mm und 8000mm korrekt platziert

---

## ISSUE-055 | Implement PanelizationError handling (PE-001 to PE-004)

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
Vier spezifische Fehlertypen für Panelisierungs-Fehlschläge. Fail-Per-Surface-Strategie: Fehler markiert Fläche, Job läuft weiter.

**Acceptance Criteria:**
- [ ] PE-001 (NO_FORMAT_FITS): wenn kein Format passt → FacadeSurface.status = PANELIZATION_FAILED, Fehlermeldung + Vorschlag
- [ ] PE-002 (EDGE_PANEL_TOO_SMALL): Randpanel < min_panel_width → FAILED mit Größenangabe
- [ ] PE-003 (ALL_PANELS_BLOCKED): alle Panels von Öffnungen eliminiert → FAILED mit Öffnungsstatistik
- [ ] PE-004 (SURFACE_TOO_SMALL): Surface < kleinstes Format → FAILED sofort
- [ ] Job-Result enthält `errors: List[PanelizationError]` mit allen fehlgeschlagenen Flächen
- [ ] CLI-Output: Fehlerliste am Ende + Exit-Code 1 wenn Fehler vorhanden

**Subtasks:**
- [ ] `PanelizationError` Value Object mit `error_type: PanelizationErrorType`, `message`, `suggestion`
- [ ] `PanelizationErrorType` Enum: PE_001..PE_004
- [ ] Error-Detection in `PanelizationService` vor/während Algorithmus
- [ ] Fail-Per-Surface: anderen Surfaces nicht blockieren
- [ ] CLI-Ausgabe: Fehlerliste am Ende mit farbiger Hervorhebung (Rich)

---

## ISSUE-056 | Implement PanelizationService (orchestrates algorithm + rules)

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 2  
**Story Points:** 5

**Beschreibung:**  
PanelizationService orchestriert den gesamten Panelisierungsablauf: Surfaces laden, Algorithmus aufrufen, Rules Engine anwenden, Ergebnisse sammeln, Fehler behandeln.

**Acceptance Criteria:**
- [ ] `PanelizationService.panelize(job) -> PanelizationResult` verarbeitet alle Surfaces im Job
- [ ] Für jede Surface: Algorithmus → Rules → Fehlerbehandlung
- [ ] `RuleEngine.evaluate_result(result, rule_catalog)` wird nach Panelisierung aufgerufen
- [ ] ERROR-Violations → Surface wird als FAILED markiert
- [ ] WARNING-Violations → im Result gespeichert, Panelisierung erfolgreich
- [ ] `PanelizationResult.statistics` enthält: total, full, cut, failed, coverage_percent

**Subtasks:**
- [ ] `domain/services/panelization_service.py`
- [ ] Ablauf: PE-004-Check → Algo.execute → PE-001/002/003-Check → RuleEngine
- [ ] Statistics-Berechnung: coverage_percent = sum(panel.actual_area) / surface.net_area
- [ ] Audit-Log-Hook: jede Entscheidung an AuditLogger weitergeben
- [ ] Unit-Tests: 5 Szenarien (OK, PE-001, PE-002, PE-003, PE-004)

---

## ISSUE-057 | Implement PanelizationJob entity and repository

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
PanelizationJob als Aggregatroot für einen Panelisierungsauftrag. Enthält Config, Referenzen und Result. Job-Repository für Persistenz (Panels in separater Datei wegen Grösse).

**Acceptance Criteria:**
- [ ] `PanelizationJob` mit Status-Übergängen: PENDING → RUNNING → COMPLETED/FAILED
- [ ] `PanelizationJobRepository.save(job)` → `<project>/jobs/<job_id>.json` + `<job_id>_panels.json`
- [ ] `PanelizationJobRepository.load(job_id)` → identisches Objekt
- [ ] `list_all()` → alle Jobs mit Status und Timestamp
- [ ] Panels in separater Datei (kann gross werden)

**Subtasks:**
- [ ] `domain/entities/panelization_job.py` mit Status-Maschine
- [ ] `infrastructure/persistence/job_repository.py`
- [ ] Panels werden in `<job_id>_panels.json` gespeichert (lazy-load)
- [ ] `PanelizationResult` serialisierbar/deserialisierbar
- [ ] Integration-Tests: Roundtrip save→load mit 500 Panels

---

## ISSUE-058 | Implement FacadeZone-based panelization with config override

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: medium`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
Panelisierung kann auf FacadeZone-Ebene gestartet werden. Eine Zone kann eine eigene `PanelizationConfig` haben, die den Job-Default überschreibt.

**Acceptance Criteria:**
- [ ] `facade panelize run --zone FZ-001 --catalog CAT-001` → panelisiert alle CONFIRMED Surfaces in Zone FZ-001
- [ ] Zone ohne Config-Override → Job-Default-Config wird verwendet
- [ ] Zone mit `panelization_override` → Override-Config wird für alle Surfaces dieser Zone verwendet
- [ ] Mischbetrieb: `--zone FZ-001 --zone FZ-002` → beide Zonen in einem Job
- [ ] Surfaces in Zonen mit unterschiedlichen Orientierungen werden korrekt verarbeitet

**Subtasks:**
- [ ] `RunPanelizationUseCase` unterstützt `zone_ids` als Alternative zu `surface_ids`
- [ ] Zone-Surfaces-Auflösung: `FacadeZoneRepository.load(zone_id) → surface_ids`
- [ ] Config-Merge: `zone.panelization_override` überschreibt Job-Config
- [ ] CLI: `facade panelize run --zone FZ-001 --zone FZ-002 --catalog CAT-001`
- [ ] E2E-Test: zwei Zonen, unterschiedliche Orientierungen

---

## ISSUE-059 | Implement CLI commands: facade panelize

**Labels:** `type: feature`, `domain: cli`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
Vollständige CLI-Befehle für Panelisierung: `run` mit allen Konfigurationsparametern, `list` und `show`.

**Acceptance Criteria:**
- [ ] `facade panelize run --surface FA-001 --catalog CAT-001` startet Job und zeigt Statistik
- [ ] `facade panelize run --zone FZ-001 --catalog CAT-001 --joint-h 10 --joint-v 8` funktioniert
- [ ] `facade panelize run` ohne Surface/Zone → Fehlermeldung: "Mindestens eine Surface oder Zone angeben"
- [ ] `facade panelize list` → Tabelle: Job-ID, Status, Surfaces, Panels, Warnungen, Datum
- [ ] `facade panelize show JOB-001` → Detail: Config, Statistik, Fehlerliste, Warnungsliste
- [ ] Fortschrittsanzeige bei > 100 Surfaces

**Subtasks:**
- [ ] `RunPanelizationUseCase` in `application/use_cases/run_panelization.py`
- [ ] CLI-Befehle in `cli/commands/panelize.py`
- [ ] Alle Config-Parameter als CLI-Optionen: `--joint-h`, `--joint-v`, `--expansion-interval`, `--orientation`, `--min-width`, `--min-height`, `--opening-strategy`
- [ ] Rich-Progress-Bar für Panelisierung
- [ ] Farbige Ausgabe: grün = erfolgreich, gelb = Warnungen, rot = Fehler

---

## ISSUE-060 | Write comprehensive unit tests for panelization algorithm

**Labels:** `type: test`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 2-3  
**Story Points:** 8

**Beschreibung:**  
Vollständige Unit-Test-Suite für GridPanelizationAlgorithm. Kein Panel-Test zu klein — der Algorithmus ist der Kern des Systems und muss exhaustiv getestet sein.

**Acceptance Criteria:**
- [ ] Coverage `domain/algorithms/grid_panelization.py` ≥ 90%
- [ ] Coverage `domain/services/panelization_service.py` ≥ 85%
- [ ] Alle PE-001 bis PE-004 Fehlertypen werden korrekt ausgelöst
- [ ] Invarianten-Tests: keine Überlappungen, alle Panels in Boundary, alle Panels haben Format
- [ ] Edge Cases: Surface-Breite = genau Format-Breite, Format grösser als Surface, 1 Panel pro Surface

**Subtasks:**
- [ ] `tests/unit/domain/test_grid_panelization.py` — 25+ Tests
- [ ] Parametrisierter Invarianten-Test: generiert 100 zufällige Rechteck+Format-Kombinationen
- [ ] Fugen-Tests: horizontal ≠ vertikal, Bewegungsfuge an verschiedenen Positionen
- [ ] Öffnungs-Tests: 1/2/3 Fenster, Fenster am Rand, Fenster ≈ gesamte Surface
- [ ] Performance-Test: 50 Surfaces × 100 Panels in < 10 Sekunden

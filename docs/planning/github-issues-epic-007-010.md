# GitHub Issues — EPIC-007 bis EPIC-010
## Facade Planning Engine

---

# EPIC-007: DXF Export System

---

## ISSUE-071 | Implement DXF document structure (AC1027, INSUNITS=mm)

**Labels:** `type: feature`, `domain: export`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 3  
**Story Points:** 3

**Beschreibung:**  
DXF-Dokument-Grundstruktur mit korrekter Version (AC1027 = AutoCAD 2013+), Einheit (INSUNITS=4, Millimeter) und Basis-Layer-Struktur einrichten.

**Acceptance Criteria:**
- [ ] Erzeugtes DXF hat Header-Variablen: `$ACADVER = AC1027`, `$INSUNITS = 4`
- [ ] `ezdxf.readfile(output.dxf)` lädt ohne Fehler
- [ ] Leeres DXF (keine Panels) öffnet in AutoCAD/BricsCAD ohne Warnung
- [ ] `$MEASUREMENT = 1` (metrisch) ist gesetzt
- [ ] DXF-Datei ist < 10MB für 500 Panels

**Subtasks:**
- [ ] `infrastructure/export/dxf_export_adapter.py` — `DXFExportAdapter` implementiert `ExportPort`
- [ ] `ezdxf.new('R2013')` mit korrekten Header-Einstellungen
- [ ] `INSUNITS = 4` (Millimeter) im DXF-Header setzen
- [ ] `MEASUREMENT = 1` im DXF-Header setzen
- [ ] Unit-Test: erzeugtes DXF via ezdxf lesen und Header-Variablen prüfen

---

## ISSUE-072 | Implement layer structure per FacadeSurface

**Labels:** `type: feature`, `domain: export`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 3  
**Story Points:** 3

**Beschreibung:**  
Pro FacadeSurface werden vier DXF-Layer angelegt mit Namenskonvention `FACADE_<SurfaceId>_<TYPE>`. Layer-Farben werden differenziert, um visuell unterscheidbar zu sein.

**Acceptance Criteria:**
- [ ] Pro Surface: Layer `FACADE_FA-001_PANELS`, `_BOUNDARY`, `_OPENINGS`, `_LABELS` vorhanden
- [ ] `FACADE_OVERVIEW` Layer für Gesamtübersicht vorhanden
- [ ] Layer-Farben: PANELS=cyan, BOUNDARY=white, OPENINGS=red, LABELS=yellow
- [ ] `ezdxf.document.layers.get("FACADE_FA-001_PANELS")` gibt korrekten Layer zurück
- [ ] Mehrere Surfaces: jede Surface hat eigene Layer (keine Vermischung)

**Subtasks:**
- [ ] Layer-Erstellung in `DXFExportAdapter._create_layers(result, surfaces)`
- [ ] Farb-Mapping als Konfiguration (nicht hard-coded in Logik)
- [ ] Validierung: kein doppelter Layer-Name
- [ ] Unit-Test: 3 Surfaces → 3×4+1 = 13 Layer im DXF

---

## ISSUE-073 | Implement panel rectangles as LWPOLYLINE entities

**Labels:** `type: feature`, `domain: export`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 3  
**Story Points:** 5

**Beschreibung:**  
Jedes Panel wird als geschlossene LWPOLYLINE (Rechteck aus 4 Punkten) auf dem Surface-spezifischen PANELS-Layer gezeichnet. Koordinaten entsprechen den mm-Werten aus dem Panel-Objekt.

**Acceptance Criteria:**
- [ ] Jedes Panel → eine LWPOLYLINE mit 4 Eckpunkten (geschlossen)
- [ ] Koordinaten: korrekte mm-Werte (Position + Breite + Höhe)
- [ ] Panel auf korrektem Layer (`FACADE_<surface_id>_PANELS`)
- [ ] Geometrische Prüfung: Panel-Fläche im DXF = `actual_width × actual_height` (±0.001mm)
- [ ] 500 Panels → DXF öffnet in < 3 Sekunden in AutoCAD

**Subtasks:**
- [ ] `DXFExportAdapter._export_panels(panels, msp, surface_layer)`
- [ ] LWPOLYLINE: 4 Punkte `[(x, y), (x+w, y), (x+w, y+h), (x, y+h)]` + `close=True`
- [ ] Batch-Verarbeitung: alle Panels einer Surface in einem Layer-Kontext
- [ ] Integration-Test: erzeugtes DXF → ezdxf liest alle LWPOLYLINE-Entities
- [ ] Koordinaten-Validierung: erstes Panel aus DXF entspricht erwartetem Panel-Objekt

---

## ISSUE-074 | Implement panel ID labels as MTEXT entities

**Labels:** `type: feature`, `domain: export`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 3  
**Story Points:** 3

**Beschreibung:**  
Panel-IDs werden als MTEXT-Objekte in der Mitte jedes Panels auf dem LABELS-Layer platziert. Text-Grösse ist proportional zur Panel-Breite.

**Acceptance Criteria:**
- [ ] Jedes Panel → ein MTEXT mit Panel-ID (z.B. "PA-001-042")
- [ ] Position: Pannelmitte (x + w/2, y + h/2)
- [ ] Text-Höhe: min(panel_width, panel_height) × 0.08 (8% der kleinsten Dimension)
- [ ] Text-Höhe mindestens 20mm, maximal 100mm
- [ ] MTEXT auf korrektem Layer (`FACADE_<surface_id>_LABELS`)
- [ ] MTEXT ist zentriert (horizontal + vertikal)

**Subtasks:**
- [ ] `DXFExportAdapter._export_panel_labels(panels, msp, labels_layer)`
- [ ] MTEXT-Eigenschaften: `char_height`, `attachment_point=MiddleCenter`, `insert=(cx, cy)`
- [ ] Text-Grössen-Berechnung als Hilfsfunktion
- [ ] Integration-Test: ezdxf liest alle MTEXT-Entities; Text stimmt mit Panel-ID überein

---

## ISSUE-075 | Implement facade boundaries and openings in DXF

**Labels:** `type: feature`, `domain: export`, `scope: mvp`, `priority: medium`  
**Milestone:** Sprint 3  
**Story Points:** 3

**Beschreibung:**  
Fassadenflächen-Umrisse und Öffnungen werden als LWPOLYLINE auf eigenen Layern exportiert. Öffnungen als gestrichelte Linien für visuelle Unterscheidung.

**Acceptance Criteria:**
- [ ] Surface-Boundary → LWPOLYLINE auf `FACADE_<id>_BOUNDARY` Layer
- [ ] Jede Öffnung → LWPOLYLINE auf `FACADE_<id>_OPENINGS` Layer mit Linetype DASHED
- [ ] Boundary-Layer: weiße Farbe, Linienstärke 0.35mm
- [ ] Openings-Layer: rote Farbe, gestrichelt

**Subtasks:**
- [ ] `DXFExportAdapter._export_surface_boundaries(surfaces, msp)`
- [ ] `DXFExportAdapter._export_openings(surfaces, msp)`
- [ ] DASHED Linetype laden oder definieren im DXF
- [ ] Integration-Test: Surface + 2 Openings → 3 LWPOLYLINE-Entities im DXF

---

## ISSUE-076 | Implement CLI command: facade export dxf

**Labels:** `type: feature`, `domain: cli`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 3  
**Story Points:** 2

**Beschreibung:**  
CLI-Befehl für DXF-Export aus einem abgeschlossenen PanelizationJob.

**Acceptance Criteria:**
- [ ] `facade export dxf JOB-001 --output ./output/facade.dxf` → DXF wird erzeugt
- [ ] `facade export dxf JOB-001` (ohne --output) → Default: `<project>/exports/<timestamp>_<job_id>.dxf`
- [ ] Job nicht abgeschlossen → Fehlermeldung: "Job JOB-001 ist nicht im Status COMPLETED"
- [ ] Ausgabeverzeichnis nicht vorhanden → wird automatisch erstellt
- [ ] Nach Export: Ausgabe: "DXF exportiert: facade.dxf | Panels: 142 | Layer: 8"

**Subtasks:**
- [ ] `ExportDxfUseCase` in `application/use_cases/export_dxf.py`
- [ ] CLI-Befehl in `cli/commands/export.py`
- [ ] Default-Pfad-Generierung: `<exports_dir>/<timestamp>_<job_id>.dxf`
- [ ] Verzeichnis-Erstellung bei fehlendem Output-Pfad
- [ ] E2E-Test: vollständiger Workflow bis `facade export dxf`

---

## ISSUE-077 | Write DXF export integration tests

**Labels:** `type: test`, `domain: export`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 3  
**Story Points:** 5

**Beschreibung:**  
Integration-Tests für DXF-Export. Prüft strukturelle Korrektheit der DXF-Datei via ezdxf, nicht via AutoCAD (kein GUI verfügbar in CI).

**Acceptance Criteria:**
- [ ] `test_dxf_header_correct`: ACADVER=AC1027, INSUNITS=4, MEASUREMENT=1
- [ ] `test_dxf_layer_count`: 3 Surfaces → exakt 13 Layer (3×4+1)
- [ ] `test_dxf_panel_count`: 142 Panels im Job → 142 LWPOLYLINE-Entities auf PANELS-Layern
- [ ] `test_dxf_label_count`: 142 Panels → 142 MTEXT-Entities auf LABELS-Layern
- [ ] `test_dxf_coordinates`: erstes Panel korrekte Koordinaten (bekanntes Ergebnis)
- [ ] `test_dxf_no_overlapping_entities`: keine zwei LWPOLYLINE-Entities überlappen sich

**Subtasks:**
- [ ] `tests/integration/test_dxf_export.py`
- [ ] Fixture: einfaches PanelizationResult mit bekannten Werten (synthetisch, kein echtes PDF)
- [ ] ezdxf-basierte Assertions für alle obigen Tests
- [ ] Koordinaten-Vergleich mit Toleranz ±0.001mm
- [ ] Performance-Test: 500 Panels in < 3 Sekunden exportiert

---

# EPIC-008: Opening Handling System

---

## ISSUE-081 | Implement Opening detection with polygon-in-polygon algorithm

**Labels:** `type: feature`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 5

**Beschreibung:**  
Vollständiger Opening-Erkennungsalgorithmus: Kandidaten-Polygone werden geprüft ob sie vollständig innerhalb einer FacadeSurface-Boundary liegen. Toleranz konfigurierbar.

**Acceptance Criteria:**
- [ ] Polygon vollständig in Surface → Opening (mit Toleranz 1mm für minimal ausserhalb liegende Punkte)
- [ ] Polygon 50% ausserhalb → kein Opening (WARNING: "Teilweise ausserhalb Boundary")
- [ ] Öffnung, die andere Öffnung enthält → nur äussere wird als Opening erfasst (MVP: keine Hierarchie)
- [ ] `Opening.opening_type` wird heuristisch bestimmt (basierend auf Aspect-Ratio + Grösse)
- [ ] Unit-Tests: 10 Szenarien

**Subtasks:**
- [ ] `SurfaceDetectionService.detect_openings(surface, candidates, tolerance=1.0)` erweitern
- [ ] Enthaltensein-Prüfung: `GeometryService.contains(surface.boundary, candidate, tolerance)`
- [ ] Opening-Typ-Heuristik: `aspect_ratio > 2.5` → WINDOW, `aspect_ratio 1.5–2.5` → DOOR, Rest → OTHER
- [ ] Teilweise-Ausserhalb-Warning generieren
- [ ] Unit-Tests mit `fixtures/pdf/facade_with_windows.pdf`

---

## ISSUE-082 | Implement TRIM and DROP strategies for panel-opening intersection

**Labels:** `type: feature`, `domain: planning`, `algorithm`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 8

**Beschreibung:**  
TRIM: Panel wird an Öffnungsgrenze zugeschnitten. DROP: Panel wird vollständig entfernt wenn es eine Öffnung überlappt. Beide Strategien sind über `PanelizationConfig.opening_strategy` wählbar.

**Acceptance Criteria:**
- [ ] TRIM: Panel schneidet Öffnung → Restpanel hat korrekte Restmaße + `is_cut=True, cut_reason=OPENING`
- [ ] TRIM: Restpanel nach Schnitt < min_panel_width_mm → Panel wird entfernt (GR-007)
- [ ] DROP: Panel überschneidet Öffnung auch minimal → Panel entfernt
- [ ] TRIM ist Default (`PanelizationConfig.opening_strategy = TRIM`)
- [ ] Beide Strategien sind Unit-getestet

**Subtasks:**
- [ ] `OpeningExclusionHandler` in `domain/algorithms/opening_exclusion_handler.py`
- [ ] TRIM-Algorithmus: `GeometryService.difference(panel_rect, opening_polygon)` → Restfläche
- [ ] Restflächen-Validierung: wenn Ergebnis kein Rechteck → zu komplex → DROP-Fallback
- [ ] DROP-Algorithmus: `GeometryService.intersects(panel_rect, opening_polygon)` → entfernen
- [ ] GR-007-Check: Restpanel nach TRIM < Mindestmaß → entfernen + `PlanningWarning`

---

## ISSUE-083 | Implement GR-006 and GR-007 rule implementations

**Labels:** `type: feature`, `domain: planning`, `rules`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
GR-006 (Mindestrandabstand Panel zu Öffnung) und GR-007 (Mindestpanelgrösse nach Öffnungsschnitt) als RuleDefinitions implementieren und in builtin_rules.py registrieren.

**Acceptance Criteria:**
- [ ] GR-006: `min_opening_clearance_mm > 0` → Panel näher als Mindestabstand → `RuleViolation(WARNING)`
- [ ] GR-007: Restpanel nach Schnitt < min_panel_width → Panel entfernt + `RuleViolation(INFO)`
- [ ] Beide Regeln erscheinen in `facade rules list`
- [ ] Beide Regeln können via `facade rules configure GR-006 --param min_opening_clearance_mm=30` konfiguriert werden
- [ ] Default GR-006: `min_opening_clearance_mm = 0` (deaktiviert, nur bei Konfiguration aktiv)

**Subtasks:**
- [ ] GR-006 `BuiltinRule` in `domain/rules/builtin_rules.py`
- [ ] GR-007 `BuiltinRule` in `domain/rules/builtin_rules.py`
- [ ] Parameter-Schema für beide Regeln
- [ ] `RuleEngine` integriert GR-006 nach OpeningExclusionHandler
- [ ] Unit-Tests: GR-006 triggerbar/nicht-triggerbar; GR-007 triggerbar

---

# EPIC-009: Rule Engine / Rules Catalog

---

## ISSUE-091 | Implement RuleDefinition, RuleCatalog and RuleViolation

**Labels:** `type: feature`, `domain: planning`, `rules`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 5

**Beschreibung:**  
Drei Kerntypen der Rules Engine Teildomäne: `RuleDefinition` (konfigurierbare Regelspezifikation), `RuleCatalog` (geordnete Regelsammlung pro Projekt), `RuleViolation` (Ergebnis einer Regelprüfung).

**Acceptance Criteria:**
- [ ] `RuleDefinition` ist immutable (frozen), hat alle Felder aus Domänenmodell
- [ ] `RuleCatalog.add_rule(rule)` — Duplikat (gleiche ID) überschreibt bestehende Regel
- [ ] `RuleCatalog.deactivate_rule(rule_id)` — Regel bleibt vorhanden, is_active=False
- [ ] `RuleCatalog.configure_rule(rule_id, parameters)` — Parameter werden gemergt
- [ ] `RuleViolation.suggestion` ist nie leer (kein None)
- [ ] Builtin-Regeln (GR-001..GR-010) können nicht gelöscht werden (nur deaktiviert)

**Subtasks:**
- [ ] `domain/rules/rule_definition.py` — `RuleDefinition` Pydantic-Modell
- [ ] `domain/rules/rule_catalog.py` — `RuleCatalog` Entity mit add/deactivate/configure
- [ ] `domain/rules/rule_violation.py` — `RuleViolation` Value Object
- [ ] `RuleCatalog.get_active_rules(category=None)` — gefilterte aktive Regeln
- [ ] Unit-Tests: 10 RuleCatalog-Operationen

---

## ISSUE-092 | Implement RuleEngine domain service

**Labels:** `type: feature`, `domain: planning`, `rules`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 5

**Beschreibung:**  
RuleEngine evaluiert aktive Regeln gegen Panelisierungsergebnisse. Gibt geordnete Liste von RuleViolations zurück. ERROR-Violations blockieren betroffene Surface.

**Acceptance Criteria:**
- [ ] `RuleEngine.evaluate_result(result, catalog)` → `List[RuleViolation]` geordnet nach Severity
- [ ] `RuleEngine.evaluate_panel(panel, surface, catalog)` → Panel-spezifische Violations
- [ ] ERROR-Violations: werden vom PanelizationService zum FAILED-Status einer Surface
- [ ] WARNING-Violations: im Result gespeichert; Panelisierung erfolgreich
- [ ] INFO-Violations: nur im Audit-Log; nicht in CLI-Output
- [ ] `RuleEngine` hat keine Seiteneffekte (pure function)

**Subtasks:**
- [ ] `domain/rules/rule_engine.py` — `RuleEngine` Domain Service
- [ ] Evaluierungs-Dispatcher: pro Rule-Kategorie eigene Evaluierungs-Methode
- [ ] Severity-Sortierung: ERROR zuerst, dann WARNING, dann INFO
- [ ] `RuleEngine` erhält Regeln als `RuleCatalog` (nicht direkt Repository)
- [ ] Unit-Tests: 15 Evaluierungs-Szenarien (alle GR-001..GR-010)

---

## ISSUE-093 | Implement builtin rules GR-001 to GR-005

**Labels:** `type: feature`, `domain: planning`, `rules`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
Geometrie- und Format-Basisregeln GR-001 bis GR-005 als Builtin-Implementierungen. Diese Regeln sind immer aktiv und nicht deaktivierbar.

**Acceptance Criteria:**
- [ ] GR-001: Panel ohne `format` → `RuleViolation(ERROR, "Panel hat keine Formatreferenz")`
- [ ] GR-002: `panel.actual_width > panel.format.width_mm` → `RuleViolation(ERROR, "Panel überschreitet Rohplattengrösse")`
- [ ] GR-003: `actual_width <= 0 or actual_height <= 0` → `RuleViolation(ERROR, "Ungültige Maße")`
- [ ] GR-004: Doppelte FacadeSurfaceId im Result → `RuleViolation(ERROR, "Surface-ID nicht eindeutig")`
- [ ] GR-005: Doppelte PanelId im Result → `RuleViolation(ERROR, "Panel-ID nicht eindeutig")`
- [ ] Alle 5 Regeln erscheinen in `facade rules list` als `is_builtin=True`

**Subtasks:**
- [ ] `domain/rules/builtin_rules.py` — Klasse `BuiltinRules` mit statischen Methoden
- [ ] GR-001 bis GR-005 als eigenständige Rule-Implementierungen
- [ ] `RuleCatalog.initialize_builtin_rules()` — lädt alle Builtin-Regeln
- [ ] `RuleCatalogRepository` ruft `initialize_builtin_rules()` bei Projekt-Erstellung auf
- [ ] Unit-Tests: je 2 Tests pro Regel (Trigger + kein-Trigger)

---

## ISSUE-094 | Implement builtin rules GR-006 to GR-010

**Labels:** `type: feature`, `domain: planning`, `rules`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
Technical- und Joint-Regeln GR-006 bis GR-010. Diese Regeln sind konfigurierbar (Parameter anpassbar) und haben definierte Defaults.

**Acceptance Criteria:**
- [ ] GR-006: Mindestrandabstand Panel zu Öffnung (default: 0mm = inaktiv)
- [ ] GR-007: Mindestpanelgrösse nach Öffnungsschnitt (default: 50mm)
- [ ] GR-008: Bewegungsfugen-Interval (default: 6000mm)
- [ ] GR-009: Mindestfugengrösse (default: 8mm, WARNING wenn unterschritten)
- [ ] GR-010: Keine zwei Panels überlappen sich (immer aktiv, ERROR)
- [ ] `facade rules configure GR-008 --param expansion_joint_interval_mm=8000` → Parameter geändert

**Subtasks:**
- [ ] GR-006 bis GR-010 in `domain/rules/builtin_rules.py`
- [ ] Parameter-Defaults als Klassen-Konstanten
- [ ] `RuleEngine` ruft spezifische Prüfmethode je Regel auf
- [ ] GR-010 Überlappungsprüfung via `GeometryService.intersects(panel_a, panel_b)` für alle Paare
- [ ] Unit-Tests: je 2 Tests pro Regel

---

## ISSUE-095 | Implement RuleCatalog repository and CLI commands

**Labels:** `type: feature`, `domain: planning`, `rules`, `scope: mvp`, `priority: medium`  
**Milestone:** Sprint 2  
**Story Points:** 3

**Beschreibung:**  
RuleCatalog-Persistenz und CLI-Verwaltungsbefehle für das Regelwerk.

**Acceptance Criteria:**
- [ ] `facade rules list` → Tabelle: ID, Name, Kategorie, Severity, Status, Parameter
- [ ] `facade rules list --category joint` → gefilterte Ausgabe
- [ ] `facade rules disable GR-009 --reason "Sonderbewilligung"` → Regel deaktiviert
- [ ] `facade rules configure GR-008 --param expansion_joint_interval_mm=8000` → Parameter geändert
- [ ] Deaktivierte Regeln erscheinen in Liste mit Status "INACTIVE"
- [ ] Builtin-Regel GR-001 kann nicht gelöscht werden, nur deaktiviert

**Subtasks:**
- [ ] `infrastructure/persistence/rule_catalog_repository.py`
- [ ] `RuleCatalog` wird beim Projekt-Erstellen mit Builtin-Regeln initialisiert
- [ ] CLI-Befehle in `cli/commands/rules.py`
- [ ] `DisableRuleUseCase` + `ConfigureRuleUseCase` in `application/use_cases/`
- [ ] E2E-Test: Regel konfigurieren → panelisieren → Verletzungsverhalten prüfen

---

# EPIC-010: Audit & Traceability System

---

## ISSUE-101 | Implement AuditLogger service and Audit JSON schema

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: medium`  
**Milestone:** Sprint 3  
**Story Points:** 5

**Beschreibung:**  
AuditLogger Service als append-only JSONL-Log pro Job. Audit-JSON enthält vollständiges Schema (GAP-010): config_snapshot, scale_calibration, input_snapshot, results.

**Acceptance Criteria:**
- [ ] `AuditLogger.log_operation(job_id, operation_type, data)` → schreibt in `<job_id>_audit.jsonl`
- [ ] Audit-JSON hat alle Pflichtfelder aus GAP-010-Spezifikation
- [ ] `schema_version: "1.0"`, `timestamp`, `engine_version` in jedem Eintrag
- [ ] `config_snapshot` enthält alle PanelizationConfig-Parameter
- [ ] `scale_calibration` enthält Kalibrierungsmethode und Faktor
- [ ] Audit-Datei kann nach Abschluss als vollständiges JSON exportiert werden

**Subtasks:**
- [ ] `domain/services/audit_logger.py` — `AuditLogger` Service
- [ ] JSONL-Format: eine JSON-Zeile pro Operation (append-only)
- [ ] `audit_entry.py` — typed Data Classes für alle Audit-Eintragstypen
- [ ] `config_snapshot`: `PanelizationConfig.model_dump()` bei Job-Start
- [ ] `scale_calibration`: aus `FacadePlan.scale_calibration` beim Job-Start
- [ ] `domain/services/audit_assembler.py` — assembliert JSONL zu vollständigem Audit-JSON

---

## ISSUE-102 | Implement format selection log in audit

**Labels:** `type: feature`, `domain: planning`, `scope: mvp`, `priority: medium`  
**Milestone:** Sprint 3  
**Story Points:** 3

**Beschreibung:**  
Optionaler Format-Selection-Log pro Panel im Audit. Dokumentiert welches Format warum gewählt wurde. Konfigurierbar (kann für grosse Projekte deaktiviert werden).

**Acceptance Criteria:**
- [ ] `config.audit_format_selection_log = True` (default) → jedes Panel hat Eintrag im Audit
- [ ] Format-Selection-Log enthält: panel_id, position, selected_format, reason, alternatives_considered
- [ ] `reason` ist eines von: FULL_PANEL_FIT, SMALLEST_FIT, ONLY_FIT, NONE_FIT
- [ ] `config.audit_format_selection_log = False` → kein Panel-Log (nur Statistik)
- [ ] `FormatSelectionService` gibt `SelectionReason` mit zurück

**Subtasks:**
- [ ] `SelectionReason` Enum: FULL_PANEL_FIT, SMALLEST_FIT, ONLY_FIT, NONE_FIT
- [ ] `FormatSelectionResult` Value Object: `(format, reason, alternatives_count)`
- [ ] `FormatSelectionService.select_format(...)` gibt `FormatSelectionResult` zurück
- [ ] `PanelizationService` loggt FormatSelectionResult an AuditLogger
- [ ] Unit-Tests: alle 4 SelectionReason-Typen auslösbar

---

## ISSUE-103 | Implement ProcessReport text exporter

**Labels:** `type: feature`, `domain: export`, `scope: mvp`, `priority: medium`  
**Milestone:** Sprint 3  
**Story Points:** 3

**Beschreibung:**  
Menschenlesbarer Prozessreport als Textdatei. Enthält Projektinfo, Input-Zusammenfassung, Panelstatistik, Warnungen, Fehlerliste. Für Fassadenplaner ohne technisches Wissen lesbar.

**Acceptance Criteria:**
- [ ] Report enthält: Projektname, Datum, Plan-Quelle, Maßstab, Anzahl Flächen, Anzahl Panels
- [ ] Statistik: total, full panels, cut panels, Abdeckung %, Flächeneffizienz %
- [ ] Warnungsliste: jede Warnung mit Regelname und betroffener Fläche
- [ ] Fehlerliste: jede fehlgeschlagene Fläche mit Fehlertyp und Vorschlag
- [ ] Report ist ohne Programmierkenntnisse lesbar (keine technischen IDs als primäre Info)
- [ ] Report-Datei ist UTF-8 kodiert

**Subtasks:**
- [ ] `infrastructure/export/report_exporter.py` — `ReportExporter`
- [ ] Report-Template als f-String oder Jinja2-Template (einfach, ohne Template-Engine besser)
- [ ] Abdeckungs-Berechnung: `total_panel_area / total_surface_net_area × 100`
- [ ] CLI-Befehl `facade export report <job_id> --output <path>`
- [ ] Integration-Test: Report enthält alle Pflichtfelder; Encoding korrekt

---

## ISSUE-104 | Write E2E tests for complete workflow

**Labels:** `type: test`, `scope: mvp`, `priority: critical`  
**Milestone:** Sprint 3  
**Story Points:** 8

**Beschreibung:**  
End-to-End-Tests für den vollständigen Workflow: PDF importieren → kalibrieren → Flächen erkennen → bestätigen → Katalog importieren → panelisieren → DXF exportieren → Report. Black-Box via CLI.

**Acceptance Criteria:**
- [ ] `test_complete_workflow_simple_facade`: alle 8 CLI-Schritte grün, DXF erzeugt
- [ ] `test_workflow_with_openings`: Fassade mit 3 Fenstern → Panels überdecken keine Öffnungen
- [ ] `test_workflow_panelization_error`: Surface zu klein → PE-004 + Job trotzdem abgeschlossen
- [ ] `test_workflow_audit_completeness`: Audit-JSON enthält alle Pflichtfelder
- [ ] Exit-Codes korrekt: 0 bei Erfolg, 1 bei Fehler

**Subtasks:**
- [ ] `tests/e2e/test_full_workflow.py` mit `typer.testing.CliRunner`
- [ ] Fixture: reproduzierbares Testprojekt in `tmp_path` (isoliert)
- [ ] `test_complete_workflow_simple_facade`: schrittweiser vollständiger Durchlauf
- [ ] `test_workflow_with_openings`: `fixtures/pdf/facade_with_windows.pdf`
- [ ] Assertions: DXF-Panelanzahl = erwartete Anzahl; Audit-JSON valide; Report vorhanden

---

## ISSUE-105 | Write performance tests for NFR compliance

**Labels:** `type: test`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 3  
**Story Points:** 3

**Beschreibung:**  
Performance-Tests für alle definierten NFRs aus SRS v1.1 Abschnitt 5.1 (geometriebasiert). Tests laufen in CI und schlagen fehl wenn Limits überschritten.

**Acceptance Criteria:**
- [ ] NFR-P-001: PDF-Import 2.000 Geometrien < 5 Sekunden
- [ ] NFR-P-001: PDF-Import 20.000 Geometrien < 20 Sekunden
- [ ] NFR-P-002: Panelisierung 500 Panels < 5 Sekunden
- [ ] NFR-P-003: DXF-Export 500 Panels < 3 Sekunden
- [ ] Tests sind in CI als separate Job-Gruppe (nicht bei jedem Commit ausgeführt — nur auf main)

**Subtasks:**
- [ ] `tests/performance/test_performance_nfr.py`
- [ ] Synthetische Geometrie-Generatoren (keine echten PDFs für Performance-Tests)
- [ ] `pytest-benchmark` oder einfache `time.perf_counter()`-Messungen
- [ ] GitHub Actions: Performance-Job nur auf `push to main` oder `workflow_dispatch`
- [ ] Performance-Report als CI-Artifact speichern

---

## ISSUE-106 | Cross-platform validation and release preparation

**Labels:** `type: chore`, `scope: mvp`, `priority: high`  
**Milestone:** Sprint 3 / Release  
**Story Points:** 5

**Beschreibung:**  
Validierung auf allen Zielplattformen (Windows, macOS, Linux) und Release-Vorbereitung: CHANGELOG, README Quick-Start, pypi-Package-Konfiguration.

**Acceptance Criteria:**
- [ ] CI-Matrix: ubuntu-latest, windows-latest, macos-latest — alle Tests grün
- [ ] `pip install facade-planning-engine` (nach pypi-Publish) installiert CLI korrekt auf allen Plattformen
- [ ] README.md enthält Quick-Start: 5 Schritte von Installation bis erstem DXF-Export
- [ ] CHANGELOG.md v1.0.0 ist vollständig (alle Features dokumentiert)
- [ ] `facade --version` gibt korrekte Versionsnummer aus

**Subtasks:**
- [ ] CI-Matrix erweitern auf windows-latest und macos-latest
- [ ] Plattform-spezifische Pfad-Tests (Windows `\` vs. Unix `/`)
- [ ] `README.md` Quick-Start-Guide schreiben (7 CLI-Befehle mit Beispiel-Output)
- [ ] `CHANGELOG.md` nach Keep a Changelog Format
- [ ] `pyproject.toml` mit vollständigen Paket-Metadaten (description, classifiers, urls)

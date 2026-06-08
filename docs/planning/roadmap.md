# Operative Roadmap
## Facade Planning Engine — MVP

**Version:** 1.0  
**Datum:** 2026-06-08  
**Autor:** Senior Software Architect / Co-Projektleiter  

---

## Grundprinzipien dieser Roadmap

1. **Vertical Slices zuerst:** Jede Phase liefert lauffähige, testbare Software.
2. **Kritischer Pfad zuerst:** Phases 0→1→3→5→6 sind sequenziell (keine Alternative). Phases 2, 4, 7 können parallel starten.
3. **Risiken früh adressieren:** Spike in Phase 0 eliminiert das grösste Implementierungsrisiko (PDF-Bibliothek).
4. **Definition of Done ist nicht verhandelbar:** Eine Phase ist erst abgeschlossen wenn alle DoD-Kriterien erfüllt sind.

---

## Kritischer Pfad (sequenziell, nicht parallelisierbar)

```
Phase 0 (Setup)
    │
    ├──▶ Phase 2 (Scale) ──────────────────────────────┐
    │                                                   │
    └──▶ Phase 1 (Geometry Pipeline) ──▶ Phase 3 (Surfaces) ──▶ Phase 5 (Panelization) ──▶ Phase 6 (DXF)
                                                        │
                                              Phase 4 (Supplier) ──────────────────────────────┘
                                              Phase 9 (Rules) ──────────────────────────────────┘
                                              
Phase 7 (Audit): begleitend zu Phases 5–6
Phase 8 (Stabilisierung): nach Phase 6 abgeschlossen
```

---

## Phase 0: Project Setup
**Dauer:** 2 Wochen  
**Sprint:** Sprint 0  
**Owner:** Tech Lead  

### Ziel
Ein produktionsreifes Entwicklungsfundament schaffen. Die Qualitätshürden des Projekts (CI, Typing, Architektur-Grenzen) sind aktiv erzwungen bevor die erste Zeile Business-Logik geschrieben wird.

### Deliverables

| # | Deliverable | Akzeptanzkriterium |
|---|------------|-------------------|
| P0-D01 | GitHub Repository + Branch-Schutzregeln (main + develop) | PR-Merge zu main erfordert grüne CI |
| P0-D02 | Python-Paketstruktur: `src/facade_engine/`, pyproject.toml | `pip install -e ".[dev]"` läuft fehlerfrei |
| P0-D03 | GitHub Actions CI: lint (ruff) + typecheck (mypy) + test + coverage | Alle Jobs grün bei Push auf develop |
| P0-D04 | Pre-commit hooks: ruff, mypy, import-linter | Commit schlägt fehl bei Architekturverletzung |
| P0-D05 | Domain Entity Stubs (Pydantic) — alle Entitäten leer aber typisiert | mypy ist 0 Fehler auf stubs |
| P0-D06 | Port-Interfaces (ABCs) für alle Adapter | import-linter akzeptiert die Imports |
| P0-D07 | Typer CLI-Skeleton — alle Befehlsgruppen vorhanden, geben "not implemented" zurück | `facade --help` und alle Sub-Befehle zeigen Usage |
| P0-D08 | Test-Infrastruktur: pytest, conftest.py, Coverage-Konfiguration | `pytest tests/unit/` läuft (0 Tests = 0 Failures) |
| P0-D09 | **ADR-002 Spike: PDF-Bibliotheksauswahl** | Entscheidung dokumentiert, ADR-002 Status = Accepted |
| P0-D10 | Basis-Testdaten: min. 1 AutoCAD-PDF + 1 CSV-Katalog in `fixtures/` | Dateien sind valide und geprüft |

### Risiken

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| Spike liefert kein klares Ergebnis (beide Bibliotheken haben Probleme) | Mittel | Entscheidung nach Performance-Priorität; pdfminer.six als Default bei Unentschieden |
| pymupdf AGPL-Lizenz blockiert kommerzielle Nutzung | Hoch (wenn kommerziell geplant) | Lizenzentscheidung als Blocker in Woche 1 klären |
| Import-linter-Konfiguration zu restriktiv → viele False-Positives | Niedrig | Ersten Commit ohne strenge Regeln; schrittweise verschärfen |

### Definition of Done

- [ ] `pip install -e ".[dev]"` ohne Fehler
- [ ] `facade --help` zeigt alle Befehlsgruppen
- [ ] `pytest tests/` läuft durch (0 Failures)
- [ ] CI-Pipeline ist grün auf develop
- [ ] ADR-002 Status ist "Accepted" (Spike abgeschlossen)
- [ ] Kein Entwickler braucht manuelle Setup-Schritte (nur: git clone + pip install)

---

## Phase 1: Core Geometry Pipeline
**Dauer:** 3 Wochen  
**Sprint:** Sprint 1 (Woche 3–5)  
**Abhängigkeit:** Phase 0 abgeschlossen  
**Epics:** EPIC-002  

### Ziel
PDF-Dateien aus AutoCAD, Revit und ArchiCAD werden in normalisierte Domänen-Geometrieobjekte transformiert. Dies ist das Fundament für alle nachgelagerten Features — ohne korrekte Geometrie ist alles weitere wertlos.

### Deliverables

| # | Deliverable | Akzeptanzkriterium |
|---|------------|-------------------|
| P1-D01 | PDFSourceDetector — identifiziert Generator aus PDF-Metadaten | AutoCAD/Revit/ArchiCAD wird korrekt erkannt; "unknown" gibt WARNING |
| P1-D02 | PDFImportAdapter — extrahiert Pfad-Geometrien via gewählte Bibliothek | Linien, Polylines, geschlossene Polygone werden extrahiert |
| P1-D03 | AutoCADPDFNormalizer — Koordinatensystem AutoCAD → Domänen-Koordinaten | Koordinaten ±1mm bei bekanntem Referenzplan |
| P1-D04 | RevitPDFNormalizer — Koordinatensystem Revit → Domänen-Koordinaten | Geometrie aus Revit-PDF ist nutzbar |
| P1-D05 | ArchiCADPDFNormalizer + GenericPDFNormalizer | ArchiCAD-PDF korrekt; Generic gibt WARNING |
| P1-D06 | GeometryMapper — RawGeometry-Objekte mit Layer-Attributen | Alle extrahierten Geometrien haben layer, geometry_type, points |
| P1-D07 | FacadePlan + PlanPage Repository (JSON-Dateibasiert) | Plan wird gespeichert und identisch geladen |
| P1-D08 | CLI: `facade plan import <file>` | Gibt Plan-ID + Geometrie-Statistik aus |
| P1-D09 | CLI: `facade plan layers` | Listet alle Layer mit Geometrie-Anzahl |
| P1-D10 | CLI: `facade plan list` + `facade plan show <id>` | Plan-Details vollständig angezeigt |

### Risiken

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| Revit-PDFs haben keine Layer → Normalisierung schwierig | Hoch | Farb- und Linientyp-basierte Heuristik als Fallback; explizite Warnung |
| PDF-Pfade sind nicht direkt Polygone (bestehen aus Segmenten) | Hoch | Polygon-Reconstruction-Algorithmus mit Toleranz |
| Koordinatenabweichung > 1mm bei bestimmten Maßstäben | Mittel | Floating-Point-Präzision testen; ggf. Dezimalrundung |
| Performance bei 50.000+ Geometrien | Niedrig | Profiling bereits in Phase 1; lazy-loading für Geometrien |

### Abhängigkeiten
- **Voraussetzung:** Phase 0 (Paketstruktur, CI, Entities-Stubs)
- **Liefert an:** Phase 2 (Scale), Phase 3 (Surface Detection)

### Definition of Done

- [ ] AutoCAD-PDF mit 500+ Geometrien importiert ohne Fehler
- [ ] Revit-PDF importiert (mit WARNING wenn layerlos)
- [ ] ArchiCAD-PDF importiert ohne Fehler
- [ ] Koordinaten aus bekanntem Referenzplan ±1mm genau
- [ ] `facade plan layers` zeigt alle Layer mit Statistik
- [ ] Unit-Test-Coverage für GeometryMapper und Normalizer ≥ 80%
- [ ] Integration-Tests für alle 3 Generatoren grün

---

## Phase 2: Scale Calibration System
**Dauer:** 1,5 Wochen  
**Sprint:** Sprint 1 (Woche 4–5, parallel zu Phase 1)  
**Abhängigkeit:** Phase 0 (Datenstrukturen)  
**Epics:** EPIC-004  

### Ziel
Jeder importierte Plan erhält eine präzise Maßstabsdefinition. Ohne korrekte Skalierung sind alle Koordinaten bedeutungslos. Die Zwei-Punkte-Kalibrierung ist die primäre Methode (GAP-002-Entscheidung).

### Deliverables

| # | Deliverable | Akzeptanzkriterium |
|---|------------|-------------------|
| P2-D01 | Scale + ScaleCalibration Value Objects | Immutable, validiert (denominator > 0, distance > 0) |
| P2-D02 | TwoPointCalibration Use Case | p1 ≠ p2 + real_distance_mm > 0 → Faktor korrekt berechnet |
| P2-D03 | DirectScaleInput Use Case (1:100 etc.) | Maßstab 1:50 → Faktor 0.02 |
| P2-D04 | Scale-Anwendung auf PlanPage-Geometrien | Alle Koordinaten nach Skalierung in mm |
| P2-D05 | Validierung + Fehlerbehandlung | Ungültige Inputs → klare Fehlermeldung + Exit-Code 1 |
| P2-D06 | CLI: `facade plan scale <id>` mit beiden Modi | `--p1 --p2 --real-mm` und `--scale 1:100` funktionieren |
| P2-D07 | Warnung bei Neu-Kalibrierung eines verarbeiteten Plans | CLI zeigt Warnung vor Überschreibung |

### Risiken

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| Nutzer gibt falsche Referenzkoordinaten ein | Hoch | Visualisierungs-Hilfe (ASCII-Koordinatenausgabe im MVP nicht möglich — Dokumentation wichtig) |
| Floating-Point-Fehler bei Kalibrierungsfaktor | Niedrig | Double-Precision genug für mm-Bereich |

### Definition of Done

- [ ] Zwei-Punkte-Kalibrierung berechnet Faktor mit ≤ 0,1% Abweichung
- [ ] Direkteingabe `1:100` ergibt Faktor 0.01
- [ ] Alle Geometrien der PlanPage sind nach Skalierung in mm
- [ ] Unit-Test-Coverage Scale-Logik ≥ 90%
- [ ] Fehlerfälle (p1=p2, distance=0) haben klare Fehlermeldungen

---

## Phase 3: Facade Surface Detection
**Dauer:** 2,5 Wochen  
**Sprint:** Sprint 2 (Woche 5–7)  
**Abhängigkeit:** Phase 1 + Phase 2  
**Epics:** EPIC-003, EPIC-008 (Opening-Grundlogik)  

### Ziel
Aus normalisierten, skalierten Geometrien werden FacadeSurfaces identifiziert, bestätigt und FacadeZones zugeordnet. Dies ist die Schnittstelle zwischen "was ist im Plan?" und "was planen wir?".

### Deliverables

| # | Deliverable | Akzeptanzkriterium |
|---|------------|-------------------|
| P3-D01 | GeometryService (Polygon-Operationen via Shapely) | area, contains, difference, intersects korrekt |
| P3-D02 | SurfaceDetectionService — geschlossene Polygone ab Toleranz erkennen | FA-001 bis FA-NNN aus Plan-Geometrien |
| P3-D03 | Opening-Detection — Polygone innerhalb von FacadeSurface-Boundary | Fenster/Türen als Holes in FacadeSurface |
| P3-D04 | FacadeSurface Entity mit Brutto-/Nettofläche | Nettofläche = Brutto − Summe(Opening.area) |
| P3-D05 | FacadeZone Entity + Repository | FZ-NNN, freier Name, 0..* Surfaces |
| P3-D06 | Surface-Bestätigungs-Workflow (DETECTED → CONFIRMED/REJECTED) | Status persistiert korrekt |
| P3-D07 | FacadeSurface Repository (JSON-Dateibasiert) | Surface + Openings werden identisch geladen |
| P3-D08 | CLI: `facade surface detect/list/show` | Flächen-Kandidaten werden aufgelistet |
| P3-D09 | CLI: `facade surface confirm/reject` mit `--zone` Option | Fläche kann Zone zugewiesen werden |
| P3-D10 | CLI: `facade zone create/list/assign` | Zone erstellen und Flächen zuweisen |

### Risiken

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| Polygon nicht vollständig geschlossen (Gap < 1mm) | Hoch | Toleranz-Parameter `close_gap_tolerance_mm` (default 0.5mm) |
| Öffnung wird als eigenständige Fassadenfläche erkannt | Mittel | Kleinstflächen-Filter + manuelle Ablehnung via CLI |
| Korrekte Zuordnung Öffnung → übergeordnete Surface bei überlappenden Flächen | Mittel | Enthält-Prüfung via Shapely `within` |

### Definition of Done

- [ ] Rechteckige Fassadenfläche aus AutoCAD-PDF korrekt erkannt
- [ ] Fenster als Opening erkannt und als Hole gespeichert
- [ ] Nettofläche korrekt berechnet
- [ ] `facade surface confirm FA-001 --zone "Nordfassade"` funktioniert
- [ ] Surface-Repository: save + load identisch
- [ ] GeometryService-Tests ≥ 90% Coverage

---

## Phase 4: Supplier Format System
**Dauer:** 1,5 Wochen  
**Sprint:** Sprint 1-2 (Woche 5–6, parallel zu Phase 3)  
**Abhängigkeit:** Phase 0, EPIC-009 Grundstruktur  
**Epics:** EPIC-005  

### Ziel
Lieferantenkataloge sind importierbar, validiert und liefern sowohl PanelFormats als auch Lieferantenregeln (die in den RuleCatalog fliessen). Dies ist eine Voraussetzung für die Panelisierung.

### Deliverables

| # | Deliverable | Akzeptanzkriterium |
|---|------------|-------------------|
| P4-D01 | JSON-Katalog-Schema v1.0 dokumentiert und validiert | JSON-Schema-Datei in `src/facade_engine/infrastructure/catalog/schema/` |
| P4-D02 | JSONCatalogAdapter — Import + Validierung | Swisspearl-Format-JSON wird importiert; invalid → klarer Fehler |
| P4-D03 | CSVCatalogAdapter — Import + Validierung | CSV mit Spalten width_mm, height_mm, code wird importiert |
| P4-D04 | SupplierCatalog + PanelFormat Entities | Maße > 0 validiert; in mm gespeichert |
| P4-D05 | Lieferantenregel-Extraktion → RuleCatalog | Regeln aus Katalog erscheinen im projektweiten RuleCatalog |
| P4-D06 | Catalog-Repository (JSON-Dateibasiert) | Katalog wird identisch geladen |
| P4-D07 | CLI: `facade catalog import/list/show` | Alle 3 Befehle funktionieren |

### Definition of Done

- [ ] `facade catalog import swisspearl.json` lädt 5+ Formate fehlerfrei
- [ ] `facade catalog import formats.csv` lädt CSV-Formate
- [ ] Lieferantenregeln aus JSON erscheinen in `facade rules list`
- [ ] Ungültige Maße (width=0) → Fehlermeldung

---

## Phase 5: Panelization Engine
**Dauer:** 3 Wochen  
**Sprint:** Sprint 2–3 (Woche 7–9)  
**Abhängigkeit:** Phases 2, 3, 4 + Phase 9 (Rules Engine Grundstruktur)  
**Epics:** EPIC-006, EPIC-008 (Opening-Algorithmus)  

> **Dies ist die kritischste Phase.** Der Grid-Algorithmus, die Fugen-Logik, die Öffnungsbehandlung und die Rules Engine Integration müssen korrekt zusammenspielen. 3 Wochen sind realistisch für 1–2 Entwickler.

### Deliverables

| # | Deliverable | Akzeptanzkriterium |
|---|------------|-------------------|
| P5-D01 | BasePanelizationAlgorithm ABC (Strategy Pattern) | Interface klar definiert; Austausch eines Algorithmus ohne Service-Änderung |
| P5-D02 | PanelizationConfig mit JointConfig | horizontal_joint, vertical_joint, expansion_joint konfigurierbar |
| P5-D03 | FormatSelectionService (GR-001, GR-002) | Vollplatte wird bevorzugt; Überschreitung → Exception |
| P5-D04 | GridPanelizationAlgorithm — Basis (rechteckige Fläche) | 100% Flächenabdeckung ohne Überlappungen |
| P5-D05 | GridPanelizationAlgorithm — Fugenintegration (JointConfig) | Fugen zwischen allen Panels korrekt |
| P5-D06 | GridPanelizationAlgorithm — Bewegungsfugen (GR-008) | Bewegungsfuge alle 6000mm eingefügt |
| P5-D07 | OpeningExclusionHandler (TRIM + DROP Strategie) | Kein Panel überdeckt eine Öffnung |
| P5-D08 | PanelizationError-Typen (PE-001..PE-004) | Jeder Fehlertyp mit spezifischer Meldung + Vorschlag |
| P5-D09 | PanelizationService (orchestriert Algo + Rules) | Fail-Per-Surface: fehlerhafte Fläche markiert; Job läuft weiter |
| P5-D10 | PanelizationJob + Result + Repository | Job + Result werden korrekt persistiert |
| P5-D11 | FacadeZone-basierte Panelisierung mit Config-Override | Zone-spezifische Konfiguration überschreibt Job-Default |
| P5-D12 | CLI: `facade panelize run --surface / --zone` | Job startet; Statistik wird ausgegeben |
| P5-D13 | CLI: `facade panelize list/show` | Jobs und Ergebnisse abrufbar |

### Risiken

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| Grid-Algorithmus korrekt bei Öffnungen am Panelrand | Hoch | Exhaustive Unit-Tests für alle Öffnungs-Positionen |
| Bewegungsfuge fällt auf Öffnung | Mittel | Verschiebelogik: Bewegungsfuge wird an nächste Panelgrenze verschoben |
| Performance bei 2.000 Panels | Niedrig | Profile-Test in Phase 8; Numpy für Gitter-Berechnung optional |

### Definition of Done

- [ ] Rechteck 6000×3000mm, Format 1250×600mm, Fuge 10mm → korrekte Panel-Anzahl
- [ ] Kein Panel überlappt ein anderes
- [ ] Kein Panel liegt ausserhalb der Surface-Boundary
- [ ] Kein Panel überdeckt eine Öffnungsfläche
- [ ] Bewegungsfuge alle 6000mm korrekt eingefügt
- [ ] PE-001 bis PE-004 werden korrekt ausgelöst
- [ ] Unit-Test-Coverage Algorithmus ≥ 85%

---

## Phase 6: DXF Export
**Dauer:** 1,5 Wochen  
**Sprint:** Sprint 3 (Woche 9–10)  
**Abhängigkeit:** Phase 5  
**Epics:** EPIC-007  

### Ziel
Ein vollständiges PanelizationResult wird als valides DXF exportiert, das in AutoCAD 2013+ und BricsCAD öffenbar ist. Die Layer-Struktur erlaubt dem CAD-Techniker sofortige Weiterarbeit.

### Deliverables

| # | Deliverable | Akzeptanzkriterium |
|---|------------|-------------------|
| P6-D01 | DXF-Dokument mit AC1027 und INSUNITS=4 (mm) | AutoCAD zeigt mm-Koordinaten korrekt |
| P6-D02 | Layer-Struktur pro FacadeSurface | FACADE_FA-001_PANELS, _BOUNDARY, _OPENINGS, _LABELS |
| P6-D03 | Panels als LWPOLYLINE auf korrektem Layer | Alle Panel-Rechtecke mit korrekten Koordinaten |
| P6-D04 | Panel-IDs als MTEXT auf Labels-Layer | Jedes Panel mit ID-Text beschriftet |
| P6-D05 | Flächen-Boundaries als LWPOLYLINE auf Boundary-Layer | Fassadenumrisse sichtbar |
| P6-D06 | Öffnungen als LWPOLYLINE auf Openings-Layer | Fenster/Türen als separate Geometrien |
| P6-D07 | DXFExportAdapter (implementiert ExportPort) | `facade export dxf --job <id>` erzeugt DXF |
| P6-D08 | CLI: `facade export dxf --job <id> --output <path>` | DXF am angegebenen Pfad gespeichert |

### Risiken

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| INSUNITS-Einstellung wird von alter AutoCAD-Version ignoriert | Niedrig | Expliziter Test mit AC1027 + ezdxf-Validierung |
| MTEXT-Grösse/Position passt nicht zu Panel-Grösse | Mittel | Text-Grösse = Panel-Breite × 0.1; zentriert |

### Definition of Done

- [ ] DXF öffnet ohne Fehler in AutoCAD 2013 (oder BricsCAD)
- [ ] Alle Panels sind als Rechtecke sichtbar
- [ ] Panel-IDs als Text auf eigenem Layer
- [ ] INSUNITS korrekt: mm
- [ ] Layer-Struktur stimmt mit Spezifikation überein
- [ ] Integration-Test: ezdxf kann DXF lesen und Entities validieren

---

## Phase 7: Audit & Traceability System
**Dauer:** 1,5 Wochen  
**Sprint:** Sprint 3 (Woche 8–10, begleitend)  
**Abhängigkeit:** Phases 2, 5  
**Epics:** EPIC-010  

### Ziel
Jede Panelisierungsoperation ist vollständig reproduzierbar dokumentiert. Das Audit-JSON enthält alle Parameter, Entscheidungen und Ergebnisse. Der Prozessreport ist für Fassadenplaner lesbar.

### Deliverables

| # | Deliverable | Akzeptanzkriterium |
|---|------------|-------------------|
| P7-D01 | AuditLogger Service (append-only JSONL) | Jede Operation erzeugt einen Audit-Eintrag |
| P7-D02 | Vollständiges Audit-JSON (Schema aus GAP-010) | Enthält: config_snapshot, scale_calibration, format_selection_log, violations |
| P7-D03 | Config-Snapshot im Audit | Alle PanelizationConfig-Parameter im Audit |
| P7-D04 | FormatSelection-Log pro Panel (konfigurierbar) | Welches Format warum gewählt — im Audit nachvollziehbar |
| P7-D05 | ProcessReport-Exporter (Textformat) | Menschenlesbarer Report: Flächen, Panels, Warnungen, Statistik |
| P7-D06 | CLI: `facade export report --job <id>` | Report-Datei wird erzeugt |

### Definition of Done

- [ ] Audit-JSON enthält alle Pflichtfelder aus GAP-010-Spezifikation
- [ ] Aus dem Audit-JSON kann die Panelisierung manuell nachvollzogen werden
- [ ] ProcessReport ist ohne technisches Wissen lesbar (für Fassadenplaner)
- [ ] Format-Selection-Log ist pro Panel oder als Zusammenfassung konfigurierbar

---

## Phase 8: Stabilisierung & Testing
**Dauer:** 1 Woche + Release  
**Sprint:** Sprint 3 / Release-Sprint (Woche 10–11)  
**Abhängigkeit:** Alle vorherigen Phasen  

### Ziel
Das System ist produktionsreif, cross-platform validiert und als v1.0 releasbar.

### Deliverables

| # | Deliverable | Akzeptanzkriterium |
|---|------------|-------------------|
| P8-D01 | E2E-Test: vollständiger Workflow PDF → DXF | Alle Schritte grün mit realen Testdaten |
| P8-D02 | Performance-Tests NFR-P-001/002/003 | Alle Zeitlimits eingehalten |
| P8-D03 | Cross-Platform-Tests: Windows 10+, macOS 12+, Ubuntu 22.04+ | Keine platform-spezifischen Fehler |
| P8-D04 | Edge-Case-Tests (PE-001..PE-004, Randfälle Algorithmus) | Alle Fehlertypen korrekt ausgelöst |
| P8-D05 | README.md mit Quick-Start-Guide | Neuer Nutzer kann in < 10 Min ersten Plan importieren |
| P8-D06 | CHANGELOG v1.0 | Alle Features dokumentiert |
| P8-D07 | pypi-Package-Konfiguration (optional) | `pip install facade-planning-engine` installiert das CLI |

### Definition of Done

- [ ] Alle Tests grün auf allen 3 Plattformen
- [ ] Performance-NFRs erfüllt (kleines Projekt < 5s Import, < 5s Panelisierung)
- [ ] `facade --help` vollständig und korrekt
- [ ] Release-Tag v1.0.0 auf main

---

## Zeitplan-Übersicht

```
Woche    01  02  03  04  05  06  07  08  09  10  11
─────────────────────────────────────────────────────
Phase 0  ████████
Phase 1          ████████████
Phase 2              ████████
Phase 3                  ████████████
Phase 4              ████████
Phase 9  (Rules)         ████████
Phase 5                          ██████████████
Phase 6                                    ████████
Phase 7                              ████████████
Phase 8                                        ████
Release                                            ▶ v1.0
```

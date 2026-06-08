# Critical Check — Projektplanung Facade Planning Engine
## AUFGABE 5: Architektonische und Planerische Risikoanalyse

**Version:** 1.0  
**Datum:** 2026-06-08  
**Erstellt durch:** Senior Software Architect / Co-Projektleiter  
**Basis:** EPIC-001 bis EPIC-010, Roadmap, MVP-Definition, alle Issues ISSUE-001..ISSUE-106

---

## 1. Fehlende Epics

Die 10 definierten Epics decken alle Feature-Bereiche des MVP ab. Folgende **querschnittliche Epics fehlen** und sollten entweder als eigenständige Epics oder als Milestones behandelt werden:

---

### FEHLENDES EPIC A | CLI User Experience & Error Messages

**Problem:**  
Über alle Feature-Epics verteilt entstehen inkonsistente Fehlermeldungen, uneinheitliche CLI-Ausgabeformate und kein definiertes Error-Handling-Verhalten. Es gibt aktuell **kein zentrales CLI-UX-Konzept**.

**Auswirkung:**  
- Jedes Epic implementiert Fehlerausgabe eigenständig → inkonsistente Nutzererfahrung
- Fehlermeldungen ohne konkreten Handlungsvorschlag → schlechte UX für Fassadenplaner
- Kein definierter Exit-Code-Standard → E2E-Tests instabil

**Empfehlung:**  
Entweder als kleines EPIC-011 (3-4 Issues) oder als **Sprint-0-Deliverable**:
- CLI-Ausgabeformatierung (Tabellen via Rich oder tabulate)
- Exit-Code-Standard (0=OK, 1=UserError, 2=SystemError, 3=ValidationError)
- Fehlerklassen-Hierarchie: `UserInputError`, `DomainRuleError`, `SystemError`
- `--verbose` / `--json-output` Flags für alle Befehle

**Priorität:** SHOULD (vor Sprint 2 definieren)

---

### FEHLENDES EPIC B | Project Management (Projektpersistenz)

**Problem:**  
EPIC-001 enthält Entity-Stubs, aber das `facade project create` Kommando und die gesamte Projekt-Persistenz-Logik ist **keinem Epic zugeordnet**. Wo wird `ProjectRepository` implementiert? Wer erstellt die Verzeichnisstruktur?

**Auswirkung:**  
- EPIC-002 (PDF Import) setzt eine Projektstruktur voraus, die nicht definiert ist
- Das `<project_dir>` Konzept aus dem Datenmodell ist kein Issue
- `facade project create` fehlt in allen Issue-Dateien

**Empfehlung:**  
2-3 Issues zu EPIC-001 hinzufügen:
- ISSUE-009 | Implement ProjectRepository and project directory structure
- ISSUE-010 | Implement `facade project create` CLI command

**Priorität:** MUST (Blocker für alle Epics)

---

### FEHLENDES EPIC C | Release Engineering

**Problem:**  
ISSUE-106 (Cross-platform + Release) ist vorhanden, aber deckt nicht ab:
- Versionierungs-Workflow (Semantic Versioning, wer bumpt die Version?)
- PyPI-Publish-Pipeline in GitHub Actions (fehlt komplett)
- `CONTRIBUTING.md` und Entwickler-Onboarding
- Keine Dokumentation für End-User (nur README Quick-Start)

**Empfehlung:**  
Nicht als separates Epic, aber als **GitHub Milestone "Release v1.0"** mit Issues:
- Semantic versioning via `bump2version` oder `commitizen`
- GitHub Actions: `on: push to tag v*` → PyPI publish
- End-User Dokumentation: `docs/user-guide/` (5 Seiten)

**Priorität:** SHOULD (nach Sprint 3, vor Release)

---

## 2. Technische Risiken

---

### RISK-T-001 | EPIC-001 Scope zu weit für Sprint 0

**Problem:**  
EPIC-001 enthält 8+ Issues inkl. ADR-002 Spike. Sprint 0 soll Fundament + Spike liefern — das ist realistisch **zu viel für 2 Wochen mit einem Entwickler**. Besonders der Spike (ADR-002) braucht Zeit.

**Konkrete Issues:**  
ISSUE-008 (Spike) ist allein schon 5 SP. ISSUE-001..007 sind weitere 15+ SP. Total: 20+ SP in Sprint 0.

**Empfehlung:**
- Spike ISSUE-008 zuerst (Woche 1, blockierend für EPIC-002)
- ISSUE-001..004 (Package-Struktur, CI) parallel in Woche 1-2
- ISSUE-005..007 (Stubs, ABCs, CLI-Skeleton) können in Woche 2 parallel
- ADR-002 muss spätestens Ende Sprint 0 entschieden sein — hard deadline

**Severity:** HIGH

---

### RISK-T-002 | ADR-002 Spike-Ausgang blockiert EPIC-002 vollständig

**Problem:**  
Wenn die Spike-Entscheidung (pdfminer.six vs. pymupdf) zu `pymupdf` tendiert, muss **LGPL-3.0 Lizenzfrage** geklärt werden (GAP-003 — kommerzielle Nutzung). Diese Lizenzklärung kann Wochen dauern bei grösseren Organisationen.

**Risikoszenario:**  
Spike in Woche 1-2 → pymupdf präferiert → Lizenz unklar → EPIC-002 blockiert bis Woche 5+.

**Empfehlung:**
- Fallback-Entscheidung VOR dem Spike festlegen: "Wenn Lizenz nicht bis [Datum] geklärt → pdfminer.six"
- Parallel: Lizenzklärung als Track des Projektleiters (nicht des Entwicklers)
- Spike-Kriterien dokumentieren: nur wenn pymupdf in ALLEN Kriterien deutlich besser → wählen

**Severity:** CRITICAL

---

### RISK-T-003 | EPIC-006 GridPanelizationAlgorithm ist unterschätzt

**Problem:**  
ISSUE-053 (GridPanelizationAlgorithm) hat 13 Story Points — das ist das grösste einzelne Issue im ganzen Projekt. Die Integration von Bewegungsfugen (GR-008) mit dem Grid-Algorithmus ist komplex: Bewegungsfugen teilen den Grid in Segmente auf, was die Koordinaten-Logik erheblich verkompliziert.

**Konkrete technische Herausforderung:**
- Expansion Joint teilt Surface bei x=6000 → zwei Sub-Grids
- Panel bei x=5900 und width=200 → überschreitet Joint bei 6000 → Panel muss gesplittet werden?
- Oder: Grid-Startpunkt verschiebt sich nach Joint? (semantisch unterschiedlich)
- Diese Entscheidung (Split-Panel vs. Grid-Reset) fehlt in der aktuellen Spezifikation

**Empfehlung:**
- Design-Session vor ISSUE-053: "Wie verhält sich das Grid an Bewegungsfugen?"
- In Domain-Model dokumentieren: Behaviour bei Grid-Segment-Grenze
- Spike-Ticket für Prototyp der Bewegungsfugen-Logik (< 2h) vor Sprint 2

**Severity:** HIGH

---

### RISK-T-004 | EPIC-002 RevitPDFNormalizer Layerlos-Fallback: Testbarkeit

**Problem:**  
ISSUE-018 (Revit PDF mit echten Layer-Daten) und der Layerlos-Fallback (Farb-/Linientyp-basierte Pseudo-Layers) sind schwer automatisiert testbar. Echte Revit-PDFs werden aus Datenschutzgründen vermutlich nicht als Test-Fixtures eingecheckt.

**Konkrete Konsequenz:**  
Der GenericPDFNormalizer und der RevitPDFNormalizer-Fallback werden nur auf einem tatsächlichen Projekt validiert — nicht in CI.

**Empfehlung:**
- Synthetische Test-PDFs (via ReportLab oder ähnliches) als Fixtures erzeugen, die Revit-typische Metadaten haben
- Alternativ: `tests/fixtures/pdf/README.md` dokumentiert welche Fixtures fehlen + manuelle Teststufe
- Acceptance Criterion zu ISSUE-018: "Wenn kein Revit-PDF verfügbar → Test mit synthetischem PDF und `Producer=Revit`"

**Severity:** MEDIUM

---

### RISK-T-005 | EPIC-009 hängt von EPIC-001 ab, aber EPIC-005 hängt von EPIC-009 ab

**Problem:**  
Der Dependency-Graph zeigt EPIC-009 als Voraussetzung für EPIC-005 (Supplier Rule Import). EPIC-005 ist Voraussetzung für EPIC-006. Wenn EPIC-009 langsamer voranschreitet als geplant, gerät die gesamte Panelisierungs-Pipeline ins Stocken.

**Konkrete Abhängigkeit:**
```
EPIC-009 (Rules: ISSUE-091..095) → EPIC-005 (Supplier: ISSUE-041-045) → EPIC-006 (ISSUE-051-060)
```

Wenn EPIC-009 Verzögerung hat → EPIC-005 kann Supplier-Regeln nicht importieren → EPIC-006 kann nicht integrationsgetestet werden.

**Empfehlung:**
- EPIC-009 in Sprint 1 priorisieren (Parallel zu EPIC-002/004)
- `RuleCatalog.initialize_builtin_rules()` als Sprint-1-Deliverable definieren (ISSUE-091-093 früh)
- EPIC-005 kann ohne Supplier-Regeln initial starten — Supplier-Regel-Import als letztes ISSUE-045

**Severity:** MEDIUM

---

### RISK-T-006 | Keine Fehlerbehandlung bei ungültigem Projektverzeichnis

**Problem:**  
Viele CLI-Befehle setzen ein initialisiertes Projekt voraus (`facade project create` muss vorher ausgeführt worden sein). Es gibt keinen Issue, der das Verhalten definiert wenn kein Projekt initialisiert wurde.

**Konkrete Szenarien:**
- User führt `facade plan import plan.pdf` in falschem Verzeichnis aus
- Projektverzeichnis wurde manuell gelöscht
- `.facadeplanner/` Verzeichnis existiert aber `project.json` ist korrupt

**Empfehlung:**
- ISSUE-009 (projektRepository) muss `ProjectNotInitializedError` definieren
- Alle CLI-Befehle rufen `ProjectService.require_initialized()` auf bevor sie ausführen
- Fehlermeldung: "Kein Projekt gefunden. Bitte zuerst `facade project create <name>` ausführen."

**Severity:** HIGH

---

## 3. Überdimensionierte Epics (Split-Vorschläge)

---

### EPIC-006 ist zu gross (Split empfohlen)

**Aktuell:**  
EPIC-006 enthält 14 Issues (ISSUE-051 bis ISSUE-060 + implizite Sub-Features). Schätzung: ~55 Story Points. Das ist in einem Sprint nicht lieferbar.

**Split-Vorschlag:**

```
EPIC-006A | Panelization Core (Grid Algorithm)
  - ISSUE-051: BasePanelizationAlgorithm ABC
  - ISSUE-052: PanelizationConfig + JointConfig Integration
  - ISSUE-053: GridPanelizationAlgorithm (13 SP)
  - ISSUE-054: JointConfig horizontal/vertical (5 SP)
  - ISSUE-060: Unit Tests Algo
  Priorität: Critical | Sprint 2

EPIC-006B | Panelization Service & Job Management
  - ISSUE-055: Bewegungsfugen (8 SP)
  - ISSUE-056: PanelizationService + RuleEngine Integration
  - ISSUE-057: PanelizationJob + PanelizationResult
  - ISSUE-058: PanelizationRepository (file-based)
  - ISSUE-059: CLI Commands
  Priorität: Critical | Sprint 2-3
```

**Vorteil:** Bessere Parallelisierung (zwei Entwickler), klarerer Fortschritt in Burndown-Chart.

---

### EPIC-002 ist zu gross (aber tolerierbar)

**Aktuell:**  
EPIC-002 enthält 9 Issues (ISSUE-011 bis ISSUE-019). Schätzung: ~38 Story Points. Verteilt auf 2 Wochen (Phase 1) ist das sehr eng.

**Risiko:**  
RevitPDFNormalizer (ISSUE-018) und ArchiCADPDFNormalizer (ISSUE-017) blockieren sich gegenseitig nicht — sie können parallel entwickelt werden. Aber der ADR-002 Spike-Ausgang beeinflusst alle.

**Empfehlung:**  
Kein Split notwendig wenn:
1. Spike in Sprint 0 abgeschlossen
2. ISSUE-015 (AutoCAD) → ISSUE-016 (Generic) → ISSUE-017/018 (parallel) → ISSUE-019 (Tests)
3. Normalizer-Reihenfolge explizit im Sprint Planning definiert

---

## 4. Abhängigkeitsprobleme

---

### PROBLEM-D-001 | Zirkuläre Konzept-Abhängigkeit zwischen EPIC-003 und EPIC-008

**Problem:**  
- EPIC-003 (Surface Detection) enthält FacadeSurface mit Openings-Attribut
- EPIC-008 (Opening Handling) baut auf FacadeSurface auf
- Wenn EPIC-003 zuerst ausgeliefert wird (ohne Openings), ist FacadeSurface `openings: List[Opening]` leer und die Entität ist unvollständig
- Wenn EPIC-008 von EPIC-003-Entities abhängt — aber EPIC-003 noch die Opening-Slots braucht — gibt es eine Henne-Ei-Situation

**Lösung:**
- EPIC-003 implementiert `FacadeSurface` mit `openings: List[Opening] = []` (leere Liste als Default)
- EPIC-008 ergänzt Opening-Erkennung und befüllt das Feld nachträglich
- EPIC-003 Issues brauchen keine Opening-Logik — nur das Datenfeld-Stub

**Handlungsbedarf:** ISSUE-021 (GeometryService) um Opening-Stub-Attribut ergänzen

---

### PROBLEM-D-002 | EPIC-007 setzt vollständiges PanelizationResult voraus — aber EPIC-006B kommt spät

**Problem:**  
DXF-Export (EPIC-007) hängt von einem vollständigen PanelizationResult ab. Wenn EPIC-006 gesplittet wird in 006A + 006B, kann DXF-Export erst nach 006B starten. Das verschiebt den ersten echten DXF-Test auf Ende Sprint 3.

**Konsequenz:**  
Kein "Sehe ich was ich bekomme" Feedback bis Sprint 3. Das ist aus Produkt-Perspektive riskant.

**Empfehlung:**  
- Integration-Test mit **synthetischem PanelizationResult** (kein echtes PDF) in EPIC-007 ermöglicht frühes Testen
- ISSUE-071 (DXF-Dokument-Grundstruktur) kann bereits mit Mock-Result entwickelt werden
- Vertikaler Schnitt: ein einfaches Szenario (1 Surface, 6 Panels, 0 Openings) als Smoke-Test

---

### PROBLEM-D-003 | EPIC-010 hat keine klare Verantwortung im Panelisierungs-Flow

**Problem:**  
AuditLogger (EPIC-010) muss von PanelizationService (EPIC-006) aufgerufen werden. Aber EPIC-010 kommt nach EPIC-006 im Dependency-Graph. Das bedeutet: EPIC-006 muss `AuditLogger` bereits korrekt aufrufen — bevor EPIC-010 vollständig implementiert ist.

**Konkrete Frage:**  
Wie ruft `PanelizationService` (EPIC-006) den `AuditLogger` auf, wenn dieser noch nicht implementiert ist?

**Lösung:**
- `AuditPort` (Interface) in EPIC-001 oder EPIC-006 definieren (kein Audit-Code, nur Interface)
- EPIC-006: `PanelizationService` nimmt `AuditPort` per Dependency Injection entgegen
- EPIC-010: implementiert `AuditLoggerAdapter(AuditPort)` — tauscht Null-Adapter aus
- `NullAuditAdapter` als Default: tut nichts, schreibt nichts

**Handlungsbedarf:** ISSUE-052 (PanelizationConfig) oder EPIC-001 um `AuditPort` ABC ergänzen

---

### PROBLEM-D-004 | Scale Calibration (EPIC-004) ist Voraussetzung für EPIC-003, aber nicht für EPIC-002

**Problem:**  
EPIC-002 extrahiert Rohgeometrien in PDF-Koordinaten. EPIC-004 kalibriert den Maßstab. EPIC-003 braucht kalibrierte Koordinaten. Aber: in der aktuellen Issue-Struktur ist unklar, wo der Skalierungsfaktor **angewendet** wird:

Option A: EPIC-004 transformiert alle Geometrien beim Kalibrieren (in place)  
Option B: EPIC-003 wendet den Faktor während der Surface-Erkennung an

**Problem:** In beiden Issues fehlt diese Spezifikation.

**Empfehlung:**
- Entscheidung in ISSUE-031 (Scale Value Objects): "Skalierung wird beim Kalibrieren auf PlanPage angewendet (Option A)"
- `PlanPage.apply_scale(factor)` transformiert alle `RawGeometry`-Koordinaten in-place
- EPIC-003 erhält bereits kalibrierte Koordinaten — kein Faktor-Handling nötig

**Handlungsbedarf:** ISSUE-031 Acceptance Criteria um Punkt ergänzen: "PlanPage.apply_scale(factor) transformiert alle Koordinaten; danach sind alle Koordinaten in mm"

---

## 5. Weitere Hinweise

---

### HINWEIS-1 | Story-Point-Inflation bei Test-Issues

**Beobachtung:**  
Test-Issues (ISSUE-027, ISSUE-034, ISSUE-060, ISSUE-077, ISSUE-104, ISSUE-105) haben 3-8 SP. Das ist korrekt bewertet. Aber die **Testinfrastruktur** (Fixtures, conftest.py) ist in EPIC-001 (ISSUE-005) — wenn diese schlecht oder gar nicht implementiert wird, steigen alle Test-Issue-Aufwände.

**Empfehlung:** ISSUE-005 (Test-Infrastruktur) hat 5 SP und ist kritischer Blocker. Nicht unterschätzen.

---

### HINWEIS-2 | Keine Issues für Supplier-Regelvalidierung (Fehlerfall)

**Beobachtung:**  
`JSONCatalogAdapter` importiert Lieferantenregeln und übergibt sie dem RuleCatalog. Aber was passiert wenn eine Lieferantenregel in der JSON-Datei einen Fehler hat? (z.B. ungültige Rule-ID, unbekannte Severity)

**Fehlender Issue:**  
Validierungsverhalten bei fehlerhaftem `"rules": [...]` im Katalog-JSON ist nicht spezifiziert. Aktuell würde Pydantic eine `ValidationError` werfen — unklar ob das eine benutzbare Fehlermeldung ergibt.

**Empfehlung:** ISSUE-044 (CSVCatalogAdapter) oder neues ISSUE-046 um Katalog-Validierungs-Fehlerbehandlung erweitern.

---

### HINWEIS-3 | FacadeZone Config-Override für Panelisierung nicht vollständig spezifiziert

**Beobachtung:**  
`facade panelize run --zone FZ-001` mit optionalem Config-Override ist im MVP definiert. Aber: wenn Zone A einen anderen `joint_h` hat als Zone B, und eine FacadeSurface wird beiden Zonen zugewiesen — welche Config gewinnt?

**Fehlende Entscheidung:** Zonen-Config-Override-Semantik (letzte Zone gewinnt? Warnung? Fehler?)

**Empfehlung:** Entscheidung in ISSUE-057 (PanelizationJob) festlegen: "Config-Override ist pro Job definiert; wenn mehrere Zonen mit unterschiedlichen Configs — erste Zone gewinnt, WARNING."

---

## 6. Zusammenfassung der Massnahmen

| ID | Massnahme | Priorität | Zuordnung |
|----|-----------|-----------|-----------|
| M-01 | EPIC-011 CLI UX erstellen ODER Sprint-0-Deliverable | SHOULD | Sprint 0 |
| M-02 | ISSUE-009/010 (ProjectRepository, `facade project create`) zu EPIC-001 hinzufügen | MUST | EPIC-001 |
| M-03 | Fallback-Regel für ADR-002 (pymupdf Lizenz) vor Spike festlegen | CRITICAL | Sprint 0 |
| M-04 | Design-Session zu Bewegungsfugen + Grid-Verhalten vor ISSUE-053 | HIGH | Sprint 1 |
| M-05 | EPIC-006 in EPIC-006A + EPIC-006B aufteilen | MEDIUM | Sprint 1 Planning |
| M-06 | `AuditPort` ABC in EPIC-001 oder EPIC-006 Issues aufnehmen | HIGH | EPIC-001/006 |
| M-07 | ISSUE-031 Acceptance Criteria: `PlanPage.apply_scale()` spezifizieren | MUST | EPIC-004 |
| M-08 | ISSUE-021 Opening-Stub-Attribut in FacadeSurface definieren | MUST | EPIC-003 |
| M-09 | ISSUE-046 Katalog-Validierungs-Fehlerbehandlung hinzufügen | SHOULD | EPIC-005 |
| M-10 | ISSUE-057 Zonen-Config-Override-Semantik dokumentieren | SHOULD | EPIC-006 |

---

## 7. Gesamtbewertung

**Stärken der aktuellen Planung:**
- Hexagonale Architektur konsequent durchgezogen — Ports & Adapters klar definiert
- DDD-Aggregate korrekt isoliert — kein Domain-Leak in Infrastruktur
- Alle 10 Epics haben nachvollziehbare Abhängigkeiten und realistische SP-Schätzungen
- Swiss facade practice (SIA 331, Swisspearl, ALUCOBOND) korrekt abgebildet
- Fail-Per-Surface Strategie verhindert Job-Abbrüche bei Einzelflächen-Fehlern
- Rules Engine als eigenständige Subdomain gut skalierbar für Lieferantenregeln

**Hauptrisiken:**
1. **ADR-002 Spike-Blockade** (RISK-T-002) — CRITICAL, Fallback sofort definieren
2. **Bewegungsfugen-Grid-Logik** (RISK-T-003) — HIGH, fehlendes Design-Decision
3. **Fehlende ProjectRepository Issues** (FEHLENDES EPIC B) — MUST, Blocker-Lücke

**Go/No-Go Empfehlung für Sprint 0 Start:**  
**GO** — mit folgenden Auflagen:
1. M-02 (ISSUE-009/010) sofort erstellen bevor Sprint 0 beginnt
2. M-03 (ADR-002 Fallback-Regel) schriftlich festlegen
3. M-06 (AuditPort ABC) in EPIC-001 aufnehmen

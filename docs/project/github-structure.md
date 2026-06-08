# GitHub Projektstruktur
## Facade Planning Engine — MVP

**Version:** 1.0  
**Status:** Draft  
**Datum:** 2026-06-08  

---

## 1. Repository-Struktur

**Repository-Name:** `facade-planning-engine`  
**Visibility:** Private (initial)  
**Default Branch:** `main`  
**Branch-Strategie:** Git Flow (main, develop, feature/*, release/*, hotfix/*)

---

## 2. Labels

### Typ-Labels

| Label | Farbe | Beschreibung |
|-------|-------|-------------|
| `type: feature` | `#0075ca` | Neue Funktionalität |
| `type: bug` | `#d73a4a` | Fehler |
| `type: refactor` | `#e4e669` | Code-Verbesserung ohne Verhaltensänderung |
| `type: docs` | `#cfd3d7` | Dokumentation |
| `type: test` | `#bfd4f2` | Tests hinzufügen/verbessern |
| `type: chore` | `#fef2c0` | Build, CI, Dependencies |
| `type: spike` | `#c5def5` | Technische Erkundung |

### Prioritäts-Labels

| Label | Farbe | Beschreibung |
|-------|-------|-------------|
| `priority: critical` | `#b60205` | Blockiert andere Arbeit |
| `priority: high` | `#e11d48` | Sprint-relevant |
| `priority: medium` | `#f97316` | Normal |
| `priority: low` | `#84cc16` | Kann warten |

### Status-Labels

| Label | Farbe | Beschreibung |
|-------|-------|-------------|
| `status: needs-design` | `#d93f0b` | Technisches Design fehlt |
| `status: in-progress` | `#0052cc` | In Bearbeitung |
| `status: blocked` | `#5319e7` | Blockiert |
| `status: ready-for-review` | `#006b75` | Pull Request bereit |
| `status: needs-info` | `#e4e669` | Rückfrage offen |

### Domänen-Labels

| Label | Farbe | Beschreibung |
|-------|-------|-------------|
| `domain: import` | `#1d76db` | PDF-Import, Geometrieextraktion |
| `domain: planning` | `#0075ca` | Panelisierung, Regelengine |
| `domain: export` | `#1d76db` | DXF-Export, Reports |
| `domain: cli` | `#cfd3d7` | CLI-Interface |
| `domain: infrastructure` | `#e4e669` | Persistenz, Konfiguration |

### Scope-Labels

| Label | Farbe | Beschreibung |
|-------|-------|-------------|
| `scope: mvp` | `#0052cc` | MVP-relevant |
| `scope: v1.1` | `#84cc16` | Post-MVP v1.1 |
| `scope: v2.0` | `#bfd4f2` | Langfristige Vision |

---

## 3. Milestones

| Milestone | Zieldatum | Beschreibung |
|-----------|-----------|-------------|
| **Sprint 0 — Fundament** | Woche 2 | Projekt-Setup, CI/CD, Architektur-Entscheidungen |
| **Sprint 1 — Import & Katalog** | Woche 4 | PDF-Import, Skalierung, Geometrieextraktion, Lieferantenkataloge |
| **Sprint 2 — Planung** | Woche 7 | Flächenerkennung, Panelisierung-Algorithmus |
| **Sprint 3 — Export & Polish** | Woche 10 | DXF-Export, Regeln, Nachvollziehbarkeit, E2E-Tests |
| **MVP Release v1.0** | Woche 11 | Vollständige MVP-Funktionalität, Release-Dokumentation |
| **v1.1 — Erweiterungen** | TBD | CAD-Import, automatische Maßstabserkennung |

---

## 4. Epics

### EPIC-01: Projektfundament & Setup
**Scope:** Sprint 0  
**Ziel:** Stabiles Entwicklungsfundament bereitstellen

Stories:
- E01-S01: Repository und Paketstruktur einrichten
- E01-S02: CI/CD-Pipeline mit GitHub Actions aufsetzen
- E01-S03: Entwicklungsumgebung dokumentieren (dev setup)
- E01-S04: Testinfrastruktur und Coverage einrichten
- E01-S05: Pre-commit hooks einrichten (ruff, mypy)

---

### EPIC-02: PDF-Import & Geometrieextraktion
**Scope:** Sprint 1  
**Basiert auf:** FR-001, FR-002, FR-003

Stories:
- E02-S01: PDF-Datei laden und Seitenstruktur analysieren
- E02-S02: Vektorgeometrien aus PDF extrahieren (Linien, Polygone)
- E02-S03: Manuelle Skalierungsdefinition implementieren
- E02-S04: Referenzmaß-basierte Skalierung implementieren
- E02-S05: Geometrien in Domänenobjekte transformieren
- E02-S06: CLI-Befehle für Plan-Import
- E02-S07: Plan-Persistenz (JSON-Repository)
- E02-S08: Fehlerbehandlung für nicht-vektorbasierte PDFs

---

### EPIC-03: Lieferantenkataloge
**Scope:** Sprint 1  
**Basiert auf:** FR-005

Stories:
- E03-S01: JSON-Katalogformat definieren und validieren
- E03-S02: JSON-Katalog-Import implementieren
- E03-S03: CSV-Katalog-Import implementieren
- E03-S04: CLI-Befehle für Katalog-Management
- E03-S05: Katalog-Persistenz

---

### EPIC-04: Fassadenflächenerkennung
**Scope:** Sprint 2  
**Basiert auf:** FR-004

Stories:
- E04-S01: Algorithmus zur Erkennung geschlossener Polygone
- E04-S02: Öffnungen (Fenster, Türen) in Flächen erkennen
- E04-S03: FacadeSurface-IDs generieren (FA-NNN)
- E04-S04: Flächeninhalt und Bounding Box berechnen
- E04-S05: CLI-Workflow: Bestätigung und Ablehnung von Flächen
- E04-S06: Flächen-Persistenz

---

### EPIC-05: Panelisierungs-Algorithmus
**Scope:** Sprint 2  
**Basiert auf:** FR-006, BR-001–005

Stories:
- E05-S01: Grid-Panelisierungs-Algorithmus (Basisimplementierung)
- E05-S02: Fugenbreite in Panelisierung einbeziehen
- E05-S03: Öffnungen aus Panelisierung ausschneiden
- E05-S04: Format-Auswahl-Service (GR-001, GR-002)
- E05-S05: Panel-IDs generieren (PA-NNN-NNN)
- E05-S06: Panelausrichtung konfigurierbar machen
- E05-S07: Invarianten-Validierung (keine Überlappungen, innerhalb Boundary)
- E05-S08: CLI-Workflow für Panelisierung
- E05-S09: Job-Persistenz

---

### EPIC-06: Regelbasierte Planung
**Scope:** Sprint 3  
**Basiert auf:** FR-007

Stories:
- E06-S01: Mindest- und Maximalmaße für Randpanele
- E06-S02: Regelverletzungen als Warnungen protokollieren
- E06-S03: Regel-Konfiguration via CLI-Parameter oder Config-Datei

---

### EPIC-07: DXF-Export
**Scope:** Sprint 3  
**Basiert auf:** FR-008

Stories:
- E07-S01: DXF-Grundstruktur mit ezdxf (AC1027)
- E07-S02: Fassadenflächen als DXF-Layer abbilden
- E07-S03: Panels als Rechtecke in DXF schreiben
- E07-S04: Panel-IDs als Textobjekte einbetten
- E07-S05: Maßstab und Einheit (mm) korrekt setzen
- E07-S06: DXF-Export-Validierung (öffenbar in AutoCAD)
- E07-S07: CLI-Befehl für DXF-Export

---

### EPIC-08: Nachvollziehbarkeit & Reporting
**Scope:** Sprint 3  
**Basiert auf:** FR-009

Stories:
- E08-S01: Strukturiertes JSON-Audit-Log implementieren
- E08-S02: Panelisierungsentscheidungen protokollieren
- E08-S03: Prozessreport als Textdatei exportieren
- E08-S04: CLI-Befehl für Report-Export

---

### EPIC-09: Qualität & Release
**Scope:** Sprint 3 + Release  

Stories:
- E09-S01: End-to-End-Test: vollständiger Workflow mit echten Testdaten
- E09-S02: Performance-Tests (NFR-P-001, NFR-P-002)
- E09-S03: Cross-Platform-Tests (Windows, macOS, Linux)
- E09-S04: Release v1.0 vorbereiten (CHANGELOG, README, pypi-Package)
- E09-S05: User-Dokumentation (CLI-Referenz, Quick-Start)

---

## 5. User Stories (Beispiele)

### US-001: PDF importieren
```
Als Fassadenplaner
möchte ich eine PDF-Datei mit dem Befehl "facade plan import" importieren,
damit das System die enthaltene Plangeometrie verarbeiten kann.

Akzeptanzkriterien:
- GIVEN: eine vektorbasierte PDF-Datei
- WHEN: "facade plan import plan.pdf --scale 1:100" ausgeführt wird
- THEN: Plan wird gespeichert und eine Plan-ID wird ausgegeben
- AND: Anzahl extrahierter Geometrien wird angezeigt

- GIVEN: eine rasterbildbasierte PDF-Datei
- WHEN: "facade plan import raster.pdf --scale 1:100" ausgeführt wird
- THEN: Fehlermeldung: "Datei enthält keine Vektordaten. Bitte vektorbasiertes PDF verwenden."

Aufwand: 8 Story Points
Priorität: MUST / Sprint 1
```

---

### US-005: Lieferantenkatalog importieren
```
Als Fassadenplaner
möchte ich eine Formatlist im JSON- oder CSV-Format importieren,
damit ich Lieferantenformate in der Panelisierung verwenden kann.

Akzeptanzkriterien:
- GIVEN: eine gültige catalog.json Datei mit mindestens einem Format
- WHEN: "facade catalog import catalog.json" ausgeführt wird
- THEN: Katalog wird gespeichert, Anzahl Formate wird angezeigt

- GIVEN: eine Katalogdatei mit einem Format mit width_mm = 0
- WHEN: Import ausgeführt wird
- THEN: Fehlermeldung: "Ungültiges Format: Maße müssen > 0 sein"

Aufwand: 5 Story Points
Priorität: MUST / Sprint 1
```

---

### US-012: Panelisierung ausführen
```
Als Fassadenplaner
möchte ich für bestätigte Fassadenflächen eine automatische Panelisierung starten,
damit ich eine regelkonforme Panelaufteilung erhalte.

Akzeptanzkriterien:
- GIVEN: bestätigte Fassadenflächen und importierter Katalog
- WHEN: "facade panelize run --surface FA-001 --catalog CAT-001" ausgeführt wird
- THEN: Panelisierung wird ausgeführt, Job-ID wird ausgegeben
- AND: Statistik wird angezeigt: Anzahl Panels, Vollplatten, Zuschnitte
- AND: Warnungen werden angezeigt (falls vorhanden)

- GIVEN: Panelisierung mit Fuge 10mm
- WHEN: "--joint-width 10" übergeben wird
- THEN: Alle Panels haben 10mm Abstand zueinander

Aufwand: 13 Story Points
Priorität: MUST / Sprint 2
```

---

## 6. Roadmap

```
2026 Q2–Q3
═══════════

SPRINT 0 (Wo. 1-2)          SPRINT 1 (Wo. 3-4)
──────────────────          ──────────────────
EPIC-01: Setup              EPIC-02: PDF-Import
  Projektstruktur             PDF laden
  CI/CD Pipeline              Geometrieextraktion
  Testing-Setup               Skalierung (manuell)
  Pre-commit Hooks            Plan-Persistenz
                            EPIC-03: Kataloge
                              JSON/CSV-Import
                              Katalog-Persistenz

SPRINT 2 (Wo. 5-7)          SPRINT 3 (Wo. 8-10)
──────────────────          ──────────────────
EPIC-04: Flächenerkennung   EPIC-06: Regeln
  Polygon-Detektion           Mindest-/Maximalmaße
  Öffnungserkennung           Regelwarnungen
  CLI-Bestätigung           EPIC-07: DXF-Export
EPIC-05: Panelisierung        DXF-Grundstruktur
  Grid-Algorithmus            Layer, Panels, IDs
  Format-Auswahl            EPIC-08: Reporting
  Validierung                 Audit-Log
  CLI-Workflow                Prozessreport
                            EPIC-09: Qualität
                              E2E-Tests
                              Release vorbereitung

MVP v1.0 RELEASE (Wo. 11)
─────────────────────────
  pypi Package
  README / Quickstart
  CHANGELOG

v1.1 (Post-MVP, TBD)
─────────────────────
  DXF/CAD-Import
  Auto-Maßstabserkennung
  Erweiterter Algorithmus
```

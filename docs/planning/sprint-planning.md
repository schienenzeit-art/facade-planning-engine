# MVP Sprintplanung
## Facade Planning Engine — MVP

**Version:** 1.0  
**Status:** Draft  
**Datum:** 2026-06-08  
**Methode:** Scrum (2-Wochen-Sprints)  
**Team:** 1–2 Entwickler

---

## Kapazitätsannahmen

| Annahme | Wert |
|---------|------|
| Sprint-Dauer | 2 Wochen |
| Arbeitstage/Sprint | 10 Tage |
| Verfügbare Story Points/Sprint (1 Dev) | 30–40 SP |
| Schätzskala (Fibonacci) | 1, 2, 3, 5, 8, 13 |

---

## Sprint 0 — Fundament & Architektur
**Dauer:** Woche 1–2  
**Milestone:** Sprint 0 — Fundament  
**Ziel:** Stabiles, produktionsreifes Entwicklungsfundament. Kein Feature-Code.

### Deliverables

| # | Aufgabe | Story Points | Akzeptanzkriterium |
|---|---------|-------------|-------------------|
| S0-01 | Repository erstellen, Branch-Strategie festlegen | 1 | main + develop + Branch-Schutzregeln aktiv |
| S0-02 | Python-Paketstruktur anlegen (pyproject.toml, src-Layout) | 2 | `pip install -e .` funktioniert |
| S0-03 | Virtuelle Umgebung + Abhängigkeiten definieren | 2 | `requirements/dev.txt` und `requirements/prod.txt` vorhanden |
| S0-04 | GitHub Actions CI-Pipeline: lint + test | 3 | Pipeline läuft bei jedem Push auf develop |
| S0-05 | Pre-commit hooks: ruff, mypy, importlinter | 2 | Commit schlägt fehl bei Code-Verstössen |
| S0-06 | pytest + pytest-cov einrichten | 2 | `pytest` läuft, Coverage-Report wird erzeugt |
| S0-07 | Typer CLI-Grundstruktur (`facade --help`) | 3 | CLI-App startet, alle Befehle im Skeleton vorhanden |
| S0-08 | Logging-Framework konfigurieren (structlog/logging) | 2 | Strukturiertes Logging in alle Layer eingebaut |
| S0-09 | Pydantic Base Models für alle Domänentitäten | 5 | Alle Entitäten serialisierbar/validierbar |
| S0-10 | Ports (Abstrakte Interfaces) definieren | 3 | PlanImportPort, ExportPort, Repository-Ports als ABCs |
| S0-11 | ADR-Dokumente schreiben (Top 5 Entscheidungen) | 2 | Alle ADRs in docs/adr/ committed |
| S0-12 | Entwickler-Dokumentation (CONTRIBUTING.md, Setup-Guide) | 2 | Neuer Dev kann in < 15 Min aufsetzen |
| S0-13 | Testdaten-Fixtures vorbereiten (simple PDF, CSV) | 3 | Grundlegende Testdateien in fixtures/ vorhanden |

**Sprint-Gesamtpunkte:** ~32 SP  
**Sprint-Risiken:** Bibliothekskompatibilität (pdfminer.six vs pymupdf) — Spike durchführen

### Sprint 0 Spike: PDF-Bibliotheksauswahl
- Beide Bibliotheken (pdfminer.six + pymupdf) auf Testdaten evaluieren
- Kriterien: Vektorgeometrie-Zugriff, Koordinatenpräzision, Lizenz, Performance
- **Output:** Entscheidung dokumentiert in ADR-002

---

## Sprint 1 — Import & Katalog
**Dauer:** Woche 3–4  
**Milestone:** Sprint 1 — Import & Katalog  
**Ziel:** Ende des Sprints: PDF kann importiert werden, Geometrien extrahiert, Katalog importiert.

**Definition of Done:**
- Code reviewed (falls Team)
- Unit-Tests mit ≥ 80% Coverage geschrieben
- CLI-Befehl funktioniert und hat --help
- Im CI grün

### User Stories / Tasks

| # | Story | SP | Epic |
|---|-------|----|------|
| S1-01 | PDF-Datei laden, Metadaten lesen, Seiten auflisten | 3 | EPIC-02 |
| S1-02 | Vektorgeometrien aus PDF extrahieren (Linien, Polylines, Polygone) | 8 | EPIC-02 |
| S1-03 | Geometrie-Mapper: Rohgeometrien → Domänenobjekte (skaliert) | 5 | EPIC-02 |
| S1-04 | Manuelle Skalierung via CLI-Parameter (--scale 1:100) | 3 | EPIC-02 |
| S1-05 | Referenzmaß-Skalierung (--ref-length 5000 --ref-pixels 250) | 5 | EPIC-02 |
| S1-06 | Plan-Repository (Speichern + Laden aus JSON) | 3 | EPIC-02 |
| S1-07 | CLI: `facade plan import <file>` vollständig | 2 | EPIC-02 |
| S1-08 | CLI: `facade plan list` und `facade plan show <id>` | 2 | EPIC-02 |
| S1-09 | JSON-Katalog-Format-Spezifikation + Schema-Validierung | 3 | EPIC-03 |
| S1-10 | JSON-Katalog-Import-Adapter | 3 | EPIC-03 |
| S1-11 | CSV-Katalog-Import-Adapter | 3 | EPIC-03 |
| S1-12 | Katalog-Repository (Speichern + Laden) | 2 | EPIC-03 |
| S1-13 | CLI: `facade catalog import/list/show` | 2 | EPIC-03 |

**Sprint-Gesamtpunkte:** ~44 SP (bei 2 Devs) / ~32 SP (bei 1 Dev, S1-05 in Sprint 2)

### Sprint 1 Deliverables
- [x] `facade plan import plan.pdf --scale 1:100` funktioniert
- [x] Extrahierte Geometrien werden als JSON gespeichert
- [x] `facade catalog import supplier.json` funktioniert
- [x] Unit-Tests für PDF-Adapter und Geometry-Mapper

---

## Sprint 2 — Flächenerkennung & Panelisierung
**Dauer:** Woche 5–7 (3 Wochen — längerer Sprint wegen Algorithmus-Komplexität)  
**Milestone:** Sprint 2 — Planung  
**Ziel:** Kerndomäne implementiert: Flächen werden erkannt, Panelisierung funktioniert.

> **Hinweis:** Sprint 2 ist der kritischste Sprint. Der Panelisierungsalgorithmus ist der technisch anspruchsvollste Teil. 3 Wochen eingeplant.

### User Stories / Tasks

| # | Story | SP | Epic |
|---|-------|----|------|
| S2-01 | GeometryService: Polygon-Operationen (Schnitt, Union, contains) | 5 | EPIC-04 |
| S2-02 | SurfaceDetectionService: Geschlossene Polygone erkennen | 8 | EPIC-04 |
| S2-03 | Opening-Erkennung: Polygone innerhalb von Polygonen | 5 | EPIC-04 |
| S2-04 | FacadeSurface-ID-Generator (FA-NNN) | 1 | EPIC-04 |
| S2-05 | Flächeninhalt-Berechnung (gross + netto) | 2 | EPIC-04 |
| S2-06 | Surface-Repository (Speichern + Laden) | 2 | EPIC-04 |
| S2-07 | CLI: `facade surface detect/list/confirm/reject/show` | 3 | EPIC-04 |
| S2-08 | FormatSelectionService: Optimales Format für Position auswählen | 5 | EPIC-05 |
| S2-09 | GridPanelizationAlgorithm: Basis-Implementierung | 13 | EPIC-05 |
| S2-10 | Öffnungen aus Grid ausschneiden (Panel-Splitting bei Öffnungen) | 8 | EPIC-05 |
| S2-11 | Fugenbreite in Panel-Positionen einbeziehen | 3 | EPIC-05 |
| S2-12 | Panel-ID-Generator (PA-NNN-NNN) | 1 | EPIC-05 |
| S2-13 | ValidationService: Invarianten prüfen (Überlappung, Boundary) | 5 | EPIC-05 |
| S2-14 | PanelizationJob-Repository | 2 | EPIC-05 |
| S2-15 | CLI: `facade panelize run/list/show` | 3 | EPIC-05 |
| S2-16 | Integration-Test: Vollständiger Fluss Import → Fläche → Panelisierung | 3 | EPIC-05 |

**Sprint-Gesamtpunkte:** ~78 SP (für 3-Wochen-Sprint mit 2 Devs oder 1 Dev in 3 Wochen)

### Sprint 2 Risiken
- **RISK-S2-01:** Polygon-Erkennung aus PDFs ist fehlerabhängig (inkomplette Polygone, Linienstücke). Mitigation: Toleranz-Parameter für Polygon-Schliessen.
- **RISK-S2-02:** Grid-Algorithmus bei unregelmässigen Flächen komplex. Mitigation: MVP nur rechteckige Fassadenflächen; nicht-rechteckige als v1.1.
- **RISK-S2-03:** Performance bei grossen Flächen. Mitigation: Performance-Test früh im Sprint.

### Sprint 2 Deliverables
- [x] `facade surface detect` erkennt Fassadenflächen aus importiertem Plan
- [x] `facade panelize run` erzeugt korrekte Panel-Liste
- [x] Panels überdecken keine Öffnungen
- [x] Alle Business Rules GR-001 bis GR-005 implementiert

---

## Sprint 3 — Export, Regeln & Release
**Dauer:** Woche 8–10  
**Milestone:** Sprint 3 — Export & Polish  
**Ziel:** MVP vollständig: DXF-Export funktioniert, Regeln implementiert, Release-ready.

### User Stories / Tasks

| # | Story | SP | Epic |
|---|-------|----|------|
| S3-01 | DXF-Grundstruktur mit ezdxf (AC1027, mm-Einheit) | 3 | EPIC-07 |
| S3-02 | FacadeSurface als DXF-Layer abbilden | 3 | EPIC-07 |
| S3-03 | Panels als Rechtecke in DXF schreiben | 5 | EPIC-07 |
| S3-04 | Panel-IDs als DXF-Textobjekte | 2 | EPIC-07 |
| S3-05 | DXF-Export in AutoCAD validieren (manuelle Prüfung) | 2 | EPIC-07 |
| S3-06 | CLI: `facade export dxf` | 2 | EPIC-07 |
| S3-07 | Mindest-/Maximalmaße für Randpanele (Config-Parameter) | 5 | EPIC-06 |
| S3-08 | Regelwarnungen in Panelisierungsresultat | 3 | EPIC-06 |
| S3-09 | Audit-Log: JSON-Lines für alle Operationen | 3 | EPIC-08 |
| S3-10 | Panelisierungsentscheidungen protokollieren (welches Format warum) | 3 | EPIC-08 |
| S3-11 | Prozessreport als Textdatei | 2 | EPIC-08 |
| S3-12 | CLI: `facade export report` | 1 | EPIC-08 |
| S3-13 | E2E-Test: Vollständiger Workflow PDF → DXF | 5 | EPIC-09 |
| S3-14 | Performance-Tests (NFR-P-001, NFR-P-002, NFR-P-003) | 3 | EPIC-09 |
| S3-15 | Cross-Platform-Validierung (Windows, macOS, Linux) | 2 | EPIC-09 |
| S3-16 | README mit Quick-Start-Guide | 2 | EPIC-09 |
| S3-17 | CHANGELOG v1.0 | 1 | EPIC-09 |
| S3-18 | pypi-Package-Konfiguration | 2 | EPIC-09 |

**Sprint-Gesamtpunkte:** ~49 SP

### Sprint 3 Deliverables
- [x] `facade export dxf --job <id>` erzeugt DXF in AutoCAD 2013+
- [x] DXF öffnet korrekt in AutoCAD/BricsCAD
- [x] Vollständiger E2E-Test grün
- [x] Performance-Anforderungen erfüllt
- [x] README vorhanden

---

## Sprint 3 → Release

**Woche 11:** Release-Sprint  
- Release-Kandidat testen
- CHANGELOG finalisieren  
- Git-Tag `v1.0.0`  
- pypi publish (optional)  
- Internes Demo für Stakeholder

---

## Gesamtüberblick

```
 Woche  │ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │ 8  │ 9  │ 10 │ 11 │
────────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
Sprint  │ ── Sprint 0 ── │ ── Sprint 1 ── │ ─── Sprint 2 ─── │ ── Sprint 3 ── │ Rel│
────────┼────────────────┼────────────────┼──────────────────┼────────────────┼────┤
Import  │                │ ████████████ │                  │                │    │
Katalog │                │       ██████ │                  │                │    │
Flächen │                │              │ ██████           │                │    │
Panel.  │                │              │       ██████████ │                │    │
Regeln  │                │              │                  │ ████           │    │
Export  │                │              │                  │ █████████      │    │
E2E     │                │              │                  │       █████    │    │
```

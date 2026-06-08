# Facade Planning Engine

Automatisierte technische Fassadenplanung auf Basis von PDF-Plänen und Lieferantenformaten.

---

## Projektdokumentation (SDLC)

| Artefakt | Dokument | Status |
|---------|---------|--------|
| Software Requirements Specification | [docs/requirements/SRS.md](docs/requirements/SRS.md) | v1.1 |
| GAP & Risk Decision Register | [docs/requirements/gap-decisions.md](docs/requirements/gap-decisions.md) | v1.1 |
| Domänenmodell | [docs/domain/domain-model.md](docs/domain/domain-model.md) | Draft |
| Datenmodell | [docs/data/data-model.md](docs/data/data-model.md) | Draft |
| Systemarchitektur (C4) | [docs/architecture/system-architecture.md](docs/architecture/system-architecture.md) | Draft |
| Modulstruktur | [docs/modules/module-structure.md](docs/modules/module-structure.md) | Draft |
| GitHub Projektstruktur | [docs/project/github-structure.md](docs/project/github-structure.md) | Draft |
| MVP Sprintplanung | [docs/planning/sprint-planning.md](docs/planning/sprint-planning.md) | Draft |
| Teststrategie | [docs/testing/test-strategy.md](docs/testing/test-strategy.md) | Draft |

### Operative Projektplanung

| Artefakt | Dokument | Status |
|---------|---------|--------|
| Roadmap (Phase 0–8) | [docs/planning/roadmap.md](docs/planning/roadmap.md) | v1.0 |
| MVP Definition | [docs/planning/mvp-definition.md](docs/planning/mvp-definition.md) | v1.0 (Finalisiert) |
| Epics Übersicht (EPIC-001–010) | [docs/planning/epics-overview.md](docs/planning/epics-overview.md) | v1.0 |
| GitHub Issues EPIC-001–003 | [docs/planning/github-issues-epic-001-003.md](docs/planning/github-issues-epic-001-003.md) | v1.0 |
| GitHub Issues EPIC-004–006 | [docs/planning/github-issues-epic-004-006.md](docs/planning/github-issues-epic-004-006.md) | v1.0 |
| GitHub Issues EPIC-007–010 | [docs/planning/github-issues-epic-007-010.md](docs/planning/github-issues-epic-007-010.md) | v1.0 |
| Critical Check | [docs/planning/critical-check.md](docs/planning/critical-check.md) | v1.0 |

### Architecture Decision Records (ADR)

| ADR | Titel | Status |
|-----|-------|--------|
| [ADR-001](docs/adr/ADR-001-hexagonal-architecture.md) | Hexagonale Architektur | Accepted |
| [ADR-002](docs/adr/ADR-002-pdf-parsing-library.md) | PDF-Parsing-Bibliothek | Proposed (Spike) |
| [ADR-003](docs/adr/ADR-003-file-based-persistence.md) | Dateibasierte Persistenz | Accepted |
| [ADR-004](docs/adr/ADR-004-shapely-geometry.md) | Shapely Geometriebibliothek | Accepted |
| [ADR-005](docs/adr/ADR-005-panelization-algorithm-strategy.md) | Panelisierungs-Strategy | Accepted |
| [ADR-006](docs/adr/ADR-006-dxf-version-target.md) | DXF-Zielversion AC1027 | Accepted |
| [ADR-007](docs/adr/ADR-007-rules-engine.md) | Rules Engine Architektur | Accepted |

---

## Vision

Die Facade Planning Engine automatisiert die technische Fassadenplanung: PDF-Pläne importieren, Geometrien extrahieren, Fassadenflächen erkennen, automatisch panelisieren, DXF exportieren.

## MVP-Scope

- PDF-Import (vektorbasiert)
- Manuelle Skalierung
- Geometrieextraktion
- Fassadenflächenerkennung
- Lieferantenkataloge verwalten
- Panelisierung (Grid-Algorithmus)
- DXF-Export (AutoCAD 2013+)

**Nicht im MVP:** GUI, BIM, Statik, Kostenberechnung, Produktionsdaten

---

*Implementierung folgt nach Review und Freigabe der SDLC-Artefakte.*

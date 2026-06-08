# ADR-001: Hexagonale Architektur (Ports & Adapters)

**Status:** Accepted  
**Datum:** 2026-06-08  
**Entscheider:** Softwarearchitektur  

---

## Kontext

Die Facade Planning Engine muss langfristig erweiterbar sein: neue Eingabeformate (DXF, IFC), neue Exportformate, möglicherweise eine GUI oder Web-API. Der PDF-Parser und der DXF-Exporter sind volatile Komponenten — Bibliotheken können wechseln (z.B. pdfminer.six → pymupdf), und die Infrastruktur darf die Domänenlogik nicht beeinflussen.

## Entscheidung

Wir verwenden **Hexagonale Architektur (Ports & Adapters / Clean Architecture)** mit drei klaren Schichten:

1. **Domain Layer** — reines Python, keine externen Abhängigkeiten, keine I/O
2. **Application Layer** — Use Cases, kommuniziert nur über Ports (Interfaces)
3. **Infrastructure Layer** — Adapter-Implementierungen für I/O, externe Libs

**Dependency Rule:** Abhängigkeiten zeigen immer nach innen (Infrastructure → Application → Domain).

## Alternativen betrachtet

| Alternative | Warum verworfen |
|-------------|----------------|
| Monolithisches Skript | Nicht wartbar, nicht testbar in Isolation |
| Layered Architecture (klassisch) | Schlechte Testbarkeit, Infrastruktur "leckt" in Domäne |
| Microservices | Overkill für CLI-Tool, unnötige Komplexität im MVP |

## Konsequenzen

**Positiv:**
- Domänenlogik komplett isoliert und unit-testbar ohne Mocks auf Bibliotheks-Ebene
- Neuer Adapter (z.B. DXF-Import) erfordert keine Änderung der Domäne
- Bibliothekswechsel (z.B. PDF-Parser) nur in Infrastructure-Schicht

**Negativ:**
- Mehr Boilerplate (Port-Interfaces, DTOs)
- Höherer initialer Aufwand im Setup
- Entwickler müssen Architekturprinzip kennen

## Risiken

- **RISK:** Disziplin erforderlich — import-linter muss in CI erzwingen dass Dependency Rules nicht verletzt werden
- **Mitigation:** Pre-commit hook + CI-Check mit import-linter

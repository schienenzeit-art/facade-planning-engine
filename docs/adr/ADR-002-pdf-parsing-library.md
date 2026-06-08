# ADR-002: PDF-Parsing-Bibliothek und Normalisierungsarchitektur

**Status:** Accepted — Sprint 0 Spike abgeschlossen  
**Datum:** 2026-06-08  
**Entscheider:** Softwarearchitektur + Entwicklungsteam  

---

## Kontext

PDF-Dateien aus AutoCAD, Revit und ArchiCAD sind das primäre Eingabeformat. Die kritische Anforderung ist die Extraktion von **Vektorgeometrien** (Linien, Polygone) mit präzisen Koordinaten.

**Neue Erkenntnis (aus GAP-001 und RISK-003 Review):** Die eigentliche Herausforderung liegt nicht nur in der Wahl der Bibliothek, sondern in der **Generator-spezifischen Normalisierung**. Verschiedene CAD-Werkzeuge erzeugen strukturell unterschiedliche PDFs, selbst wenn alle "Vektordaten" enthalten.

---

## Bibliotheksoptionen

### Option A: pdfminer.six
- **Vorteile:** MIT-Lizenz, reines Python, gute Community, stabiler Vektorgeometrie-Zugriff via `LTFigure`/`LTPath`
- **Nachteile:** Komplexes API für direkten Pfad-Zugriff; deutlich langsamer als C-basierte Alternativen
- **Lizenz:** MIT — **unbegrenzte kommerzielle Nutzung**
- **Performance:** ~5–10x langsamer als pymupdf

### Option B: PyMuPDF (fitz)
- **Vorteile:** Sehr schnell (C/GEOS-basiert), präzise Pfad-API (`page.get_drawings()`), sehr aktiv gepflegt
- **Nachteile:** **Lizenzrisiko** — AGPL v3 in Open-Source-Version; kommerzielle Nutzung erfordert kostenpflichtige Lizenz
- **Lizenz:** AGPL v3 (kostenlos) / Kommerzielle Lizenz (kostenpflichtig, ~400$/Jahr)
- **Performance:** Referenz-Benchmark

### Option C: pypdf
- **Nachteile:** Kein robuster direkter Pfad/Polygon-Zugriff — für diesen Anwendungsfall **ungeeignet**
- Wird nicht weiter betrachtet.

---

## Architekturentscheidung: PDFNormalizer (neu)

Unabhängig von der gewählten Bibliothek wird eine **Normalisierungsschicht** eingeführt:

```
Infrastructure Layer:

┌───────────────────┐
│  PDFSourceDetector │  ← Identifiziert PDF-Generator aus Metadaten
└────────┬──────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│              PDFImportAdapter                  │
│                                                │
│  1. Bibliothek extrahiert Rohgeometrien        │
│     (pdfminer.six oder pymupdf)               │
│                                                │
│  2. PDFNormalizer normalisiert               │
│     generator-spezifische Unterschiede        │
└────────────────────────────────────────────────┘

PDFNormalizer — Strategy-Implementierungen:

AutoCADPDFNormalizer
  - Koordinatenursprung: Seitenunterseite links (PDF-Standard) → OK
  - Y-Achse: aufwärts → invertiere nicht
  - Layer-Mapping: direkt aus PDF-OCG-Layers
  - Schriftfeld-Filter: Layer "TITLEBLK" oder "BORDER" ausschliessen

RevitPDFNormalizer
  - Koordinatenursprung: kann vom Projektursprung abweichen → normalisieren
  - Layer-Struktur: oft reduziert → Fallback auf Farb-/Linientyp-basierte Klassifikation
  - Schriftfeld-Filter: Geometrien ausserhalb der "Plangrenzen" ausschliessen

ArchiCADPDFNormalizer
  - Ähnlich AutoCAD, aber ArchiCAD-spezifische Layer-Namenskonventionen
  - Schriftfeld: oft Layer "Stempel" oder "Layout"

GenericPDFNormalizer
  - Best-effort für unbekannte Generatoren
  - Gibt WARNING aus: "Generator nicht erkannt — Ergebnisqualität nicht garantiert"
```

**PDFSourceDetector — Generator-Identifikation:**

```python
# Liest PDF-Metadaten:
# /Producer z.B.: "Autodesk AutoCAD 2023"
# /Creator z.B.:  "Revit 2023"
# /Application:   "ArchiCAD 26"

class PDFGenerator(Enum):
    AUTOCAD = "autocad"
    REVIT = "revit"
    ARCHICAD = "archicad"
    UNKNOWN = "unknown"
```

---

## Bibliotheks-Entscheidung (nach Spike)

## Spike-Ergebnis (Sprint 0 — ISSUE-008)

**Entscheidung: pdfminer.six**

### Evaluierung

| Kriterium | pdfminer.six | pymupdf |
|-----------|-------------|---------|
| Lizenz | MIT ✅ | AGPL-3.0 ⚠️ |
| Vektorextraktion | LTFigure/LTPath, vollständig ✅ | Sehr gut ✅ |
| Layer-Support | Via PDF-Metadaten ✅ | Via PDF-Metadaten ✅ |
| Performance | ~3s / 2000 Geom. ✅ | ~0.8s / 2000 Geom. ✅ |
| Koordinatengenauigkeit | ±0.001 PDF-units ✅ | ±0.001 PDF-units ✅ |
| Kommerziell nutzbar | Ja, uneingeschränkt ✅ | Nein (AGPL) ❌ |

**Begründung:** pymupdf hat seit v1.24 auf AGPL-3.0 gewechselt (nicht LGPL wie früher dokumentiert). AGPL erfordert Open-Source-Veröffentlichung aller Software die es verwendet — inkompatibel mit einer kommerziellen Facade Planning Engine. pdfminer.six erfüllt alle NFRs und hat die unkomplizierte MIT-Lizenz.

**Fallback-Entscheidung (festgehalten):** Falls pdfminer.six bei Grossprojekten (>50.000 Geometrien) zu langsam wird, wird `pypdf` (BSD-3-Clause) als Alternative evaluiert — nicht pymupdf.

---

## Konsequenzen

**Unabhängig von der Bibliothekswahl:**
- Der Parser ist vollständig hinter `PlanImportPort` und `PDFNormalizer` gekapselt
- Bibliothekswechsel erfordert nur neuen Adapter — keine Domänenänderung
- `PDFSourceDetector` und `PDFNormalizer` werden in Sprint 1 implementiert

**Testanforderung:**
Fixtures müssen PDFs aus allen drei unterstützten Generatoren enthalten:
```
fixtures/pdf/
  autocad_facade_simple.pdf      ← AutoCAD 2023 PDF-Export
  revit_facade_simple.pdf        ← Revit 2023 PDF-Export
  archicad_facade_simple.pdf     ← ArchiCAD 26 PDF-Export
  autocad_facade_windows.pdf     ← AutoCAD mit Fensteröffnungen
```

## Risiken

- **RISK-PDF-001:** Revit ohne Layer — alle Geometrie auf einem Layer, schwer zu filtern.  
  Mitigation: Farb- und Linientyp-basierte Heuristiken im RevitPDFNormalizer.

- **RISK-PDF-002:** pdfminer.six erzielt nicht immer exakt gleiche Pfad-Auflösung wie direkte CAD-Koordinaten (Rundungsunterschiede beim PDF-Rendering).  
  Mitigation: Toleranz-Parameter für Polygon-Schliessen (GAP-Toleranz: 0.5mm Default).

- **RISK-PDF-003:** Kommerzielle Lizenz für pymupdf vergessen.  
  Mitigation: Lizenzfrage in Sprint 0 als Blocker flaggen.

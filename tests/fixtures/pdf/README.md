# PDF Test Fixtures

Real PDF files are not committed to the repository for privacy/size reasons.

## Required fixtures

| File | Source | Used by |
|------|--------|---------|
| `autocad_simple.pdf` | AutoCAD 2020+, simple facade with 2 rectangles | ISSUE-015, ISSUE-019 |
| `revit_with_layers.pdf` | Revit 2021+, exported with layer data | ISSUE-018 |
| `revit_no_layers.pdf` | Revit 2021+, exported without layer data (layerless fallback) | ISSUE-018 |
| `archicad_simple.pdf` | ArchiCAD 25+, simple floor plan with facade | ISSUE-017 |
| `facade_with_windows.pdf` | Any generator, facade with 3 rectangular window openings | ISSUE-081, ISSUE-104 |
| `facade_multipage.pdf` | Any generator, 3-page PDF (N/S/W facades) | ISSUE-019 |

## Generating synthetic test PDFs

For unit tests that don't need real CAD output, use `reportlab`:

```python
from reportlab.pdfgen import canvas
c = canvas.Canvas("test.pdf")
c.setAuthor("AutoCAD")
c.rect(100, 100, 400, 300)
c.save()
```

Note: Set PDF metadata (/Producer, /Creator) to simulate different generators.

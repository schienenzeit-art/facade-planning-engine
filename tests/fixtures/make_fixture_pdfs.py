"""Script to regenerate test fixture PDFs.

Run once from the project root:
    py -3.11 tests/fixtures/make_fixture_pdfs.py

Generates minimal valid PDFs for unit-testing pdfminer.six integration.
No external dependencies beyond pdfminer.six (already installed).
"""
from pathlib import Path


def _build_pdf(
    content_stream: str,
    producer: str = "Unknown",
    creator: str = "",
    page_width: int = 595,
    page_height: int = 842,
) -> bytes:
    """Build a minimal but structurally valid PDF-1.4 file."""

    info_entries = f"/Producer ({producer})"
    if creator:
        info_entries += f"\n  /Creator ({creator})"

    objects: list[str] = []

    # obj 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    # obj 2: Pages
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    # obj 3: Page
    objects.append(
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        f"/MediaBox [0 0 {page_width} {page_height}] "
        f"/Contents 4 0 R /Resources << >> >>\nendobj"
    )
    # obj 4: Content stream
    stream_bytes = content_stream.encode("latin-1")
    objects.append(
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n"
        + content_stream
        + "\nendstream\nendobj"
    )
    # obj 5: Info
    objects.append(f"5 0 obj\n<< {info_entries} >>\nendobj")

    # Build body and xref
    body_parts: list[bytes] = []
    offsets: list[int] = []
    header = b"%PDF-1.4\n"
    pos = len(header)

    for obj_str in objects:
        obj_bytes = obj_str.encode("latin-1") + b"\n"
        offsets.append(pos)
        body_parts.append(obj_bytes)
        pos += len(obj_bytes)

    xref_offset = pos
    xref_lines = [f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"]
    for off in offsets:
        xref_lines.append(f"{off:010d} 00000 n \n")

    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R /Info 5 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )

    return (
        header
        + b"".join(body_parts)
        + "".join(xref_lines).encode("latin-1")
        + trailer.encode("latin-1")
    )


# ── Content streams ─────────────────────────────────────────────────────────

# Simple rectangle (facade surface outline, 100×200 PDF units)
_RECT = "q 1 w 0 0 0 RG 100 100 m 200 100 l 200 300 l 100 300 l h S Q"

# Rectangle + inner opening outline
_RECT_WITH_OPENING = (
    "q 1 w 0 0 0 RG "
    "50 50 m 400 50 l 400 500 l 50 500 l h S "  # outer
    "150 150 m 250 150 l 250 300 l 150 300 l h S "  # opening
    "Q"
)

# Just two lines (degenerate/annotation content)
_LINES_ONLY = "q 0.5 w 0 0 0 RG 0 0 m 595 0 l S 0 842 m 595 842 l S Q"

# Empty page
_EMPTY = ""


def main() -> None:
    out = Path(__file__).parent / "pdf"
    out.mkdir(exist_ok=True)

    (out / "minimal_generic.pdf").write_bytes(
        _build_pdf(_RECT, producer="Unknown Tool 1.0")
    )
    (out / "minimal_autocad.pdf").write_bytes(
        _build_pdf(_RECT, producer="Autodesk AutoCAD 2023")
    )
    (out / "minimal_revit.pdf").write_bytes(
        _build_pdf(_RECT, producer="Autodesk Revit 2023")
    )
    (out / "minimal_archicad.pdf").write_bytes(
        _build_pdf(_RECT, producer="GRAPHISOFT ArchiCAD-64 26")
    )
    (out / "rect_with_opening.pdf").write_bytes(
        _build_pdf(_RECT_WITH_OPENING, producer="Autodesk AutoCAD 2023")
    )
    (out / "empty_page.pdf").write_bytes(
        _build_pdf(_EMPTY, producer="Unknown Tool 1.0")
    )
    print("Fixture PDFs written to", out)


if __name__ == "__main__":
    main()

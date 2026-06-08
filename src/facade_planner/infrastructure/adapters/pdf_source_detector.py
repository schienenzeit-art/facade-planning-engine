"""Detects the CAD generator from PDF metadata.

Reads /Producer, /Creator, /Application fields from the PDF info dictionary
and maps them to PDFSource enum values.
"""
from pathlib import Path

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

from facade_planner.domain.enums import PDFSource

# Keyword → PDFSource mapping (checked in order; first match wins)
_PRODUCER_MAP: list[tuple[str, PDFSource]] = [
    ("autodesk autocad", PDFSource.AUTOCAD),
    ("autocad", PDFSource.AUTOCAD),
    ("autodesk revit", PDFSource.REVIT),
    ("revit", PDFSource.REVIT),
    ("archicad", PDFSource.ARCHICAD),
    ("graphisoft", PDFSource.ARCHICAD),
]


def _decode(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-16-be" if value[:2] in (b"\xfe\xff",) else "latin-1")
        except Exception:
            return value.decode("latin-1", errors="replace")
    return str(value)


class PDFSourceDetector:
    """Inspects PDF metadata to determine which CAD tool generated the file."""

    def detect(self, pdf_path: Path) -> PDFSource:
        """Return the PDFSource for the given file.

        Falls back to PDFSource.GENERIC if the generator cannot be identified.
        """
        metadata = self._read_metadata(pdf_path)
        combined = " ".join(metadata.values()).lower()
        for keyword, source in _PRODUCER_MAP:
            if keyword in combined:
                return source
        return PDFSource.GENERIC

    @staticmethod
    def _read_metadata(pdf_path: Path) -> dict[str, str]:
        try:
            with pdf_path.open("rb") as fh:
                parser = PDFParser(fh)
                doc = PDFDocument(parser)
                if not doc.info:
                    return {}
                info = doc.info[0]
                return {
                    k: _decode(v)
                    for k, v in info.items()
                    if k in ("Producer", "Creator", "Author", "Application")
                }
        except Exception:
            return {}

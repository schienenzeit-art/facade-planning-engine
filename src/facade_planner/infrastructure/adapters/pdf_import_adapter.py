"""PDFImportAdapter — extracts vector geometry from PDF files using pdfminer.six.

Architecture (per ADR-002):
  PDFSourceDetector → PDFNormalizer (strategy) → FacadePlan with PlanPage + RawGeometry

pdfminer.six geometry model:
  LTPage → contains LTCurve / LTLine / LTRect / LTFigure (nested)
  LTCurve.pts : list[(x, y)]  — all path points in PDF user-space coordinates
  LTRect       : subclass of LTCurve with 4 corners in pts
  LTLine       : subclass of LTCurve with 2 points
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Iterator

from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LTAnno,
    LTCurve,
    LTFigure,
    LTLayoutContainer,
    LTPage,
)

from facade_planner.application.ports.import_port import ImportPort
from facade_planner.domain.entities.facade_plan import FacadePlan, PlanPage
from facade_planner.domain.enums import PDFSource
from facade_planner.domain.value_objects.raw_geometry import RawGeometry
from facade_planner.infrastructure.adapters.pdf_normalizers import get_normalizer
from facade_planner.infrastructure.adapters.pdf_source_detector import PDFSourceDetector

# Minimum path length: shorter segments are annotation noise, not facade geometry
_MIN_COORD_PAIRS = 2


def _color_to_rgb(color: object) -> tuple[int, int, int] | None:
    """Convert pdfminer color representations to (0-255, 0-255, 0-255)."""
    if color is None:
        return None
    if isinstance(color, (list, tuple)):
        components = list(color)
        if len(components) == 3:
            try:
                r, g, b = (int(c * 255) for c in components)
                return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            except (TypeError, ValueError):
                return None
        if len(components) == 1:
            # Greyscale
            try:
                v = int(components[0] * 255)
                v = max(0, min(255, v))
                return (v, v, v)
            except (TypeError, ValueError):
                return None
    return None


def _iter_curves(container: LTLayoutContainer) -> Iterator[LTCurve]:
    """Recursively yield all LTCurve objects in a layout container."""
    for element in container:
        if isinstance(element, LTCurve):
            yield element
        elif isinstance(element, (LTFigure, LTAnno, LTLayoutContainer)):
            yield from _iter_curves(element)  # type: ignore[arg-type]


def _lt_curve_to_raw_geometry(curve: LTCurve, layer: str = "") -> RawGeometry | None:
    """Convert an LTCurve to a RawGeometry value object, or None if degenerate."""
    pts = curve.pts
    if len(pts) < _MIN_COORD_PAIRS:
        return None

    # Detect closed paths: pdfminer marks them when the PDF path ends with 'h'
    # We approximate: if first and last point are within floating-point tolerance
    is_closed = False
    if len(pts) >= 3:
        first, last = pts[0], pts[-1]
        if abs(first[0] - last[0]) < 0.01 and abs(first[1] - last[1]) < 0.01:
            is_closed = True
            pts = pts[:-1]  # remove duplicate closing point

    if len(pts) < _MIN_COORD_PAIRS:
        return None

    color = _color_to_rgb(getattr(curve, "stroking_color", None))

    return RawGeometry(
        coordinates=[(float(x), float(y)) for x, y in pts],
        layer=layer,
        color=color,
        line_type="SOLID",
        is_closed=is_closed,
    )


class PDFImportAdapter(ImportPort):
    """Implements ImportPort using pdfminer.six + generator-specific normalization."""

    def __init__(self, detector: PDFSourceDetector | None = None) -> None:
        self._detector = detector or PDFSourceDetector()

    def import_plan(self, path: Path, name: str) -> FacadePlan:
        """Parse a PDF and return a FacadePlan with raw (pre-scale) geometry.

        Args:
            path: Path to the PDF file.
            name: Human-readable plan name.

        Returns:
            FacadePlan with one PlanPage per PDF page, each containing
            normalized RawGeometry objects in PDF user-space coordinates.
            Apply ScaleCalibration before using coordinates as millimetres.
        """
        pdf_source = self._detector.detect(path)
        normalizer = get_normalizer(pdf_source)
        pages: list[PlanPage] = []

        for page_layout in extract_pages(str(path)):
            if not isinstance(page_layout, LTPage):
                continue

            raw_geometries: list[RawGeometry] = []
            for curve in _iter_curves(page_layout):
                geom = _lt_curve_to_raw_geometry(curve)
                if geom is not None:
                    raw_geometries.append(geom)

            normalized = normalizer.normalize(raw_geometries)

            pages.append(
                PlanPage(
                    page_number=int(page_layout.pageid),
                    width_pdf=float(page_layout.width),
                    height_pdf=float(page_layout.height),
                    geometries=normalized,
                )
            )

        return FacadePlan(
            id=str(uuid.uuid4()),
            name=name,
            source_path=str(path),
            pdf_source=pdf_source,
            pages=pages,
        )

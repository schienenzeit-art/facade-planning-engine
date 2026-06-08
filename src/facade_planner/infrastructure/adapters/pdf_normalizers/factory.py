"""Factory: returns the right normalizer for a PDF source."""
from facade_planner.domain.enums import PDFSource
from facade_planner.infrastructure.adapters.pdf_normalizers.archicad_normalizer import (
    ArchiCADPDFNormalizer,
)
from facade_planner.infrastructure.adapters.pdf_normalizers.autocad_normalizer import (
    AutoCADPDFNormalizer,
)
from facade_planner.infrastructure.adapters.pdf_normalizers.base import BasePDFNormalizer
from facade_planner.infrastructure.adapters.pdf_normalizers.generic_normalizer import (
    GenericPDFNormalizer,
)
from facade_planner.infrastructure.adapters.pdf_normalizers.revit_normalizer import (
    RevitPDFNormalizer,
)


def get_normalizer(source: PDFSource) -> BasePDFNormalizer:
    match source:
        case PDFSource.AUTOCAD:
            return AutoCADPDFNormalizer()
        case PDFSource.REVIT:
            return RevitPDFNormalizer()
        case PDFSource.ARCHICAD:
            return ArchiCADPDFNormalizer()
        case _:
            return GenericPDFNormalizer()

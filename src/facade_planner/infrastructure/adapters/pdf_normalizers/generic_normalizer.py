"""Generic PDF normalizer — best-effort for unknown generators."""
import warnings

from facade_planner.domain.value_objects.raw_geometry import RawGeometry
from facade_planner.infrastructure.adapters.pdf_normalizers.base import BasePDFNormalizer


class GenericPDFNormalizer(BasePDFNormalizer):
    def should_include_layer(self, layer: str) -> bool:
        return True  # cannot reliably identify title-block layers for unknown generators

    def normalize(self, geometries: list[RawGeometry]) -> list[RawGeometry]:
        warnings.warn(
            "PDF-Generator nicht erkannt — GenericPDFNormalizer wird verwendet. "
            "Ergebnisqualität ist nicht garantiert.",
            UserWarning,
            stacklevel=2,
        )
        result = self._remove_degenerate(geometries)
        result = self._deduplicate(result)
        return result

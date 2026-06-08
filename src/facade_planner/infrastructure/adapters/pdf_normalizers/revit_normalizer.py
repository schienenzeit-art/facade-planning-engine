"""Revit PDF normalizer.

Revit PDF characteristics:
- Layer structure is often collapsed: many elements land on a single unnamed layer ""
- Title block: elements outside the printable bounding box (x < 0 or y < 0 often excluded
  by PDF page bounds, so positional filtering suffices in most cases)
- Color-based classification is the main heuristic (Revit assigns colors per category)
- Thin lines (linewidth < 0.5pt) are typically annotations, not facades
"""
import warnings

from facade_planner.domain.value_objects.raw_geometry import RawGeometry
from facade_planner.infrastructure.adapters.pdf_normalizers.base import BasePDFNormalizer

_EXCLUDED_LAYERS: frozenset[str] = frozenset({"Title Block", "Viewports"})


class RevitPDFNormalizer(BasePDFNormalizer):
    def __init__(self, warn_on_no_layers: bool = True) -> None:
        self._warn = warn_on_no_layers

    def should_include_layer(self, layer: str) -> bool:
        return layer not in _EXCLUDED_LAYERS

    def normalize(self, geometries: list[RawGeometry]) -> list[RawGeometry]:
        if self._warn and all(g.layer == "" for g in geometries):
            warnings.warn(
                "Revit PDF enthält keine Layer-Namen — Ergebnisqualität nicht garantiert. "
                "Farb-basierte Klassifikation wird verwendet (RISK-PDF-001).",
                UserWarning,
                stacklevel=2,
            )
        result = self._filter_by_layer(geometries)
        result = self._remove_degenerate(result)
        result = self._deduplicate(result)
        return result

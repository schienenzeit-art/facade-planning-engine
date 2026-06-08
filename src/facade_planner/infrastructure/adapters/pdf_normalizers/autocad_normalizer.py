"""AutoCAD PDF normalizer.

AutoCAD PDF characteristics:
- Coordinate origin: bottom-left (standard PDF) — no Y-flip needed
- Layer names: exported as PDF OCG layer names (e.g. "A-WALL", "TITLEBLK", "BORDER")
- Title block: typically on layers "TITLEBLK", "BORDER", "DEFPOINTS", or "A-ANNO"
- Grid lines: layer "A-GRID" or "GRID"
"""
from facade_planner.domain.value_objects.raw_geometry import RawGeometry
from facade_planner.infrastructure.adapters.pdf_normalizers.base import BasePDFNormalizer

_EXCLUDED_LAYERS: frozenset[str] = frozenset(
    {
        "TITLEBLK",
        "TITLEBLOCK",
        "BORDER",
        "DEFPOINTS",
        "A-ANNO",
        "A-ANNO-SYMB",
        "A-SHEET",
    }
)


class AutoCADPDFNormalizer(BasePDFNormalizer):
    def should_include_layer(self, layer: str) -> bool:
        return layer.upper() not in _EXCLUDED_LAYERS

    def normalize(self, geometries: list[RawGeometry]) -> list[RawGeometry]:
        result = self._filter_by_layer(geometries)
        result = self._remove_degenerate(result)
        result = self._deduplicate(result)
        return result

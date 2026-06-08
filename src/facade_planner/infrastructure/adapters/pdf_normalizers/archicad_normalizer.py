"""ArchiCAD PDF normalizer.

ArchiCAD PDF characteristics:
- Similar to AutoCAD in coordinate convention (bottom-left origin, no Y-flip)
- Layer names: ArchiCAD-specific conventions ("Stempel", "Layout", "Schriftfeld")
- Title block layers are localized (German: "Stempel"/"Schriftfeld", English: "Titleblock")
"""
from facade_planner.domain.value_objects.raw_geometry import RawGeometry
from facade_planner.infrastructure.adapters.pdf_normalizers.base import BasePDFNormalizer

_EXCLUDED_LAYERS: frozenset[str] = frozenset(
    {
        "Stempel",
        "Schriftfeld",
        "Titleblock",
        "TitleBlock",
        "Layout",
        "Rahmen",
        "Border",
    }
)


class ArchiCADPDFNormalizer(BasePDFNormalizer):
    def should_include_layer(self, layer: str) -> bool:
        return layer not in _EXCLUDED_LAYERS

    def normalize(self, geometries: list[RawGeometry]) -> list[RawGeometry]:
        result = self._filter_by_layer(geometries)
        result = self._remove_degenerate(result)
        result = self._deduplicate(result)
        return result

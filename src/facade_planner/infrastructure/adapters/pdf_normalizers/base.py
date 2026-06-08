"""Abstract base for PDF normalizers (Strategy Pattern per ADR-002)."""
from abc import ABC, abstractmethod

from facade_planner.domain.value_objects.raw_geometry import RawGeometry


class BasePDFNormalizer(ABC):
    """Normalizes raw geometries extracted from a PDF to a canonical form.

    Each subclass handles the quirks of one specific CAD generator
    (coordinate origin, layer naming, title-block filtering, etc.).
    """

    @abstractmethod
    def normalize(self, geometries: list[RawGeometry]) -> list[RawGeometry]:
        """Return a cleaned, normalized subset of the input geometries."""

    @abstractmethod
    def should_include_layer(self, layer: str) -> bool:
        """True if a geometry on this layer should be kept."""

    # ── Shared helpers ────────────────────────────────────────────────────────

    def _filter_by_layer(self, geometries: list[RawGeometry]) -> list[RawGeometry]:
        return [g for g in geometries if self.should_include_layer(g.layer)]

    @staticmethod
    def _remove_degenerate(geometries: list[RawGeometry]) -> list[RawGeometry]:
        """Drop paths with fewer than 2 distinct points."""
        result: list[RawGeometry] = []
        for g in geometries:
            coords = g.coordinates
            if len(coords) < 2:
                continue
            unique = set(coords)
            if len(unique) < 2:
                continue
            result.append(g)
        return result

    @staticmethod
    def _deduplicate(geometries: list[RawGeometry]) -> list[RawGeometry]:
        """Remove exact coordinate-level duplicates (keeps first occurrence)."""
        seen: set[tuple] = set()
        result: list[RawGeometry] = []
        for g in geometries:
            key = tuple(g.coordinates)
            if key not in seen:
                seen.add(key)
                result.append(g)
        return result

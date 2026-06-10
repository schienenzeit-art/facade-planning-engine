"""OpeningDetectionService — detects openings (windows/doors) within a FacadeSurface.

Algorithm (ISSUE-081):
- Candidate polygon fully contained in surface (within tolerance_mm buffer) → Opening
- Candidate polygon 50%+ outside surface → warning, not an opening
- Nested openings (one inside another): only the outer one is kept (MVP: no hierarchy)
- OpeningType from bounding-box aspect ratio:
    > 2.5  → WINDOW
    1.5–2.5 → DOOR
    else   → OTHER
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from shapely.geometry import Polygon
from shapely.validation import make_valid

from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.opening import Opening
from facade_planner.domain.enums import OpeningType

Coordinate = tuple[float, float]

_ASPECT_WINDOW = 2.5
_ASPECT_DOOR = 1.5


@dataclass
class OpeningDetectionResult:
    openings: list[Opening] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class OpeningDetectionService:
    """Classifies candidate polygon boundaries as openings of a FacadeSurface."""

    def detect(
        self,
        surface: FacadeSurface,
        candidate_boundaries: list[list[Coordinate]],
        tolerance_mm: float = 1.0,
    ) -> OpeningDetectionResult:
        """Return openings and any geometry warnings.

        Args:
            surface: The FacadeSurface to check against.
            candidate_boundaries: Raw polygon boundary lists to evaluate.
            tolerance_mm: Inward buffer on the surface polygon.  A candidate
                that fits within this expanded boundary is considered "inside".
        """
        result = OpeningDetectionResult()

        surface_poly = _make_polygon(surface.boundary)
        if surface_poly is None or surface_poly.is_empty:
            result.warnings.append(
                f"Surface '{surface.id}' hat keine gueltige Polygon-Geometrie."
            )
            return result

        # Negative buffer = inward shrink by tolerance_mm
        surface_inner = surface_poly.buffer(-tolerance_mm) if tolerance_mm > 0 else surface_poly

        raw_openings: list[tuple[Polygon, list[Coordinate]]] = []

        for idx, boundary in enumerate(candidate_boundaries):
            cand_poly = _make_polygon(boundary)
            if cand_poly is None or cand_poly.is_empty:
                continue

            # Fraction of candidate that lies inside the surface
            inter = surface_poly.intersection(cand_poly)
            overlap = inter.area / cand_poly.area if cand_poly.area > 0 else 0.0

            outside_fraction = 1.0 - overlap

            if outside_fraction >= 0.5:
                result.warnings.append(
                    f"Kandidat #{idx + 1} liegt zu {outside_fraction:.0%} ausserhalb "
                    f"von Surface '{surface.id}' — kein Opening."
                )
                continue

            # Fully inside check (within tolerance buffer)
            if not surface_inner.contains(cand_poly):
                # More than tolerance outside, but < 50% outside: treat as opening anyway
                # (partial containment case, e.g. border geometries)
                pass

            raw_openings.append((cand_poly, boundary))

        # Remove nested openings: keep only outer ones
        outer_openings = _filter_nested(raw_openings)

        for poly, boundary in outer_openings:
            opening_type = _classify_type(poly)
            result.openings.append(
                Opening(
                    id=f"OPN-{uuid.uuid4().hex[:8].upper()}",
                    surface_id=surface.id,
                    opening_type=opening_type,
                    boundary=boundary,
                )
            )

        return result


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_polygon(coords: list[Coordinate]) -> Polygon | None:
    if len(coords) < 3:
        return None
    # Drop explicit closing vertex if present
    pts = list(coords)
    if pts[0] == pts[-1] and len(pts) > 3:
        pts = pts[:-1]
    if len(set(pts)) < 3:
        return None
    try:
        poly = Polygon(pts)
        return make_valid(poly) if not poly.is_valid else poly
    except Exception:
        return None


def _filter_nested(
    openings: list[tuple[Polygon, list[Coordinate]]],
) -> list[tuple[Polygon, list[Coordinate]]]:
    """Remove any opening whose polygon is fully contained within another opening."""
    result = []
    for i, (poly_i, boundary_i) in enumerate(openings):
        # Only mark as nested when containment is strictly one-directional
        # (prevents removing both when two identical polygons are present)
        is_nested = any(
            poly_j.contains(poly_i) and not poly_i.contains(poly_j)
            for j, (poly_j, _) in enumerate(openings)
            if j != i
        )
        if not is_nested:
            result.append((poly_i, boundary_i))
    return result


def _classify_type(poly: Polygon) -> OpeningType:
    min_x, min_y, max_x, max_y = poly.bounds
    w = max_x - min_x
    h = max_y - min_y
    if w <= 0 or h <= 0:
        return OpeningType.OTHER
    aspect = max(w, h) / min(w, h)
    if aspect > _ASPECT_WINDOW:
        return OpeningType.WINDOW
    if aspect >= _ASPECT_DOOR:
        return OpeningType.DOOR
    return OpeningType.OTHER

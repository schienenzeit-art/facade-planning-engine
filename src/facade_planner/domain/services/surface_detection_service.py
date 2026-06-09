"""SurfaceDetectionService — detects facade surfaces from calibrated RawGeometry.

Algorithm:
  1. Collect closed polygons (is_closed=True) with ≥ 3 distinct points.
  2. Attempt gap-closure on nearly-closed open paths (within gap_tolerance_mm).
  3. Build Shapely Polygons; validate and auto-repair where possible.
  4. Filter by configured area window [min_area_mm2, max_area_mm2].
  5. Remove near-duplicate polygons (overlap > 90% of smaller area).
  6. Return FacadeSurface objects sorted largest-first, status=DETECTED.

Opening detection is handled separately in EPIC-008.
"""
from __future__ import annotations

import math
import uuid

from pydantic import BaseModel
from shapely.geometry import Polygon
from shapely.validation import make_valid

from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.enums import SurfaceStatus
from facade_planner.domain.value_objects.raw_geometry import RawGeometry

Coordinate = tuple[float, float]

# A facade surface must be at least this large to be considered (0.1 m²)
_DEFAULT_MIN_AREA_MM2: float = 100_000.0
# Gap-close tolerance: endpoints within this distance → treat as closed
_DEFAULT_GAP_TOLERANCE_MM: float = 0.5
# Two polygons are "duplicates" if the smaller overlaps the larger by this fraction
_DUPLICATE_IOU_THRESHOLD: float = 0.90


class SurfaceDetectionConfig(BaseModel):
    model_config = {"frozen": True}

    min_area_mm2: float = _DEFAULT_MIN_AREA_MM2
    max_area_mm2: float | None = None
    gap_tolerance_mm: float = _DEFAULT_GAP_TOLERANCE_MM


class SurfaceDetectionService:
    def __init__(self, config: SurfaceDetectionConfig | None = None) -> None:
        self._cfg = config or SurfaceDetectionConfig()

    def detect(
        self,
        plan_id: str,
        page_number: int,
        geometries: list[RawGeometry],
    ) -> list[FacadeSurface]:
        """Return detected FacadeSurface objects sorted by area descending."""
        polygons = self._build_polygons(geometries)
        polygons = self._filter_by_area(polygons)
        polygons = self._remove_duplicates(polygons)

        surfaces: list[FacadeSurface] = []
        for poly in sorted(polygons, key=lambda p: p.area, reverse=True):
            coords = _exterior_coords(poly)
            if len(coords) < 3:
                continue
            surfaces.append(
                FacadeSurface(
                    id=str(uuid.uuid4()),
                    plan_id=plan_id,
                    page_number=page_number,
                    boundary=coords,
                    status=SurfaceStatus.DETECTED,
                )
            )
        return surfaces

    # ── private ─────────────────────────────────────────────────────────────

    def _build_polygons(self, geometries: list[RawGeometry]) -> list[Polygon]:
        result: list[Polygon] = []
        for geom in geometries:
            coords = list(geom.coordinates)
            if geom.is_closed:
                poly = _try_polygon(coords)
            else:
                poly = _try_gap_close(coords, self._cfg.gap_tolerance_mm)
            if poly is not None:
                result.append(poly)
        return result

    def _filter_by_area(self, polygons: list[Polygon]) -> list[Polygon]:
        result: list[Polygon] = []
        for poly in polygons:
            if poly.area < self._cfg.min_area_mm2:
                continue
            if self._cfg.max_area_mm2 is not None and poly.area > self._cfg.max_area_mm2:
                continue
            result.append(poly)
        return result

    @staticmethod
    def _remove_duplicates(polygons: list[Polygon]) -> list[Polygon]:
        """Keep the largest of any pair that overlaps by > 90% of the smaller's area."""
        sorted_polys = sorted(polygons, key=lambda p: p.area, reverse=True)
        kept: list[Polygon] = []
        for candidate in sorted_polys:
            dominated = False
            for existing in kept:
                try:
                    intersection_area = candidate.intersection(existing).area
                    if intersection_area / candidate.area > _DUPLICATE_IOU_THRESHOLD:
                        dominated = True
                        break
                except Exception:
                    continue
            if not dominated:
                kept.append(candidate)
        return kept


# ── module-level helpers ─────────────────────────────────────────────────────

def _try_polygon(coords: list[Coordinate]) -> Polygon | None:
    """Build a valid Shapely Polygon from coords, or return None."""
    if len(coords) < 3:
        return None
    # Drop explicit closing point if present
    if coords[0] == coords[-1] and len(coords) > 3:
        coords = coords[:-1]
    if len(set(coords)) < 3:
        return None
    try:
        poly = Polygon(coords)
        if not poly.is_valid:
            poly = make_valid(poly)
        if not isinstance(poly, Polygon) or poly.is_empty:
            return None
        return poly
    except Exception:
        return None


def _try_gap_close(
    coords: list[Coordinate], tolerance_mm: float
) -> Polygon | None:
    """If endpoints are within tolerance, attempt polygon construction."""
    if len(coords) < 3:
        return None
    first, last = coords[0], coords[-1]
    dist = math.hypot(first[0] - last[0], first[1] - last[1])
    if dist > tolerance_mm:
        return None
    return _try_polygon(coords)


def _exterior_coords(poly: Polygon) -> list[Coordinate]:
    """Return exterior ring coordinates (excluding Shapely's closing duplicate)."""
    coords = list(poly.exterior.coords)
    if coords and coords[0] == coords[-1]:
        coords = coords[:-1]
    return [(float(x), float(y)) for x, y in coords]

"""PanelOpeningFilter — applies TRIM or DROP strategy against surface openings.

TRIM (default):
  For each panel overlapping an opening, find the largest axis-aligned
  rectangular sub-region that does not overlap any opening.
  If that remainder is smaller than min_panel_width/height_mm → drop the panel.
  If the opening sits in the centre of a panel (no clean rectangular clip) → drop.

DROP:
  Any panel with even minimal overlap with an opening is removed.
"""
from __future__ import annotations

from shapely.geometry import box
from shapely.ops import unary_union

from facade_planner.domain.entities.opening import Opening
from facade_planner.domain.entities.panel import Panel
from facade_planner.domain.enums import CutReason, OpeningStrategy, SelectionReason

_EPSILON = 0.001


class PanelOpeningFilter:
    """Filters / trims panels against a list of openings."""

    def apply(
        self,
        panels: list[Panel],
        openings: list[Opening],
        strategy: OpeningStrategy,
        min_panel_width_mm: float,
        min_panel_height_mm: float,
    ) -> list[Panel]:
        """Return the filtered/trimmed panel list.

        Panels that do not overlap any opening are returned unchanged.
        """
        if not openings:
            return panels

        opening_polys = [
            _make_opening_poly(o)
            for o in openings
        ]
        opening_polys = [p for p in opening_polys if p is not None and not p.is_empty]

        if not opening_polys:
            return panels

        result: list[Panel] = []
        for panel in panels:
            processed = _process_panel(
                panel,
                opening_polys,
                strategy,
                min_panel_width_mm,
                min_panel_height_mm,
            )
            if processed is not None:
                result.append(processed)
        return result


# ── internal ─────────────────────────────────────────────────────────────────


def _make_opening_poly(opening: Opening):
    from shapely.geometry import Polygon
    from shapely.validation import make_valid
    pts = list(opening.boundary)
    if len(pts) < 3:
        return None
    try:
        poly = Polygon(pts)
        return make_valid(poly) if not poly.is_valid else poly
    except Exception:
        return None


def _process_panel(
    panel: Panel,
    opening_polys: list,
    strategy: OpeningStrategy,
    min_w: float,
    min_h: float,
) -> Panel | None:
    px1 = panel.x_mm
    py1 = panel.y_mm
    px2 = px1 + panel.actual_width_mm
    py2 = py1 + panel.actual_height_mm
    panel_box = box(px1, py1, px2, py2)

    # Collect openings with actual area overlap (shared edges don't count)
    overlapping = [
        op for op in opening_polys
        if panel_box.intersection(op).area > _EPSILON
    ]
    if not overlapping:
        return panel

    # DROP: remove any panel touching an opening
    if strategy == OpeningStrategy.DROP:
        return None

    # TRIM: find the best rectangular sub-region
    union = unary_union(overlapping)
    inter = panel_box.intersection(union)
    if inter.is_empty:
        return panel

    ix1, iy1, ix2, iy2 = inter.bounds

    # 4 candidate rectangular clips (always produces an axis-aligned rectangle)
    candidates: list[tuple[float, float, float, float]] = []

    left_w = ix1 - px1
    if left_w >= min_w - _EPSILON:
        candidates.append((px1, py1, left_w, panel.actual_height_mm))

    right_w = px2 - ix2
    if right_w >= min_w - _EPSILON:
        candidates.append((ix2, py1, right_w, panel.actual_height_mm))

    bottom_h = iy1 - py1
    if bottom_h >= min_h - _EPSILON:
        candidates.append((px1, py1, panel.actual_width_mm, bottom_h))

    top_h = py2 - iy2
    if top_h >= min_h - _EPSILON:
        candidates.append((px1, iy2, panel.actual_width_mm, top_h))

    if not candidates:
        return None

    # Pick largest area candidate that truly doesn't overlap the union
    best: tuple[float, float, float, float] | None = None
    best_area = -1.0
    for x, y, w, h in candidates:
        candidate_box = box(x, y, x + w, y + h)
        still_overlaps = candidate_box.intersection(union).area > _EPSILON
        if still_overlaps:
            continue
        area = w * h
        if area > best_area:
            best_area = area
            best = (x, y, w, h)

    if best is None:
        return None

    bx, by, bw, bh = best
    return panel.model_copy(
        update={
            "x_mm": bx,
            "y_mm": by,
            "actual_width_mm": bw,
            "actual_height_mm": bh,
            "is_cut": True,
            "cut_reason": CutReason.OPENING,
            "selection_reason": SelectionReason.SMALLEST_FIT,
        }
    )

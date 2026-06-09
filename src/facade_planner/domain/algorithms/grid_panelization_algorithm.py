"""GridPanelizationAlgorithm — regular axis-aligned grid with expansion joints.

Design decisions (Grid-Reset strategy, see ISSUE-053):
- One format is selected for the whole surface (prefer largest full-panel fit).
- Columns and rows are laid out independently using the same _build_segments helper.
- Expansion joints are inserted as gaps (no panel placed inside the gap).
  After each expansion joint, a new grid segment starts (Grid-Reset strategy).
- Edge panels (right column / bottom row) are cut panels if they are at least
  min_panel_width_mm / min_panel_height_mm wide; smaller → PE-002.
"""
from __future__ import annotations

from facade_planner.domain.algorithms.base_panelization_algorithm import (
    BasePanelizationAlgorithm,
)
from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.panel import Panel
from facade_planner.domain.entities.panel_format import PanelFormat
from facade_planner.domain.entities.panelization_job import PanelizationConfig
from facade_planner.domain.enums import (
    CutReason,
    PanelizationErrorType,
    PanelOrientation,
    SelectionReason,
)
from facade_planner.domain.exceptions import PanelizationError

_EPSILON = 0.001  # mm tolerance for floating-point edge comparisons

# (position, size, is_cut) segment triple
_Segment = tuple[float, float, bool]


class GridPanelizationAlgorithm(BasePanelizationAlgorithm):
    """Places panels in a regular grid, full-panels first, with expansion joints."""

    @classmethod
    def name(cls) -> str:
        return "grid-v1"

    def panelize(
        self,
        surface: FacadeSurface,
        formats: list[PanelFormat],
        config: PanelizationConfig,
    ) -> list[Panel]:
        surface_w = surface.width_mm
        surface_h = surface.height_mm
        origin_x = surface.bounding_box[0]
        origin_y = surface.bounding_box[1]

        # PE-004: surface is smaller than the minimum allowed panel size
        if (
            surface_w < config.min_panel_width_mm - _EPSILON
            or surface_h < config.min_panel_height_mm - _EPSILON
        ):
            raise PanelizationError(
                PanelizationErrorType.PE_004_SURFACE_TOO_SMALL.value,
                surface.id,
                f"Flaeche zu klein ({surface_w:.0f}x{surface_h:.0f}mm) — "
                f"Minimum: {config.min_panel_width_mm:.0f}x"
                f"{config.min_panel_height_mm:.0f}mm.",
            )

        # Format selection
        fmt = _select_format(formats, surface_w, surface_h, config.orientation)
        if fmt is None:
            raise PanelizationError(
                PanelizationErrorType.PE_001_NO_FORMAT_FITS.value,
                surface.id,
                f"Kein Format passt in die Flaeche ({surface_w:.0f}x{surface_h:.0f}mm). "
                "Alle verfuegbaren Formate sind zu gross.",
            )

        jc = config.joint_config

        col_segs = _build_segments(
            total_length=surface_w,
            panel_size=fmt.width_mm,
            joint_mm=jc.horizontal_joint_mm,
            exp_interval=jc.expansion_joint_interval_mm,
            exp_width=jc.expansion_joint_width_mm,
            min_size=config.min_panel_width_mm,
            surface_id=surface.id,
        )
        row_segs = _build_segments(
            total_length=surface_h,
            panel_size=fmt.height_mm,
            joint_mm=jc.vertical_joint_mm,
            exp_interval=jc.expansion_joint_interval_mm,
            exp_width=jc.expansion_joint_width_mm,
            min_size=config.min_panel_height_mm,
            surface_id=surface.id,
        )

        panels: list[Panel] = []
        for row_idx, (row_y, row_h, row_cut) in enumerate(row_segs):
            for col_idx, (col_x, col_w, col_cut) in enumerate(col_segs):
                is_cut = col_cut or row_cut
                panels.append(
                    Panel(
                        id=f"{surface.id}-R{row_idx:03d}C{col_idx:03d}",
                        surface_id=surface.id,
                        format_code=fmt.format_code,
                        x_mm=origin_x + col_x,
                        y_mm=origin_y + row_y,
                        actual_width_mm=col_w,
                        actual_height_mm=row_h,
                        is_cut=is_cut,
                        cut_reason=CutReason.SURFACE_EDGE if is_cut else None,
                        selection_reason=(
                            SelectionReason.FULL_PANEL_FIT
                            if not is_cut
                            else SelectionReason.SMALLEST_FIT
                        ),
                        row=row_idx,
                        col=col_idx,
                    )
                )

        return panels


# ── internal helpers ─────────────────────────────────────────────────────────


def _select_format(
    formats: list[PanelFormat],
    surface_w: float,
    surface_h: float,
    orientation: PanelOrientation,
) -> PanelFormat | None:
    """Pick the best-fitting format for the surface.

    Prefers the largest format (by area) whose nominal dimensions fit
    within the surface bounding box.  Active formats only.
    """
    candidates = [
        f
        for f in formats
        if f.is_active
        and f.width_mm <= surface_w + _EPSILON
        and f.height_mm <= surface_h + _EPSILON
    ]
    if not candidates:
        # Try swapped dimensions if orientation allows
        if orientation != PanelOrientation.HORIZONTAL:
            candidates = [
                f
                for f in formats
                if f.is_active
                and f.height_mm <= surface_w + _EPSILON
                and f.width_mm <= surface_h + _EPSILON
            ]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.area_mm2)


def _build_segments(
    total_length: float,
    panel_size: float,
    joint_mm: float,
    exp_interval: float,
    exp_width: float,
    min_size: float,
    surface_id: str,
) -> list[_Segment]:
    """Build (position, size, is_cut) segments along one dimension.

    Handles regular panels, edge (cut) panels, and expansion-joint gaps.
    Raises PanelizationError(PE-002) when an edge panel would be smaller
    than *min_size*.
    """
    segments: list[_Segment] = []
    pos = 0.0
    last_exp_end = 0.0  # x/y position where the last expansion joint ended

    while pos < total_length - _EPSILON:
        # Insert expansion joint when interval is exceeded
        if exp_interval > 0.0 and pos > last_exp_end + _EPSILON:
            distance_since_last = pos - last_exp_end
            if distance_since_last >= exp_interval - _EPSILON:
                pos += exp_width
                last_exp_end = pos
                if pos >= total_length - _EPSILON:
                    break
                continue  # re-evaluate from the new pos

        remaining = total_length - pos

        if remaining >= panel_size - _EPSILON:
            segments.append((pos, panel_size, False))
            pos += panel_size + joint_mm
        elif remaining >= min_size - _EPSILON:
            segments.append((pos, remaining, True))
            break
        elif remaining < _EPSILON:
            break
        else:
            raise PanelizationError(
                PanelizationErrorType.PE_002_EDGE_PANEL_TOO_SMALL.value,
                surface_id,
                f"Randpanel zu schmal ({remaining:.1f}mm < Minimum {min_size:.1f}mm). "
                "Passe min_panel_width_mm / min_panel_height_mm oder das Format an.",
            )

    return segments

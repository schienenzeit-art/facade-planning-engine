"""DXF export adapter — writes PanelizationResult as DXF AC1027 (R2013, mm).

Layer scheme per surface (sid = first 8 chars of surface UUID):
  FACADE-{sid}-BOUND  green  (3)  — surface boundary LWPOLYLINE
  FACADE-{sid}-OPENS  red    (1)  — opening LWPOLYLINEs
  FACADE-{sid}-PANLS  cyan   (4)  — panel rectangle LWPOLYLINEs
  FACADE-{sid}-LABLS  white  (7)  — panel-ID MTEXT labels
"""
from __future__ import annotations

from pathlib import Path

import ezdxf
import ezdxf.math

from facade_planner.application.ports.export_port import ExportPort
from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.panelization_result import PanelizationResult
from facade_planner.domain.exceptions import ExportError

_LABEL_HEIGHT_MM = 80.0

_LAYER_COLORS = {
    "BOUND": 3,   # green
    "OPENS": 1,   # red
    "PANLS": 4,   # cyan
    "LABLS": 7,   # white
}


def _sid(surface_id: str) -> str:
    return surface_id[:8]


def _layer(surface_id: str, suffix: str) -> str:
    return f"FACADE-{_sid(surface_id)}-{suffix}"


class DxfExportAdapter(ExportPort):
    """Writes PanelizationResult + FacadeSurfaces to a DXF R2013 file."""

    def export(
        self,
        result: PanelizationResult,
        surfaces: list[FacadeSurface],
        output_path: Path,
    ) -> None:
        try:
            doc = self._build_document(result, surfaces)
            doc.saveas(str(output_path))
        except ezdxf.DXFError as exc:
            raise ExportError(f"DXF-Schreiben fehlgeschlagen: {exc}") from exc

    def _build_document(
        self,
        result: PanelizationResult,
        surfaces: list[FacadeSurface],
    ) -> ezdxf.document.Drawing:
        doc = ezdxf.new("R2013")
        doc.header["$INSUNITS"] = 4    # millimeters
        doc.header["$MEASUREMENT"] = 1  # metric

        surface_map = {s.id: s for s in surfaces}
        self._create_layers(doc, surfaces)
        msp = doc.modelspace()

        for surface in surfaces:
            self._write_boundary(msp, surface)
            self._write_openings(msp, surface)

        for panel in result.panels:
            surface = surface_map.get(panel.surface_id)
            if surface is None:
                continue
            self._write_panel(msp, panel, panel.surface_id)
            self._write_label(msp, panel, panel.surface_id)

        return doc

    def _create_layers(
        self,
        doc: ezdxf.document.Drawing,
        surfaces: list[FacadeSurface],
    ) -> None:
        layers = doc.layers
        for surface in surfaces:
            for suffix, color in _LAYER_COLORS.items():
                name = _layer(surface.id, suffix)
                if name not in layers:
                    layers.add(name, color=color)

    def _write_boundary(self, msp: object, surface: FacadeSurface) -> None:
        if len(surface.boundary) < 3:
            return
        msp.add_lwpolyline(  # type: ignore[attr-defined]
            surface.boundary,
            close=True,
            dxfattribs={"layer": _layer(surface.id, "BOUND")},
        )

    def _write_openings(self, msp: object, surface: FacadeSurface) -> None:
        for opening in surface.openings:
            if len(opening.boundary) < 3:
                continue
            msp.add_lwpolyline(  # type: ignore[attr-defined]
                opening.boundary,
                close=True,
                dxfattribs={"layer": _layer(surface.id, "OPENS")},
            )

    def _write_panel(self, msp: object, panel: object, surface_id: str) -> None:
        msp.add_lwpolyline(  # type: ignore[attr-defined]
            panel.corners,  # type: ignore[attr-defined]
            close=True,
            dxfattribs={"layer": _layer(surface_id, "PANLS")},
        )

    def _write_label(self, msp: object, panel: object, surface_id: str) -> None:
        cx = panel.x_mm + panel.actual_width_mm / 2  # type: ignore[attr-defined]
        cy = panel.y_mm + panel.actual_height_mm / 2  # type: ignore[attr-defined]
        msp.add_mtext(  # type: ignore[attr-defined]
            panel.id,  # type: ignore[attr-defined]
            dxfattribs={
                "insert": ezdxf.math.Vec3(cx, cy, 0.0),
                "char_height": _LABEL_HEIGHT_MM,
                "layer": _layer(surface_id, "LABLS"),
                "attachment_point": 5,  # MIDDLE_CENTER
            },
        )

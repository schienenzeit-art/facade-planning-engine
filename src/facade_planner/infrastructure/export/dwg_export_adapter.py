"""DWG export adapter — DXF write + ODA File Converter conversion."""
from __future__ import annotations

from pathlib import Path

from facade_planner.application.ports.export_port import ExportPort
from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.panelization_result import PanelizationResult
from facade_planner.infrastructure.export.dxf_export_adapter import DxfExportAdapter
from facade_planner.infrastructure.export.oda_converter_adapter import OdaConverterAdapter


class DwgExportAdapter(ExportPort):
    """Exports PanelizationResult as DWG via DXF + ODA File Converter."""

    def __init__(
        self,
        oda_adapter: OdaConverterAdapter | None = None,
        dxf_adapter: DxfExportAdapter | None = None,
    ) -> None:
        self._oda = oda_adapter or OdaConverterAdapter()
        self._dxf = dxf_adapter or DxfExportAdapter()

    def export(
        self,
        result: PanelizationResult,
        surfaces: list[FacadeSurface],
        output_path: Path,
    ) -> None:
        """Write DXF to a temp file, convert to DWG, delete temp file."""
        tmp_dxf = output_path.with_suffix(".dxf")
        try:
            self._dxf.export(result, surfaces, tmp_dxf)
            self._oda.convert(tmp_dxf, output_path)
        finally:
            if tmp_dxf.exists():
                tmp_dxf.unlink()

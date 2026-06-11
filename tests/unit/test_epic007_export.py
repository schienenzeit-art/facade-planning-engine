"""Tests for EPIC-007 (DXF Export) and EPIC-011 (DWG Export via ODA)."""
from __future__ import annotations

import subprocess
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import ezdxf
import pytest

from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.entities.opening import Opening
from facade_planner.domain.entities.panel import Panel
from facade_planner.domain.entities.panelization_result import PanelizationResult
from facade_planner.domain.enums import OpeningType
from facade_planner.domain.exceptions import ExportError, OdaConverterNotFoundError
from facade_planner.infrastructure.export.dxf_export_adapter import DxfExportAdapter
from facade_planner.infrastructure.export.dwg_export_adapter import DwgExportAdapter
from facade_planner.infrastructure.export.oda_converter_adapter import OdaConverterAdapter


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def surface_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def surface_with_opening(surface_id: str) -> FacadeSurface:
    opening = Opening(
        id=str(uuid.uuid4()),
        surface_id=surface_id,
        opening_type=OpeningType.WINDOW,
        boundary=[(1000.0, 500.0), (2000.0, 500.0), (2000.0, 1500.0), (1000.0, 1500.0)],
    )
    return FacadeSurface(
        id=surface_id,
        plan_id="plan-001",
        page_number=1,
        boundary=[(0.0, 0.0), (5000.0, 0.0), (5000.0, 3000.0), (0.0, 3000.0)],
        openings=[opening],
    )


def _make_panels(surface_id: str, count: int = 3) -> list[Panel]:
    panels = []
    for i in range(count):
        panels.append(
            Panel(
                id=f"P-{i:04d}",
                surface_id=surface_id,
                format_code="SW-1250x3050",
                x_mm=float(i * 1260),
                y_mm=0.0,
                actual_width_mm=1250.0,
                actual_height_mm=3000.0,
            )
        )
    return panels


@pytest.fixture
def result(surface_id: str) -> PanelizationResult:
    return PanelizationResult(
        job_id="job-test-001",
        panels=_make_panels(surface_id),
    )


# ── DXF header ───────────────────────────────────────────────────────────────


def test_dxf_header(
    tmp_path: Path,
    result: PanelizationResult,
    surface_with_opening: FacadeSurface,
) -> None:
    out = tmp_path / "test.dxf"
    DxfExportAdapter().export(result, [surface_with_opening], out)

    doc = ezdxf.readfile(str(out))
    assert doc.header["$INSUNITS"] == 4, "INSUNITS must be 4 (mm)"
    assert doc.header["$MEASUREMENT"] == 1, "MEASUREMENT must be 1 (metric)"
    assert doc.acad_release == "R2013"


# ── Layer structure ───────────────────────────────────────────────────────────


def test_dxf_layers_created(
    tmp_path: Path,
    result: PanelizationResult,
    surface_with_opening: FacadeSurface,
) -> None:
    out = tmp_path / "test.dxf"
    DxfExportAdapter().export(result, [surface_with_opening], out)

    doc = ezdxf.readfile(str(out))
    layer_names = {layer.dxf.name for layer in doc.layers}
    sid = surface_with_opening.id[:8]

    assert f"FACADE-{sid}-BOUND" in layer_names
    assert f"FACADE-{sid}-OPENS" in layer_names
    assert f"FACADE-{sid}-PANLS" in layer_names
    assert f"FACADE-{sid}-LABLS" in layer_names


def test_dxf_layer_colors(
    tmp_path: Path,
    result: PanelizationResult,
    surface_with_opening: FacadeSurface,
) -> None:
    out = tmp_path / "test.dxf"
    DxfExportAdapter().export(result, [surface_with_opening], out)

    doc = ezdxf.readfile(str(out))
    sid = surface_with_opening.id[:8]
    layers = {layer.dxf.name: layer.dxf.color for layer in doc.layers}

    assert layers[f"FACADE-{sid}-BOUND"] == 3   # green
    assert layers[f"FACADE-{sid}-OPENS"] == 1   # red
    assert layers[f"FACADE-{sid}-PANLS"] == 4   # cyan
    assert layers[f"FACADE-{sid}-LABLS"] == 7   # white


# ── Entity counts ─────────────────────────────────────────────────────────────


def test_dxf_panel_count(
    tmp_path: Path,
    result: PanelizationResult,
    surface_with_opening: FacadeSurface,
) -> None:
    out = tmp_path / "test.dxf"
    DxfExportAdapter().export(result, [surface_with_opening], out)

    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    sid = surface_with_opening.id[:8]
    panel_layer = f"FACADE-{sid}-PANLS"
    panels = [e for e in msp if e.dxf.layer == panel_layer]
    assert len(panels) == result.total_panels


def test_dxf_label_count(
    tmp_path: Path,
    result: PanelizationResult,
    surface_with_opening: FacadeSurface,
) -> None:
    out = tmp_path / "test.dxf"
    DxfExportAdapter().export(result, [surface_with_opening], out)

    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    sid = surface_with_opening.id[:8]
    label_layer = f"FACADE-{sid}-LABLS"
    labels = [e for e in msp if e.dxf.layer == label_layer]
    assert len(labels) == result.total_panels


def test_dxf_opening_written(
    tmp_path: Path,
    result: PanelizationResult,
    surface_with_opening: FacadeSurface,
) -> None:
    out = tmp_path / "test.dxf"
    DxfExportAdapter().export(result, [surface_with_opening], out)

    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    sid = surface_with_opening.id[:8]
    opens_layer = f"FACADE-{sid}-OPENS"
    openings = [e for e in msp if e.dxf.layer == opens_layer]
    assert len(openings) == len(surface_with_opening.openings)


# ── Panel coordinates ─────────────────────────────────────────────────────────


def test_dxf_panel_coordinates(
    tmp_path: Path,
    surface_id: str,
    surface_with_opening: FacadeSurface,
) -> None:
    panel = Panel(
        id="P-COORD",
        surface_id=surface_id,
        format_code="TEST",
        x_mm=100.0,
        y_mm=200.0,
        actual_width_mm=1000.0,
        actual_height_mm=2000.0,
    )
    result = PanelizationResult(job_id="j1", panels=[panel])
    out = tmp_path / "coords.dxf"
    DxfExportAdapter().export(result, [surface_with_opening], out)

    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    sid = surface_with_opening.id[:8]
    panel_entities = [e for e in msp if e.dxf.layer == f"FACADE-{sid}-PANLS"]
    assert len(panel_entities) == 1

    pts = list(panel_entities[0].get_points())
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    assert min(xs) == pytest.approx(100.0, abs=0.001)
    assert min(ys) == pytest.approx(200.0, abs=0.001)
    assert max(xs) == pytest.approx(1100.0, abs=0.001)
    assert max(ys) == pytest.approx(2200.0, abs=0.001)


# ── Multiple surfaces ─────────────────────────────────────────────────────────


def test_dxf_multiple_surfaces(tmp_path: Path) -> None:
    s1_id = str(uuid.uuid4())
    s2_id = str(uuid.uuid4())
    surfaces = [
        FacadeSurface(
            id=s1_id, plan_id="p1", page_number=1,
            boundary=[(0.0, 0.0), (3000.0, 0.0), (3000.0, 2000.0), (0.0, 2000.0)],
        ),
        FacadeSurface(
            id=s2_id, plan_id="p1", page_number=1,
            boundary=[(4000.0, 0.0), (7000.0, 0.0), (7000.0, 2000.0), (4000.0, 2000.0)],
        ),
    ]
    panels = _make_panels(s1_id, 2) + _make_panels(s2_id, 2)
    result = PanelizationResult(job_id="j2", panels=panels)
    out = tmp_path / "multi.dxf"
    DxfExportAdapter().export(result, surfaces, out)

    doc = ezdxf.readfile(str(out))
    layer_names = {layer.dxf.name for layer in doc.layers}
    assert f"FACADE-{s1_id[:8]}-PANLS" in layer_names
    assert f"FACADE-{s2_id[:8]}-PANLS" in layer_names


# ── ODA Converter Adapter ─────────────────────────────────────────────────────


def test_oda_not_found_raises(tmp_path: Path) -> None:
    adapter = OdaConverterAdapter(oda_path=Path("/nonexistent/ODAFileConverter"))
    with pytest.raises(OdaConverterNotFoundError):
        adapter.convert(tmp_path / "in.dxf", tmp_path / "out.dwg")


def test_oda_nonzero_exit_raises(tmp_path: Path) -> None:
    fake_oda = tmp_path / "fake_oda"
    fake_oda.touch()
    src_dxf = tmp_path / "in.dxf"
    src_dxf.write_text("DXF placeholder")

    adapter = OdaConverterAdapter(oda_path=fake_oda)
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "conversion error"
    mock_result.stdout = ""

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(ExportError, match="ODA-Konvertierung fehlgeschlagen"):
            adapter.convert(src_dxf, tmp_path / "out.dwg")


def test_oda_no_output_raises(tmp_path: Path) -> None:
    fake_oda = tmp_path / "fake_oda"
    fake_oda.touch()
    src_dxf = tmp_path / "in.dxf"
    src_dxf.write_text("DXF placeholder")

    adapter = OdaConverterAdapter(oda_path=fake_oda)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    mock_result.stdout = ""

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(ExportError, match="keine .dwg-Datei"):
            adapter.convert(src_dxf, tmp_path / "out.dwg")


# ── DWG Export Adapter ────────────────────────────────────────────────────────


def test_dwg_adapter_calls_dxf_then_oda(
    tmp_path: Path,
    result: PanelizationResult,
    surface_with_opening: FacadeSurface,
) -> None:
    mock_dxf = MagicMock(spec=DxfExportAdapter)
    mock_oda = MagicMock(spec=OdaConverterAdapter)

    out = tmp_path / "output.dwg"
    DwgExportAdapter(oda_adapter=mock_oda, dxf_adapter=mock_dxf).export(
        result, [surface_with_opening], out
    )

    mock_dxf.export.assert_called_once()
    mock_oda.convert.assert_called_once()

    # DXF temp file should be passed without .dwg suffix
    dxf_call_args = mock_dxf.export.call_args
    assert str(dxf_call_args[0][2]).endswith(".dxf")


def test_dwg_adapter_cleans_temp_on_oda_failure(
    tmp_path: Path,
    result: PanelizationResult,
    surface_with_opening: FacadeSurface,
) -> None:
    """Temp DXF must be deleted even when ODA raises."""
    written_paths: list[Path] = []

    def write_dxf(res, surfaces, path: Path) -> None:
        path.write_text("fake dxf")
        written_paths.append(path)

    mock_dxf = MagicMock(spec=DxfExportAdapter)
    mock_dxf.export.side_effect = write_dxf
    mock_oda = MagicMock(spec=OdaConverterAdapter)
    mock_oda.convert.side_effect = ExportError("ODA failed")

    out = tmp_path / "output.dwg"
    with pytest.raises(ExportError):
        DwgExportAdapter(oda_adapter=mock_oda, dxf_adapter=mock_dxf).export(
            result, [surface_with_opening], out
        )

    assert written_paths, "DXF should have been written"
    assert not written_paths[0].exists(), "Temp DXF must be cleaned up after failure"


# ── Performance ───────────────────────────────────────────────────────────────


def test_dxf_performance_500_panels(tmp_path: Path) -> None:
    sid = str(uuid.uuid4())
    surface = FacadeSurface(
        id=sid, plan_id="p1", page_number=1,
        boundary=[(0.0, 0.0), (20000.0, 0.0), (20000.0, 12000.0), (0.0, 12000.0)],
    )
    panels = _make_panels(sid, 500)
    result = PanelizationResult(job_id="perf", panels=panels)
    out = tmp_path / "perf.dxf"

    import time
    start = time.perf_counter()
    DxfExportAdapter().export(result, [surface], out)
    elapsed = time.perf_counter() - start

    assert elapsed < 3.0, f"500 panels took {elapsed:.2f}s (limit: 3s)"
    assert out.stat().st_size < 10 * 1024 * 1024, "DXF > 10MB for 500 panels"

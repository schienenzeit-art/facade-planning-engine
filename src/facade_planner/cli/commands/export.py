"""CLI commands for DXF and DWG export (EPIC-007, EPIC-011)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from facade_planner.application.services.project_service import ProjectService
from facade_planner.domain.exceptions import ExportError, FacadePlannerError, OdaConverterNotFoundError

app = typer.Typer(help="Panelisierungsergebnis exportieren (DXF, DWG).", no_args_is_help=True)
console = Console()


def _data_dir() -> Path:
    return Path.cwd() / ".facadeplanner"


def _load_result_and_surfaces(job_id: str):  # type: ignore[return]
    from facade_planner.infrastructure.persistence.panelization_repository import (
        FilePanelizationRepository,
    )
    from facade_planner.infrastructure.persistence.facade_surface_repository import (
        FileFacadeSurfaceRepository,
    )

    job_repo = FilePanelizationRepository(_data_dir() / "jobs")
    job = job_repo.load_job(job_id)
    result = job_repo.load_result(job_id)

    surface_repo = FileFacadeSurfaceRepository(_data_dir() / "surfaces")
    surfaces = [surface_repo.load(sid) for sid in job.surface_ids]
    return result, surfaces


@app.command("dxf")
def export_dxf(
    job_id: str = typer.Argument(..., help="Job-ID (aus 'facade panelize list')"),
    output: Path = typer.Option(
        ..., "--output", "-o", help="Ausgabepfad der .dxf-Datei"
    ),
) -> None:
    """Panelisierungsergebnis als DXF R2013 (AC1027, mm) exportieren."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        result, surfaces = _load_result_and_surfaces(job_id)

        from facade_planner.infrastructure.export.dxf_export_adapter import DxfExportAdapter

        output = output.with_suffix(".dxf")
        DxfExportAdapter().export(result, surfaces, output)

        console.print(f"[green]DXF exportiert:[/green] {output}")
        console.print(
            f"  {result.total_panels} Panels · {len(surfaces)} Fläche(n)"
        )

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e
    except ExportError as e:
        console.print(f"[red]Export-Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("dwg")
def export_dwg(
    job_id: str = typer.Argument(..., help="Job-ID (aus 'facade panelize list')"),
    output: Path = typer.Option(
        ..., "--output", "-o", help="Ausgabepfad der .dwg-Datei"
    ),
    oda_path: Optional[Path] = typer.Option(
        None,
        "--oda-path",
        help=(
            "Pfad zum ODA File Converter Binary. "
            "Standard: plattformspezifischer Standardpfad. "
            "Download: https://www.opendesign.com/guestfiles/oda_file_converter"
        ),
    ),
) -> None:
    """Panelisierungsergebnis als DWG ACAD2018 exportieren (via ODA File Converter)."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        result, surfaces = _load_result_and_surfaces(job_id)

        from facade_planner.infrastructure.export.oda_converter_adapter import OdaConverterAdapter
        from facade_planner.infrastructure.export.dwg_export_adapter import DwgExportAdapter

        oda = OdaConverterAdapter(oda_path=oda_path)
        output = output.with_suffix(".dwg")
        DwgExportAdapter(oda_adapter=oda).export(result, surfaces, output)

        console.print(f"[green]DWG exportiert:[/green] {output}")
        console.print(
            f"  {result.total_panels} Panels · {len(surfaces)} Fläche(n) · Format: ACAD2018"
        )

    except OdaConverterNotFoundError as e:
        console.print(f"[red]ODA File Converter nicht gefunden:[/red]\n{e}")
        raise typer.Exit(1) from e
    except ExportError as e:
        console.print(f"[red]Export-Fehler:[/red] {e}")
        raise typer.Exit(1) from e
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e

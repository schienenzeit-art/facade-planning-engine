from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from facade_planner.application.services.project_service import ProjectService
from facade_planner.application.use_cases.calibrate_scale import (
    DirectScaleInputUseCase,
    TwoPointCalibrationUseCase,
)
from facade_planner.domain.exceptions import FacadePlannerError

app = typer.Typer(help="Manage facade plans (PDF import, scale calibration).", no_args_is_help=True)
console = Console()


def _not_implemented(cmd: str) -> None:
    console.print(f"[yellow]Not implemented yet:[/yellow] facade plan {cmd}")
    raise typer.Exit(1)


@app.command("scale")
def scale(
    page: int = typer.Option(1, "--page", "-p", help="Plan page number to calibrate"),
    scale_ratio: Optional[int] = typer.Option(
        None,
        "--ratio",
        "-r",
        help="Scale denominator for 1:N (e.g. 100 for 1:100).",
    ),
    pdf_dist: Optional[float] = typer.Option(
        None,
        "--pdf-dist",
        help="Measured distance in PDF units (for two-point calibration).",
    ),
    real_dist: Optional[float] = typer.Option(
        None,
        "--real-dist",
        help="Corresponding real distance in mm (for two-point calibration).",
    ),
) -> None:
    """Calibrate the scale of a plan page.

    \b
    Two modes:
      Direct:      --ratio 100          (1:100 architectural scale)
      Two-point:   --pdf-dist 283.5 --real-dist 6000   (measure a known distance)
    """
    try:
        ProjectService(Path.cwd()).require_initialized()

        if scale_ratio is not None:
            uc = DirectScaleInputUseCase()
            calibration = uc.execute(scale_ratio)
        elif pdf_dist is not None and real_dist is not None:
            uc_tp = TwoPointCalibrationUseCase()
            calibration = uc_tp.execute(pdf_dist, real_dist)
        else:
            console.print(
                "[red]Fehler:[/red] Entweder --ratio oder (--pdf-dist + --real-dist) angeben."
            )
            raise typer.Exit(1)

        table = Table(title=f"Kalibrierung Seite {page}")
        table.add_column("Eigenschaft", style="cyan")
        table.add_column("Wert")
        table.add_row("Methode", calibration.method.value)
        table.add_row("Faktor", f"{calibration.factor:.6f} mm/unit")
        table.add_row("Beschreibung", calibration.description)
        console.print(table)
        console.print(
            "[dim]Hinweis: Kalibrierung wird beim PDF-Import auf Seite angewendet.[/dim]"
        )
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("import")
def import_plan(
    path: Path = typer.Argument(..., help="Pfad zur PDF-Datei"),
) -> None:
    """Import a PDF plan file (not yet implemented)."""
    _not_implemented("import")


@app.command("list")
def list_plans() -> None:
    """List all imported plans (not yet implemented)."""
    _not_implemented("list")

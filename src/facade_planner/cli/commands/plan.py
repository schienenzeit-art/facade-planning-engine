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
    pdf_path: Path = typer.Argument(..., help="Pfad zur PDF-Datei"),
    name: str = typer.Option("", "--name", "-n", help="Plan-Name (Standard: Dateiname)"),
) -> None:
    """Import a PDF plan and extract vector geometry."""
    import warnings
    from facade_planner.infrastructure.adapters.pdf_import_adapter import PDFImportAdapter
    from facade_planner.infrastructure.persistence.facade_plan_repository import FileFacadePlanRepository

    try:
        project = ProjectService(Path.cwd()).require_initialized()

        if not pdf_path.exists():
            console.print(f"[red]Fehler:[/red] Datei nicht gefunden: {pdf_path}")
            raise typer.Exit(1)

        plan_name = name or pdf_path.stem

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            adapter = PDFImportAdapter()
            plan = adapter.import_plan(pdf_path, plan_name)

        for w in caught:
            console.print(f"[yellow]Warnung:[/yellow] {w.message}")

        plans_dir = Path.cwd() / ".facadeplanner" / "plans"
        repo = FileFacadePlanRepository(plans_dir)
        repo.save(plan)

        table = Table(title=f"Plan importiert: {plan.name}")
        table.add_column("Eigenschaft", style="cyan")
        table.add_column("Wert")
        table.add_row("ID", plan.id)
        table.add_row("Generator", plan.pdf_source.value)
        table.add_row("Seiten", str(plan.page_count))
        table.add_row("Geometrien (gesamt)", str(plan.total_geometry_count))
        table.add_row("Quelle", plan.source_path)
        console.print(table)
        console.print("[dim]Kalibrierung: 'facade plan scale --ratio 100' (oder --pdf-dist/--real-dist)[/dim]")
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("list")
def list_plans() -> None:
    """List all imported plans."""
    from facade_planner.infrastructure.persistence.facade_plan_repository import FileFacadePlanRepository

    try:
        ProjectService(Path.cwd()).require_initialized()
        plans_dir = Path.cwd() / ".facadeplanner" / "plans"
        repo = FileFacadePlanRepository(plans_dir)
        plans = repo.list_all()

        if not plans:
            console.print("[yellow]Keine Pläne importiert.[/yellow]")
            return

        table = Table(title="Importierte Pläne")
        table.add_column("ID", style="dim", width=10)
        table.add_column("Name")
        table.add_column("Generator", width=10)
        table.add_column("Seiten", width=6)
        table.add_column("Geometrien", width=12)
        table.add_column("Importiert")

        for plan in plans:
            table.add_row(
                plan.id[:8],
                plan.name,
                plan.pdf_source.value,
                str(plan.page_count),
                str(plan.total_geometry_count),
                plan.imported_at.strftime("%Y-%m-%d %H:%M"),
            )
        console.print(table)
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e

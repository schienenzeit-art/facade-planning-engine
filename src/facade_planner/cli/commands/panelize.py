"""CLI commands for running and inspecting panelization jobs (EPIC-006)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from facade_planner.application.services.project_service import ProjectService
from facade_planner.domain.entities.panelization_job import (
    PanelizationConfig,
)
from facade_planner.domain.enums import RuleSeverity
from facade_planner.domain.exceptions import FacadePlannerError
from facade_planner.domain.value_objects.joint_config import JointConfig

app = typer.Typer(help="Run panelization jobs.", no_args_is_help=True)
console = Console()


def _data_dir() -> Path:
    return Path.cwd() / ".facadeplanner"


def _job_repo():
    from facade_planner.infrastructure.persistence.panelization_repository import (
        FilePanelizationRepository,
    )
    return FilePanelizationRepository(_data_dir() / "jobs")


@app.command("run")
def run_panelization(
    catalog: list[str] = typer.Option(
        [],
        "--catalog",
        "-c",
        help="Katalog-ID(s) (mehrfach verwendbar). Leer = alle importierten Kataloge.",
    ),
    surface: list[str] = typer.Option(
        [],
        "--surface",
        "-s",
        help="Flaechen-ID(s) (mehrfach verwendbar). Leer = alle bestaetigten Flaechen.",
    ),
    joint_h: float = typer.Option(
        10.0, "--joint-h", help="Horizontale Fugenbreite in mm (Standard: 10mm)."
    ),
    joint_v: float = typer.Option(
        10.0, "--joint-v", help="Vertikale Fugenbreite in mm (Standard: 10mm)."
    ),
    expansion_interval: float = typer.Option(
        6000.0,
        "--expansion-interval",
        help="Bewegungsfugen-Intervall in mm (0 = deaktiviert, Standard: 6000mm).",
    ),
    expansion_width: float = typer.Option(
        20.0,
        "--expansion-width",
        help="Bewegungsfugen-Breite in mm (Standard: 20mm).",
    ),
    min_panel_w: float = typer.Option(
        100.0, "--min-panel-w", help="Mindest-Panelbreite in mm (Standard: 100mm)."
    ),
    min_panel_h: float = typer.Option(
        100.0, "--min-panel-h", help="Mindest-Panelhoehe in mm (Standard: 100mm)."
    ),
) -> None:
    """Run a panelization job on confirmed surfaces using imported catalog formats."""
    try:
        project = ProjectService(Path.cwd()).require_initialized()

        from facade_planner.application.use_cases.panelize import PanelizeUseCase

        jc = JointConfig(
            horizontal_joint_mm=joint_h,
            vertical_joint_mm=joint_v,
            expansion_joint_interval_mm=expansion_interval,
            expansion_joint_width_mm=expansion_width,
        )
        cfg = PanelizationConfig(
            joint_config=jc,
            min_panel_width_mm=min_panel_w,
            min_panel_height_mm=min_panel_h,
        )

        uc = PanelizeUseCase(_data_dir())
        job, result = uc.execute(
            project_id=project.id,
            catalog_ids=list(catalog),
            surface_ids=list(surface) if surface else None,
            config=cfg,
        )

        # Summary table
        table = Table(title=f"Panelisierung abgeschlossen: {job.id}")
        table.add_column("Eigenschaft", style="cyan")
        table.add_column("Wert")
        table.add_row("Job-ID", job.id)
        table.add_row("Status", f"[green]{job.status.value}[/green]" if job.status.value == "COMPLETED" else f"[yellow]{job.status.value}[/yellow]")
        table.add_row("Panels total", str(result.total_panels))
        table.add_row("  davon Vollplatten", str(result.full_panels))
        table.add_row("  davon Schnittplatten", str(result.cut_panels))
        table.add_row("Flaechen mit Fehler", str(len(result.failed_surface_ids)))
        table.add_row("Regel-Warnungen", str(len(result.rule_violations)))
        console.print(table)

        if result.surface_errors:
            console.print("\n[red]Fehler pro Flaeche:[/red]")
            for err in result.surface_errors:
                console.print(f"  [{err.error_type}] {err.surface_id}: {err.message}")

        if result.rule_violations:
            _print_violations(result.rule_violations)

        console.print(
            f"\n[dim]Details: [bold]facade panelize show {job.id}[/bold][/dim]"
        )

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("list")
def list_jobs() -> None:
    """List all panelization jobs."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        jobs = _job_repo().list_jobs()

        if not jobs:
            console.print("[yellow]Keine Panelisierungs-Jobs vorhanden.[/yellow]")
            console.print("Tipp: [bold]facade panelize run --catalog <id>[/bold]")
            return

        table = Table(title="Panelisierungs-Jobs")
        table.add_column("Job-ID", style="cyan")
        table.add_column("Erstellt")
        table.add_column("Status")
        table.add_column("Flaechen", justify="right")
        table.add_column("Kataloge")

        for job in sorted(jobs, key=lambda j: j.created_at, reverse=True):
            status_str = (
                f"[green]{job.status.value}[/green]"
                if job.status.value == "COMPLETED"
                else f"[yellow]{job.status.value}[/yellow]"
                if job.status.value == "RUNNING"
                else f"[red]{job.status.value}[/red]"
                if job.status.value == "FAILED"
                else job.status.value
            )
            table.add_row(
                job.id,
                job.created_at.strftime("%Y-%m-%d %H:%M"),
                status_str,
                str(len(job.surface_ids)),
                ", ".join(job.catalog_ids) or "—",
            )
        console.print(table)

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("show")
def show_job(
    job_id: str = typer.Argument(..., help="Job-ID (aus 'facade panelize list')"),
    panels: bool = typer.Option(False, "--panels", help="Alle Panels anzeigen"),
) -> None:
    """Show details of a panelization job including violations and errors."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        repo = _job_repo()
        job = repo.load_job(job_id)

        # Job info
        info = Table(title=f"Job: {job_id}")
        info.add_column("Eigenschaft", style="cyan")
        info.add_column("Wert")
        info.add_row("Status", job.status.value)
        info.add_row("Erstellt", job.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        info.add_row("Abgeschlossen", job.completed_at.strftime("%Y-%m-%d %H:%M:%S") if job.completed_at else "—")
        info.add_row("Flaechen", ", ".join(job.surface_ids) or "—")
        info.add_row("Kataloge", ", ".join(job.catalog_ids) or "alle")
        jc = job.config.joint_config
        info.add_row("Fuge H/V mm", f"{jc.horizontal_joint_mm} / {jc.vertical_joint_mm}")
        info.add_row("Bewegungsfuge Intervall mm", str(jc.expansion_joint_interval_mm))
        console.print(info)

        if not repo.exists_result(job_id):
            console.print("[yellow]Kein Ergebnis gespeichert.[/yellow]")
            return

        result = repo.load_result(job_id)

        # Summary
        summary = Table(title="Ergebnis")
        summary.add_column("Kennzahl", style="cyan")
        summary.add_column("Wert", justify="right")
        summary.add_row("Panels total", str(result.total_panels))
        summary.add_row("  Vollplatten", str(result.full_panels))
        summary.add_row("  Schnittplatten", str(result.cut_panels))
        summary.add_row("Flaechen mit Fehler", str(len(result.failed_surface_ids)))
        summary.add_row("Regel-Verletzungen", str(len(result.rule_violations)))
        console.print(summary)

        if result.surface_errors:
            console.print("\n[red]Flaechen-Fehler:[/red]")
            for err in result.surface_errors:
                console.print(f"  [{err.error_type}] {err.surface_id}: {err.message}")

        if result.rule_violations:
            _print_violations(result.rule_violations)

        if panels and result.panels:
            pt = Table(title=f"Panels ({result.total_panels})")
            pt.add_column("Panel-ID")
            pt.add_column("Format")
            pt.add_column("X mm", justify="right")
            pt.add_column("Y mm", justify="right")
            pt.add_column("B mm", justify="right")
            pt.add_column("H mm", justify="right")
            pt.add_column("Schnitt")
            for p in result.panels[:200]:
                pt.add_row(
                    p.id,
                    p.format_code,
                    f"{p.x_mm:.0f}",
                    f"{p.y_mm:.0f}",
                    f"{p.actual_width_mm:.0f}",
                    f"{p.actual_height_mm:.0f}",
                    "✓" if p.is_cut else "",
                )
            if result.total_panels > 200:
                console.print(f"[dim]... {result.total_panels - 200} weitere Panels nicht angezeigt.[/dim]")
            console.print(pt)

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


def _print_violations(violations) -> None:
    vt = Table(title="Regel-Verletzungen")
    vt.add_column("Regel", style="cyan", width=8)
    vt.add_column("Schwere", width=9)
    vt.add_column("Meldung")
    for v in violations:
        sev = v.severity if isinstance(v.severity, str) else v.severity.value
        color = "red" if sev == RuleSeverity.ERROR.value else "yellow" if sev == RuleSeverity.WARNING.value else "dim"
        vt.add_row(v.rule_id, f"[{color}]{sev}[/{color}]", v.message[:80])
    console.print(vt)

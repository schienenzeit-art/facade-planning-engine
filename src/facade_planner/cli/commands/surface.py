"""CLI commands for surface detection and management (EPIC-003)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from facade_planner.application.services.project_service import ProjectService
from facade_planner.application.use_cases.detect_surfaces import DetectSurfacesUseCase
from facade_planner.domain.enums import SurfaceStatus
from facade_planner.domain.exceptions import FacadePlannerError
from facade_planner.domain.services.surface_detection_service import SurfaceDetectionConfig
from facade_planner.infrastructure.persistence.facade_plan_repository import (
    FileFacadePlanRepository,
)
from facade_planner.infrastructure.persistence.facade_surface_repository import (
    FileFacadeSurfaceRepository,
)

app = typer.Typer(help="Detect and manage facade surfaces.", no_args_is_help=True)
console = Console()


def _surface_repo() -> FileFacadeSurfaceRepository:
    return FileFacadeSurfaceRepository(Path.cwd() / ".facadeplanner" / "surfaces")


def _plan_repo() -> FileFacadePlanRepository:
    return FileFacadePlanRepository(Path.cwd() / ".facadeplanner" / "plans")


_STATUS_STYLE: dict[SurfaceStatus, str] = {
    SurfaceStatus.DETECTED: "yellow",
    SurfaceStatus.CONFIRMED: "green",
    SurfaceStatus.REJECTED: "red",
}


@app.command("detect")
def detect(
    plan_id: str = typer.Argument(..., help="Plan-ID (aus 'facade plan list')"),
    page: int = typer.Option(1, "--page", "-p", help="Seitennummer (1-basiert, Standard: 1)"),
    min_area: float = typer.Option(
        100_000.0,
        "--min-area",
        help="Minimale Fläche in mm² (Standard: 100000 = 0.1 m²)",
    ),
    max_area: Optional[float] = typer.Option(
        None,
        "--max-area",
        help="Maximale Fläche in mm² (kein Limit per Default)",
    ),
    gap_tolerance: float = typer.Option(
        0.5,
        "--gap-tolerance",
        help="Max. Endpunkt-Abstand in mm zum Schliessen offener Pfade (Standard: 0.5)",
    ),
) -> None:
    """Detect facade surfaces from a calibrated plan page.

    \b
    Prerequisites:
      1. Plan imported:   facade plan import <pdf>
      2. Page calibrated: facade plan scale --ratio 100

    Detected surfaces are saved and can be reviewed with 'facade surface list'.
    Confirm or reject them with 'facade surface confirm / reject'.
    """
    try:
        ProjectService(Path.cwd()).require_initialized()

        plan = _plan_repo().load(plan_id)
        config = SurfaceDetectionConfig(
            min_area_mm2=min_area,
            max_area_mm2=max_area,
            gap_tolerance_mm=gap_tolerance,
        )
        uc = DetectSurfacesUseCase()
        surfaces = uc.execute(plan, page, config)

        if not surfaces:
            console.print(
                f"[yellow]Keine Flächen erkannt[/yellow] auf Seite {page} "
                f"(Mindestfläche {min_area:.0f} mm²)."
            )
            console.print(
                "Tipp: --min-area verkleinern oder Seite zuerst kalibrieren "
                "('facade plan scale ...')."
            )
            return

        repo = _surface_repo()
        for surface in surfaces:
            repo.save(surface)

        table = Table(title=f"Erkannte Flächen — Plan {plan_id[:8]} / Seite {page}")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Brutto-Fläche m²", justify="right")
        table.add_column("Breite mm", justify="right")
        table.add_column("Höhe mm", justify="right")
        table.add_column("Eckpunkte", justify="right")
        table.add_column("Status")

        for s in surfaces:
            table.add_row(
                s.id[:8],
                f"{s.gross_area_mm2 / 1_000_000:.3f}",
                f"{s.width_mm:.0f}",
                f"{s.height_mm:.0f}",
                str(len(s.boundary)),
                s.status.value,
            )
        console.print(table)
        console.print(
            f"\n[green]{len(surfaces)} Fläche(n) gespeichert.[/green] "
            "Überprüfen: [bold]facade surface list[/bold]"
        )

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("list")
def list_surfaces(
    plan_id: Optional[str] = typer.Option(
        None,
        "--plan",
        help="Nur Flächen dieses Plans anzeigen.",
    ),
    status_filter: Optional[str] = typer.Option(
        None,
        "--status",
        help="Filtern nach Status: DETECTED, CONFIRMED, REJECTED",
    ),
) -> None:
    """List all detected surfaces."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        repo = _surface_repo()

        surfaces = repo.list_by_plan(plan_id) if plan_id else repo.list_all()

        if status_filter:
            try:
                sf = SurfaceStatus(status_filter.upper())
            except ValueError:
                console.print(f"[red]Unbekannter Status:[/red] {status_filter}")
                raise typer.Exit(1)
            surfaces = [s for s in surfaces if s.status == sf]

        if not surfaces:
            console.print("[yellow]Keine Flächen gefunden.[/yellow]")
            console.print("Tipp: [bold]facade surface detect <plan-id>[/bold]")
            return

        table = Table(title=f"Flächen ({len(surfaces)} gesamt)")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Plan-ID", style="dim", width=8)
        table.add_column("Seite", width=5)
        table.add_column("Brutto m²", justify="right")
        table.add_column("Netto m²", justify="right")
        table.add_column("Status")
        table.add_column("Zone", style="dim")

        for s in surfaces:
            style = _STATUS_STYLE.get(s.status, "")
            table.add_row(
                s.id[:8],
                s.plan_id[:8],
                str(s.page_number),
                f"{s.gross_area_mm2 / 1_000_000:.3f}",
                f"{s.net_area_mm2 / 1_000_000:.3f}",
                f"[{style}]{s.status.value}[/{style}]",
                s.zone_id or "—",
            )
        console.print(table)

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("confirm")
def confirm_surface(
    surface_id: str = typer.Argument(..., help="Surface-ID (aus 'facade surface list')"),
    zone_id: Optional[str] = typer.Option(None, "--zone", help="Zone-ID zuweisen"),
) -> None:
    """Confirm a detected surface (marks it as usable for panelization)."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        repo = _surface_repo()
        surface = repo.load(surface_id)
        surface.confirm(zone_id=zone_id)
        repo.save(surface)
        console.print(
            f"[green]Fläche bestätigt:[/green] {surface_id[:8]} "
            f"— {surface.gross_area_mm2 / 1_000_000:.3f} m²"
        )
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("reject")
def reject_surface(
    surface_id: str = typer.Argument(..., help="Surface-ID"),
    reason: str = typer.Option("", "--reason", "-r", help="Ablehnungsgrund"),
) -> None:
    """Reject a detected surface (e.g. title block, annotation area)."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        repo = _surface_repo()
        surface = repo.load(surface_id)
        surface.reject(reason=reason)
        repo.save(surface)
        console.print(f"[yellow]Fläche abgelehnt:[/yellow] {surface_id[:8]}")
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("detect-openings")
def detect_openings(
    surface_id: str = typer.Argument(..., help="Surface-ID (aus 'facade surface list')"),
    tolerance: float = typer.Option(
        1.0, "--tolerance", "-t", help="Toleranz in mm fuer Polygon-Einschluss (Standard: 1mm)."
    ),
    max_area: Optional[float] = typer.Option(
        None,
        "--max-area",
        help="Maximale Kandidaten-Flaeche in mm² (kein Limit per Default).",
    ),
    replace: bool = typer.Option(
        False,
        "--replace",
        help="Bestehende Oeffnungen loeschen und neu erkennen.",
    ),
) -> None:
    """Detect openings (windows/doors) in a surface from its plan geometries.

    \b
    Reads raw geometries from the plan page that contains the surface.
    Closed polygons smaller than the surface and passing containment checks
    are added as openings (type: WINDOW / DOOR / OTHER).

    Use --replace to clear existing openings and re-run detection.
    """
    try:
        ProjectService(Path.cwd()).require_initialized()

        from facade_planner.application.use_cases.detect_openings import (
            DetectOpeningsUseCase,
            openings_from_plan_page,
        )

        data_dir = Path.cwd() / ".facadeplanner"
        repo = _surface_repo()
        surface = repo.load(surface_id)

        # Auto-extract candidates from the plan page
        candidates = openings_from_plan_page(surface, data_dir, max_opening_area_mm2=max_area)

        if not candidates:
            console.print(
                f"[yellow]Keine Kandidaten gefunden[/yellow] auf Plan-Seite "
                f"{surface.plan_id[:8]}/Seite {surface.page_number}."
            )
            console.print(
                "Tipp: Seite muss kalibriert sein und geschlossene Polygone enthalten."
            )
            return

        uc = DetectOpeningsUseCase(data_dir)
        result = uc.execute(
            surface_id=surface_id,
            candidate_boundaries=candidates,
            tolerance_mm=tolerance,
            replace_existing=replace,
        )

        if result.warnings:
            for w in result.warnings:
                console.print(f"[yellow]Warnung:[/yellow] {w}")

        if not result.openings:
            console.print(
                f"[yellow]Keine Oeffnungen erkannt[/yellow] in {surface_id[:8]} "
                f"({len(candidates)} Kandidaten geprueft)."
            )
            return

        table = Table(title=f"Erkannte Oeffnungen — {surface_id[:8]}")
        table.add_column("ID", style="dim", width=12)
        table.add_column("Typ")
        table.add_column("Flaeche m²", justify="right")
        table.add_column("Eckpunkte", justify="right")

        for opening in result.openings:
            table.add_row(
                opening.id,
                opening.opening_type.value,
                f"{opening.area_mm2 / 1_000_000:.4f}",
                str(len(opening.boundary)),
            )
        console.print(table)
        console.print(
            f"\n[green]{len(result.openings)} Oeffnung(en) gespeichert.[/green]"
        )

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("show")
def show_surface(
    surface_id: str = typer.Argument(..., help="Surface-ID"),
) -> None:
    """Show details of a surface including openings."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        repo = _surface_repo()
        surface = repo.load(surface_id)

        info = Table(title=f"Surface: {surface_id[:8]}")
        info.add_column("Eigenschaft", style="cyan")
        info.add_column("Wert")
        info.add_row("ID", surface.id)
        info.add_row("Plan", surface.plan_id[:8])
        info.add_row("Seite", str(surface.page_number))
        info.add_row("Status", surface.status.value)
        info.add_row("Zone", surface.zone_id or "—")
        info.add_row("Brutto m²", f"{surface.gross_area_mm2 / 1_000_000:.4f}")
        info.add_row("Netto m²", f"{surface.net_area_mm2 / 1_000_000:.4f}")
        info.add_row("Breite mm", f"{surface.width_mm:.0f}")
        info.add_row("Hoehe mm", f"{surface.height_mm:.0f}")
        info.add_row("Oeffnungen", str(len(surface.openings)))
        console.print(info)

        if surface.openings:
            ot = Table(title="Oeffnungen")
            ot.add_column("ID", style="dim")
            ot.add_column("Typ")
            ot.add_column("Flaeche m²", justify="right")
            for o in surface.openings:
                ot.add_row(o.id, o.opening_type.value, f"{o.area_mm2 / 1_000_000:.4f}")
            console.print(ot)

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e

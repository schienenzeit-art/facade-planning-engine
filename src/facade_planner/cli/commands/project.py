from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from facade_planner.application.services.project_service import ProjectService
from facade_planner.domain.exceptions import FacadePlannerError

app = typer.Typer(help="Manage facade planning projects.", no_args_is_help=True)
console = Console()


@app.command("create")
def create(
    name: str = typer.Argument(..., help="Project name"),
) -> None:
    """Create a new facade planning project in the current directory."""
    try:
        svc = ProjectService(Path.cwd())
        project = svc.create_project(name)
        console.print(f"[green]Projekt erstellt:[/green] {project.name}")
        console.print(f"  Verzeichnis: {project.data_path}")
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("info")
def info() -> None:
    """Show information about the current project."""
    try:
        svc = ProjectService(Path.cwd())
        project = svc.require_initialized()
        table = Table(title=f"Projekt: {project.name}")
        table.add_column("Eigenschaft", style="cyan")
        table.add_column("Wert")
        table.add_row("ID", project.id)
        table.add_row("Name", project.name)
        table.add_row("Pfad", project.path)
        table.add_row("Erstellt", project.created_at.strftime("%Y-%m-%d %H:%M"))
        console.print(table)
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from facade_planner.application.services.project_service import ProjectService
from facade_planner.domain.enums import RuleSeverity
from facade_planner.domain.exceptions import FacadePlannerError
from facade_planner.infrastructure.persistence.rule_catalog_repository import (
    FileRuleCatalogRepository,
)

app = typer.Typer(help="View and configure planning rules.", no_args_is_help=True)
console = Console()

_SEVERITY_STYLE: dict[RuleSeverity, str] = {
    RuleSeverity.ERROR: "red",
    RuleSeverity.WARNING: "yellow",
    RuleSeverity.INFO: "cyan",
}


def _get_repo() -> FileRuleCatalogRepository:
    return FileRuleCatalogRepository(Path.cwd() / ".facadeplanner")


@app.command("list")
def list_rules(
    active_only: bool = typer.Option(False, "--active-only", help="Show only active rules"),
) -> None:
    """List all planning rules and their current status."""
    try:
        svc = ProjectService(Path.cwd())
        project = svc.require_initialized()
        repo = _get_repo()
        catalog = repo.load_or_create(project.id)

        rules = catalog.get_active_rules() if active_only else sorted(catalog.rules.values(), key=lambda r: r.id)
        if not rules:
            console.print("[yellow]Keine Regeln gefunden.[/yellow]")
            return

        table = Table(title="Planungsregeln", show_lines=True)
        table.add_column("ID", style="bold", width=8)
        table.add_column("Name")
        table.add_column("Kategorie", width=12)
        table.add_column("Schwere", width=10)
        table.add_column("Aktiv", width=6)
        table.add_column("Builtin", width=8)
        table.add_column("Parameter")

        for rule in rules:
            sev_style = _SEVERITY_STYLE.get(rule.severity, "white")
            params = ", ".join(f"{k}={v}" for k, v in rule.parameters.items()) or "—"
            table.add_row(
                rule.id,
                rule.name,
                rule.category.value,
                f"[{sev_style}]{rule.severity.value}[/{sev_style}]",
                "[green]Ja[/green]" if rule.is_active else "[dim]Nein[/dim]",
                "Ja" if rule.is_builtin else "Nein",
                params,
            )
        console.print(table)
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("disable")
def disable_rule(
    rule_id: str = typer.Argument(..., help="Regel-ID (z.B. GR-009)"),
) -> None:
    """Deactivate a rule (builtin rules can only be disabled, not deleted)."""
    try:
        svc = ProjectService(Path.cwd())
        project = svc.require_initialized()
        repo = _get_repo()
        catalog = repo.load_or_create(project.id)
        catalog.deactivate_rule(rule_id)
        repo.save(catalog)
        console.print(f"[yellow]Regel deaktiviert:[/yellow] {rule_id}")
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("enable")
def enable_rule(
    rule_id: str = typer.Argument(..., help="Regel-ID (z.B. GR-009)"),
) -> None:
    """Activate a previously disabled rule."""
    try:
        svc = ProjectService(Path.cwd())
        project = svc.require_initialized()
        repo = _get_repo()
        catalog = repo.load_or_create(project.id)
        catalog.activate_rule(rule_id)
        repo.save(catalog)
        console.print(f"[green]Regel aktiviert:[/green] {rule_id}")
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("configure")
def configure_rule(
    rule_id: str = typer.Argument(..., help="Regel-ID (z.B. GR-008)"),
    params: list[str] = typer.Argument(..., help="Parameter als key=value (z.B. expansion_joint_interval_mm=4000)"),
) -> None:
    """Set rule parameters (key=value pairs)."""
    try:
        svc = ProjectService(Path.cwd())
        project = svc.require_initialized()
        repo = _get_repo()
        catalog = repo.load_or_create(project.id)

        parsed: dict[str, float | str] = {}
        for param in params:
            if "=" not in param:
                console.print(f"[red]Fehler:[/red] Parameter muss 'key=value' sein, got: '{param}'")
                raise typer.Exit(1)
            key, _, raw_value = param.partition("=")
            try:
                parsed[key.strip()] = float(raw_value.strip())
            except ValueError:
                parsed[key.strip()] = raw_value.strip()

        catalog.configure_rule(rule_id, parsed)
        repo.save(catalog)
        console.print(f"[green]Regel konfiguriert:[/green] {rule_id} — {parsed}")
    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e

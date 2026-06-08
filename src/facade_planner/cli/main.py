import typer
from rich.console import Console

from facade_planner import __version__
from facade_planner.cli.commands import catalog, export, panelize, plan, project, rules, surface, zone

app = typer.Typer(
    name="facade",
    help="Facade Planning Engine — Automated facade panelization from PDF plans.",
    no_args_is_help=True,
)
console = Console()

app.add_typer(project.app, name="project")
app.add_typer(plan.app, name="plan")
app.add_typer(surface.app, name="surface")
app.add_typer(zone.app, name="zone")
app.add_typer(catalog.app, name="catalog")
app.add_typer(rules.app, name="rules")
app.add_typer(panelize.app, name="panelize")
app.add_typer(export.app, name="export")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"facade-planning-engine v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(  # noqa: FBT001
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    pass


if __name__ == "__main__":
    app()

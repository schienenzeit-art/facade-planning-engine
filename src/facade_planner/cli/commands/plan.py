import typer
from rich.console import Console

app = typer.Typer(help="Manage facade plans (PDF import, scale calibration).", no_args_is_help=True)
console = Console()


def _not_implemented(cmd: str) -> None:
    console.print(f"[yellow]Not implemented yet:[/yellow] facade plan {cmd}")
    raise typer.Exit(1)


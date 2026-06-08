import typer
from rich.console import Console

app = typer.Typer(help="Run panelization jobs.", no_args_is_help=True)
console = Console()


def _not_implemented(cmd: str) -> None:
    console.print(f"[yellow]Not implemented yet:[/yellow] facade panelize {cmd}")
    raise typer.Exit(1)


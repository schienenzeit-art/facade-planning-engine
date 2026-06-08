import typer
from rich.console import Console

app = typer.Typer(help="Export results (DXF, report).", no_args_is_help=True)
console = Console()


def _not_implemented(cmd: str) -> None:
    console.print(f"[yellow]Not implemented yet:[/yellow] facade export {cmd}")
    raise typer.Exit(1)


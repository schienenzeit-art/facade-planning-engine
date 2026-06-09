from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from facade_planner.application.services.catalog_import_service import (
    BUNDLED_CATALOGS,
    CatalogImportService,
)
from facade_planner.application.services.project_service import ProjectService
from facade_planner.domain.exceptions import FacadePlannerError
from facade_planner.infrastructure.persistence.supplier_catalog_repository import (
    FileSupplierCatalogRepository,
)

app = typer.Typer(help="Import and manage supplier format catalogs.", no_args_is_help=True)
console = Console()


def _get_repo() -> FileSupplierCatalogRepository:
    return FileSupplierCatalogRepository(Path.cwd() / ".facadeplanner" / "catalogs")


@app.command("import")
def import_catalog(
    name_or_path: str = typer.Argument(
        ...,
        help=(
            "Katalog-Name (z.B. 'swisspearl', 'alucobond-a2') "
            "oder Pfad zu einer JSON-Datei."
        ),
    ),
    overwrite: bool = typer.Option(False, "--overwrite", "-f", help="Bestehenden Katalog überschreiben"),
) -> None:
    """Import a supplier catalog into the project.

    \b
    Bundled catalogs (no download required):
      swisspearl        Swisspearl 2026 Facade DE/AT (17 Formate)
      alucobond-a2      ALUCOBOND A2, A2-s1,d0 (11 Formate)
      alucobond-plus    ALUCOBOND PLUS, B1 (10 Formate)
      alucobond-standard  ALUCOBOND Standard, B2 (10 Formate)

    Or pass a path to any compatible JSON file.
    """
    try:
        ProjectService(Path.cwd()).require_initialized()
        svc = CatalogImportService()
        repo = _get_repo()

        # Decide: bundled name or file path?
        if name_or_path in BUNDLED_CATALOGS:
            catalog = svc.import_bundled(name_or_path)
        else:
            file_path = Path(name_or_path)
            catalog = svc.import_from_file(file_path)

        if repo.exists(catalog.id) and not overwrite:
            console.print(
                f"[yellow]Katalog '{catalog.id}' bereits importiert.[/yellow] "
                "Verwende --overwrite zum Überschreiben."
            )
            raise typer.Exit(1)

        repo.save(catalog)

        table = Table(title=f"Katalog importiert: {catalog.supplier_name}")
        table.add_column("Eigenschaft", style="cyan")
        table.add_column("Wert")
        table.add_row("ID", catalog.id)
        table.add_row("Lieferant", catalog.supplier_name)
        table.add_row("Formate (total)", str(len(catalog.formats)))
        table.add_row("Formate (aktiv)", str(len(catalog.active_formats)))
        table.add_row("Regeln", str(len(catalog.rules_raw)))
        table.add_row("Quelle", catalog.source_path)
        console.print(table)

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("list")
def list_catalogs() -> None:
    """List all imported supplier catalogs."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        catalogs = _get_repo().list_all()

        if not catalogs:
            console.print("[yellow]Keine Kataloge importiert.[/yellow]")
            console.print(
                "Tipp: [bold]facade catalog import swisspearl[/bold] oder "
                "[bold]facade catalog import alucobond-a2[/bold]"
            )
            return

        table = Table(title="Importierte Lieferantenkataloge")
        table.add_column("ID")
        table.add_column("Lieferant")
        table.add_column("Formate", width=8)
        table.add_column("Importiert")
        table.add_column("Quelle", style="dim")

        for cat in catalogs:
            table.add_row(
                cat.id,
                cat.supplier_name,
                str(len(cat.active_formats)),
                cat.imported_at.strftime("%Y-%m-%d %H:%M"),
                Path(cat.source_path).name if cat.source_path else "—",
            )
        console.print(table)

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("show")
def show_catalog(
    catalog_id: str = typer.Argument(..., help="Katalog-ID (aus 'facade catalog list')"),
    inactive: bool = typer.Option(False, "--inactive", help="Auch inaktive Formate anzeigen"),
) -> None:
    """Show all formats in a catalog."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        catalog = _get_repo().load(catalog_id)
        formats = catalog.formats if inactive else catalog.active_formats

        if not formats:
            console.print("[yellow]Keine Formate gefunden.[/yellow]")
            return

        table = Table(title=f"{catalog.supplier_name} — {catalog_id} ({len(formats)} Formate)")
        table.add_column("Format-Code", style="bold")
        table.add_column("Breite mm", justify="right")
        table.add_column("Höhe mm", justify="right")
        table.add_column("Stärke mm", justify="right")
        table.add_column("kg/m²", justify="right")
        table.add_column("Beschreibung")

        for fmt in sorted(formats, key=lambda f: f.format_code):
            table.add_row(
                fmt.format_code,
                f"{fmt.width_mm:.0f}",
                f"{fmt.height_mm:.0f}",
                f"{fmt.thickness_mm:.1f}" if fmt.thickness_mm else "—",
                f"{fmt.weight_kg_m2:.1f}" if fmt.weight_kg_m2 else "—",
                fmt.description,
            )
        console.print(table)

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("available")
def list_available() -> None:
    """List bundled catalogs available for import (no download required)."""
    table = Table(title="Verfügbare Bundled-Kataloge")
    table.add_column("Name", style="bold cyan")
    table.add_column("Lieferant")
    table.add_column("Datei")

    descriptions = {
        "swisspearl": ("Swisspearl", "swisspearl_2026_facade_DE-AT.json"),
        "alucobond-a2": ("ALUCOBOND", "alucobond_a2.json"),
        "alucobond-plus": ("ALUCOBOND", "alucobond_plus.json"),
        "alucobond-standard": ("ALUCOBOND", "alucobond_standard.json"),
    }
    for name, (supplier, filename) in descriptions.items():
        table.add_row(name, supplier, filename)

    console.print(table)
    console.print("\nImport: [bold]facade catalog import <name>[/bold]")


@app.command("delete")
def delete_catalog(
    catalog_id: str = typer.Argument(..., help="Katalog-ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Ohne Rückfrage löschen"),
) -> None:
    """Remove a catalog from the project."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        repo = _get_repo()
        catalog = repo.load(catalog_id)

        if not confirm:
            typer.confirm(
                f"Katalog '{catalog.supplier_name}' ({catalog_id}) wirklich löschen?",
                abort=True,
            )

        repo.delete(catalog_id)
        console.print(f"[green]Katalog gelöscht:[/green] {catalog_id}")

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e

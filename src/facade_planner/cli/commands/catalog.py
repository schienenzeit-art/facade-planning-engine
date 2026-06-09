"""CLI commands for supplier catalog management (EPIC-005)."""
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


def _get_rule_catalog_repo():
    from facade_planner.infrastructure.persistence.rule_catalog_repository import (
        FileRuleCatalogRepository,
    )
    return FileRuleCatalogRepository(Path.cwd() / ".facadeplanner")


@app.command("import")
def import_catalog(
    name_or_path: str = typer.Argument(
        ...,
        help=(
            "Katalog-Name (z.B. 'swisspearl', 'alucobond-a2'), "
            "Pfad zu einer JSON-Datei oder CSV-Datei."
        ),
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", "-f", help="Bestehenden Katalog ueberschreiben."
    ),
    catalog_id: str = typer.Option(
        "", "--catalog-id", help="Katalog-ID (nur bei CSV-Import; Standard: Dateiname)."
    ),
    supplier_name: str = typer.Option(
        "", "--supplier-name", "-s", help="Lieferantenname (nur bei CSV-Import; Standard: Dateiname)."
    ),
    extract_rules: bool = typer.Option(
        False,
        "--extract-rules",
        help="Lieferantenregeln aus 'rules_raw' in den Projekt-RuleCatalog uebernehmen.",
    ),
) -> None:
    """Import a supplier catalog into the project.

    \b
    Bundled catalogs (no download required):
      swisspearl          Swisspearl 2026 Facade DE/AT (18 Formate)
      alucobond-a2        ALUCOBOND A2, A2-s1,d0 (11 Formate)
      alucobond-plus      ALUCOBOND PLUS, B1 (10 Formate)
      alucobond-standard  ALUCOBOND Standard, B2 (10 Formate)

    Or pass a path to a JSON or CSV file.

    \b
    CSV-Schema (Pflichtfelder: format_code, width_mm, height_mm):
      format_code,width_mm,height_mm,thickness_mm,weight_kg_m2,description,is_active
      MY-1250x3050-8,1250,3050,8,16.0,Beschreibung,true

    \b
    Regeln aus dem Katalog in den Projekt-RuleCatalog uebernehmen:
      facade catalog import swisspearl --extract-rules
    """
    try:
        project = ProjectService(Path.cwd()).require_initialized()
        svc = CatalogImportService()
        repo = _get_repo()

        # Resolve: bundled name, file path (JSON or CSV)
        if name_or_path in BUNDLED_CATALOGS:
            catalog = svc.import_bundled(name_or_path)
        else:
            file_path = Path(name_or_path)
            if file_path.suffix.lower() == ".csv":
                catalog = svc.import_from_csv(
                    file_path,
                    catalog_id=catalog_id,
                    supplier_name=supplier_name,
                )
            else:
                catalog = svc.import_from_file(file_path)

        if repo.exists(catalog.id) and not overwrite:
            console.print(
                f"[yellow]Katalog '{catalog.id}' bereits importiert.[/yellow] "
                "Verwende --overwrite zum Ueberschreiben."
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
        table.add_row("Regeln (rules_raw)", str(len(catalog.rules_raw)))
        table.add_row("Quelle", Path(catalog.source_path).name if catalog.source_path else "bundled")
        console.print(table)

        # Optionally extract supplier rules into project RuleCatalog
        if extract_rules:
            _do_extract_rules(catalog, project.id)

        if catalog.rules_raw and not extract_rules:
            console.print(
                f"[dim]Hinweis: Katalog enthaelt {len(catalog.rules_raw)} Lieferantenregel(n). "
                "Uebernehmen mit: facade catalog import ... --extract-rules[/dim]"
            )

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


def _do_extract_rules(catalog, project_id: str) -> None:
    """Extract catalog rules_raw into the project RuleCatalog."""
    from facade_planner.application.use_cases.import_catalog_rules import (
        ImportCatalogRulesUseCase,
    )

    rule_repo = _get_rule_catalog_repo()
    rule_catalog = rule_repo.load_or_create(project_id)
    uc = ImportCatalogRulesUseCase()
    added = uc.execute(catalog, rule_catalog)
    rule_repo.save(rule_catalog)

    if added:
        console.print(
            f"[green]{len(added)} Lieferantenregel(n) in RuleCatalog uebernommen:[/green]"
        )
        for rule in added:
            console.print(f"  + [cyan]{rule.id}[/cyan] — {rule.description[:60]}")
    else:
        console.print("[dim]Keine neuen Lieferantenregeln (bereits alle vorhanden).[/dim]")


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
        table.add_column("Regeln", width=7)
        table.add_column("Importiert")
        table.add_column("Quelle", style="dim")

        for cat in catalogs:
            table.add_row(
                cat.id,
                cat.supplier_name,
                str(len(cat.active_formats)),
                str(len(cat.rules_raw)),
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
    show_rules: bool = typer.Option(False, "--rules", help="Lieferantenregeln anzeigen"),
) -> None:
    """Show all formats (and optionally rules) in a catalog."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        catalog = _get_repo().load(catalog_id)
        formats = catalog.formats if inactive else catalog.active_formats

        if not formats:
            console.print("[yellow]Keine Formate gefunden.[/yellow]")
            return

        table = Table(
            title=f"{catalog.supplier_name} — {catalog_id} ({len(formats)} Formate)"
        )
        table.add_column("Format-Code", style="bold")
        table.add_column("Breite mm", justify="right")
        table.add_column("Hoehe mm", justify="right")
        table.add_column("Staerke mm", justify="right")
        table.add_column("kg/m2", justify="right")
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

        if show_rules:
            _print_rules_raw(catalog)
        elif catalog.rules_raw:
            console.print(
                f"[dim]{len(catalog.rules_raw)} Lieferantenregel(n) vorhanden — "
                "anzeigen mit: facade catalog show ... --rules[/dim]"
            )

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e


def _print_rules_raw(catalog) -> None:
    if not catalog.rules_raw:
        console.print("[dim]Keine Lieferantenregeln definiert.[/dim]")
        return
    rt = Table(title="Lieferantenregeln (rules_raw)")
    rt.add_column("ID", style="cyan")
    rt.add_column("Beschreibung")
    rt.add_column("Parameter", style="dim")
    for r in catalog.rules_raw:
        params = ", ".join(f"{k}={v}" for k, v in r.get("parameters", {}).items())
        rt.add_row(r.get("id", "?"), r.get("description", ""), params or "—")
    console.print(rt)


@app.command("available")
def list_available() -> None:
    """List bundled catalogs available for import (no download required)."""
    table = Table(title="Verfuegbare Bundled-Kataloge")
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
    confirm: bool = typer.Option(False, "--yes", "-y", help="Ohne Rueckfrage loeschen"),
) -> None:
    """Remove a catalog from the project."""
    try:
        ProjectService(Path.cwd()).require_initialized()
        repo = _get_repo()
        catalog = repo.load(catalog_id)

        if not confirm:
            typer.confirm(
                f"Katalog '{catalog.supplier_name}' ({catalog_id}) wirklich loeschen?",
                abort=True,
            )

        repo.delete(catalog_id)
        console.print(f"[green]Katalog geloescht:[/green] {catalog_id}")

    except FacadePlannerError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        raise typer.Exit(1) from e

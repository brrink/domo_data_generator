"""CLI interface for the Domo sample data generator."""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from datagen.config import CATALOG_DIR, DATA_DIR

app = typer.Typer(
    name="datagen",
    help="Generate and manage sample data for Domo.",
    no_args_is_help=True,
)
pool_app = typer.Typer(help="Manage the shared entity pool.")
app.add_typer(pool_app, name="pool")

console = Console()


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    setup_logging(verbose)


# --- generate ---


@app.command()
def generate(
    name: Optional[str] = typer.Argument(None, help="Dataset name (YAML filename stem)"),
    all_: bool = typer.Option(False, "--all", help="Generate all datasets"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed for reproducibility"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be generated without writing"),
) -> None:
    """Generate sample data for one or all datasets."""
    from datagen.uploader import generate_all, generate_and_save
    from datagen.entity_pool import load_pool
    from datagen.catalog_loader import load_all as load_all_catalogs

    cat_dir = catalog_dir or CATALOG_DIR
    d_dir = data_dir or DATA_DIR

    if not all_ and not name:
        console.print("[red]Specify a dataset name or use --all[/red]")
        raise typer.Exit(1)

    if all_:
        if dry_run:
            definitions = load_all_catalogs(cat_dir)
            for n, defn in definitions.items():
                console.print(f"  Would generate: {n} ({defn.dataset.row_count} rows)")
            return

        results = generate_all(catalog_dir=cat_dir, data_dir=d_dir, seed=seed)
        console.print(f"\n[green]Generated {len(results)} datasets:[/green]")
        for n, df in results.items():
            console.print(f"  {n}: {len(df)} rows")
    else:
        if dry_run:
            from datagen.catalog_loader import load_one
            defn = load_one(name, cat_dir)
            console.print(f"  Would generate: {name} ({defn.dataset.row_count} rows)")
            return

        df = generate_and_save(name, data_dir=d_dir, catalog_dir=cat_dir, seed=seed)
        console.print(f"[green]Generated {name}: {len(df)} rows[/green]")


# --- upload ---


@app.command()
def upload(
    name: Optional[str] = typer.Argument(None, help="Dataset name"),
    all_: bool = typer.Option(False, "--all", help="Upload all datasets"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir"),
) -> None:
    """Upload generated data to Domo (full replace)."""
    from datagen.uploader import upload_all, upload_dataset

    if not all_ and not name:
        console.print("[red]Specify a dataset name or use --all[/red]")
        raise typer.Exit(1)

    if all_:
        uploaded = upload_all(catalog_dir=catalog_dir, data_dir=data_dir)
        console.print(f"\n[green]Uploaded {len(uploaded)} datasets[/green]")
    else:
        upload_dataset(name, catalog_dir=catalog_dir, data_dir=data_dir)
        console.print(f"[green]Uploaded {name}[/green]")


# --- create-dataset ---


@app.command("create-dataset")
def create_dataset(
    name: Optional[str] = typer.Argument(None, help="Dataset name"),
    all_: bool = typer.Option(False, "--all", help="Create all datasets"),
    skip_existing: bool = typer.Option(False, "--skip-existing", help="Skip datasets that already have a domo_id"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
) -> None:
    """Create dataset(s) in Domo from catalog definitions."""
    from datagen.uploader import create_domo_dataset
    from datagen.catalog_loader import load_all as load_all_catalogs

    if not all_ and not name:
        console.print("[red]Specify a dataset name or use --all[/red]")
        raise typer.Exit(1)

    if all_:
        definitions = load_all_catalogs(catalog_dir)
        created = 0
        for n, defn in definitions.items():
            result = create_domo_dataset(n, definition=defn, catalog_dir=catalog_dir, skip_existing=skip_existing)
            if result:
                created += 1
                console.print(f"  Created: {n} -> {result}")
        console.print(f"\n[green]Created {created} datasets in Domo[/green]")
    else:
        dataset_id = create_domo_dataset(name, catalog_dir=catalog_dir, skip_existing=skip_existing)
        if dataset_id:
            console.print(f"[green]Created {name} -> {dataset_id}[/green]")
        else:
            console.print(f"[yellow]Skipped {name} (already exists)[/yellow]")


# --- roll-dates ---


@app.command("roll-dates")
def roll_dates(
    anchor_date: Optional[str] = typer.Option(
        None, "--anchor-date", help="Target date (YYYY-MM-DD). Defaults to today."
    ),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir"),
) -> None:
    """Shift all rolling date columns to stay current."""
    from datagen.date_roller import roll_all
    from datagen.catalog_loader import load_all as load_all_catalogs

    anchor = None
    if anchor_date:
        anchor = date.fromisoformat(anchor_date)

    definitions = load_all_catalogs(catalog_dir)
    rolled = roll_all(definitions, anchor_date=anchor, data_dir=data_dir)

    if rolled:
        console.print(f"[green]Rolled dates in {len(rolled)} datasets:[/green]")
        for name in rolled:
            console.print(f"  {name}")
    else:
        console.print("[yellow]No datasets needed date rolling[/yellow]")


# --- list ---


@app.command("list")
def list_datasets(
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show column details"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
) -> None:
    """List all dataset definitions in the catalog."""
    from datagen.catalog_loader import load_all as load_all_catalogs

    definitions = load_all_catalogs(catalog_dir)

    if not definitions:
        console.print("[yellow]No datasets found in catalog[/yellow]")
        return

    table = Table(title="Dataset Catalog")
    table.add_column("Name", style="cyan")
    table.add_column("Source Type", style="green")
    table.add_column("Rows", justify="right")
    table.add_column("Columns", justify="right")
    table.add_column("Domo ID", style="dim")

    for stem, defn in definitions.items():
        table.add_row(
            defn.dataset.name,
            defn.dataset.source_type,
            str(defn.dataset.row_count),
            str(len(defn.schema_)),
            defn.dataset.domo_id or "—",
        )

    console.print(table)

    if verbose:
        for stem, defn in definitions.items():
            console.print(f"\n[bold]{defn.dataset.name}[/bold] ({stem}.yaml)")
            col_table = Table(show_header=True)
            col_table.add_column("Column")
            col_table.add_column("Type")
            col_table.add_column("Generator")
            col_table.add_column("Rolling")
            for col in defn.schema_:
                col_table.add_row(
                    col.name,
                    col.type,
                    col.generator,
                    "yes" if col.rolling else "",
                )
            console.print(col_table)


# --- pool ---


@pool_app.command("regenerate")
def pool_regenerate(
    seed: int = typer.Option(42, "--seed", help="Random seed"),
    company_count: Optional[int] = typer.Option(None, "--company-count"),
    person_count: Optional[int] = typer.Option(None, "--person-count"),
    product_count: Optional[int] = typer.Option(None, "--product-count"),
    sales_rep_count: Optional[int] = typer.Option(None, "--sales-rep-count"),
    campaign_count: Optional[int] = typer.Option(None, "--campaign-count"),
) -> None:
    """Regenerate the shared entity pool."""
    from datagen.entity_pool import generate_pool, save_pool

    sizes = {}
    if company_count is not None:
        sizes["company"] = company_count
    if person_count is not None:
        sizes["person"] = person_count
    if product_count is not None:
        sizes["product"] = product_count
    if sales_rep_count is not None:
        sizes["sales_rep"] = sales_rep_count
    if campaign_count is not None:
        sizes["campaign"] = campaign_count

    pool = generate_pool(seed=seed, pool_sizes=sizes)
    save_pool(pool)

    console.print("[green]Entity pool regenerated:[/green]")
    for entity_type, entities in pool.entities.items():
        console.print(f"  {entity_type}: {len(entities)} entities")


@pool_app.command("show")
def pool_show() -> None:
    """Show entity pool summary."""
    from datagen.entity_pool import load_pool

    try:
        pool = load_pool()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    console.print(f"Generated at: {pool.generated_at}")
    console.print(f"Seed: {pool.seed}")
    console.print()
    for entity_type, entities in pool.entities.items():
        console.print(f"  {entity_type}: {len(entities)} entities")
        if entities:
            sample = entities[0]
            console.print(f"    Sample: {sample}")


# --- status ---


@app.command()
def status(
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir"),
) -> None:
    """Show generation status for all datasets."""
    from datagen.catalog_loader import load_all as load_all_catalogs
    from datagen.date_roller import load_metadata
    import os

    d_dir = data_dir or DATA_DIR
    definitions = load_all_catalogs(catalog_dir)
    meta = load_metadata()

    console.print(f"Generated at: {meta.get('generated_at', 'never')}")
    console.print()

    table = Table(title="Dataset Status")
    table.add_column("Dataset", style="cyan")
    table.add_column("CSV Exists")
    table.add_column("CSV Rows", justify="right")
    table.add_column("Expected Rows", justify="right")
    table.add_column("Domo ID", style="dim")

    for stem, defn in definitions.items():
        csv_path = d_dir / f"{stem}.csv"
        exists = csv_path.exists()
        csv_rows = "—"
        if exists:
            # Count lines minus header
            with open(csv_path) as f:
                csv_rows = str(sum(1 for _ in f) - 1)

        table.add_row(
            defn.dataset.name,
            "[green]yes[/green]" if exists else "[red]no[/red]",
            csv_rows,
            str(defn.dataset.row_count),
            defn.dataset.domo_id or "—",
        )

    console.print(table)


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()

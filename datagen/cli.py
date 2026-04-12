"""CLI interface for the Domo sample data generator."""

from __future__ import annotations

import logging
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from datagen.config import CATALOG_DIR, DATA_DIR, get_bundled_catalog_dir
from datagen.output import emit
from datagen.state import AppState

app = typer.Typer(
    name="datagen",
    help="Generate and manage sample data for Domo.",
    no_args_is_help=True,
)
pool_app = typer.Typer(help="Manage the shared entity pool.")
app.add_typer(pool_app, name="pool")

console = Console(stderr=True)


def _get_state(ctx: typer.Context) -> AppState:
    return ctx.obj or AppState()


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    output: str = typer.Option("json", "--output", "-o", help="Output format: json, table, yaml"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
) -> None:
    """Generate and manage sample data for Domo."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    ctx.obj = AppState(output_format=output, yes=yes)


# --- init ---


@app.command()
def init(
    target: Optional[Path] = typer.Argument(None, help="Target directory (defaults to CWD)"),
) -> None:
    """Initialize a working directory with catalog files and .env template."""
    import importlib.resources

    dest = target or Path.cwd()
    dest = dest.resolve()

    # Copy catalog YAML files
    catalog_dest = dest / "catalog"
    if catalog_dest.exists():
        console.print(f"[yellow]catalog/ already exists at {catalog_dest}, skipping[/yellow]")
    else:
        bundled = get_bundled_catalog_dir()
        shutil.copytree(bundled, catalog_dest)
        console.print(f"[green]Copied catalog definitions to {catalog_dest}[/green]")

    # Copy .env.example
    env_dest = dest / ".env"
    if env_dest.exists():
        console.print(f"[yellow].env already exists at {env_dest}, skipping[/yellow]")
    else:
        env_example = importlib.resources.files("datagen") / ".env.example"
        shutil.copy2(str(env_example), env_dest)
        console.print(f"[green]Copied .env template to {env_dest}[/green]")

    # Create data directory
    data_dest = dest / "data"
    data_dest.mkdir(exist_ok=True)
    console.print(f"[green]Data directory ready at {data_dest}[/green]")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Edit .env with your Domo credentials")
    console.print("  2. datagen pool regenerate")
    console.print("  3. datagen generate --all")
    console.print("  4. datagen create-dataset --all --skip-existing")
    console.print("  5. datagen upload --all")


# --- generate ---


@app.command()
def generate(
    ctx: typer.Context,
    name: Optional[str] = typer.Argument(None, help="Dataset name (YAML filename stem)"),
    all_: bool = typer.Option(False, "--all", help="Generate all datasets"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed for reproducibility"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be generated without writing"),
) -> None:
    """Generate sample data for one or all datasets."""
    from datagen.uploader import generate_all, generate_and_save
    from datagen.catalog_loader import load_all as load_all_catalogs

    state = _get_state(ctx)
    cat_dir = catalog_dir or CATALOG_DIR
    d_dir = data_dir or DATA_DIR

    if not all_ and not name:
        console.print("[red]Specify a dataset name or use --all[/red]")
        raise typer.Exit(1)

    if all_:
        if dry_run:
            definitions = load_all_catalogs(cat_dir)
            result = [
                {"name": n, "row_count": defn.dataset.row_count, "dry_run": True}
                for n, defn in definitions.items()
            ]
            emit(result, state.output_format)
            return

        results = generate_all(catalog_dir=cat_dir, data_dir=d_dir, seed=seed)
        result = [
            {"name": n, "rows": len(df)} for n, df in results.items()
        ]
        emit({"generated": len(results), "datasets": result}, state.output_format)
    else:
        if dry_run:
            from datagen.catalog_loader import load_one
            defn = load_one(name, cat_dir)
            emit({"name": name, "row_count": defn.dataset.row_count, "dry_run": True}, state.output_format)
            return

        df = generate_and_save(name, data_dir=d_dir, catalog_dir=cat_dir, seed=seed)
        emit({"name": name, "rows": len(df)}, state.output_format)


# --- upload ---


@app.command()
def upload(
    ctx: typer.Context,
    name: Optional[str] = typer.Argument(None, help="Dataset name"),
    all_: bool = typer.Option(False, "--all", help="Upload all datasets"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir"),
) -> None:
    """Upload generated data to Domo (full replace)."""
    from datagen.uploader import upload_all, upload_dataset

    state = _get_state(ctx)

    if not all_ and not name:
        console.print("[red]Specify a dataset name or use --all[/red]")
        raise typer.Exit(1)

    if all_:
        uploaded = upload_all(catalog_dir=catalog_dir, data_dir=data_dir)
        emit({"uploaded": len(uploaded), "datasets": uploaded}, state.output_format)
    else:
        upload_dataset(name, catalog_dir=catalog_dir, data_dir=data_dir)
        emit({"uploaded": name}, state.output_format)


# --- create-dataset ---


@app.command("create-dataset")
def create_dataset(
    ctx: typer.Context,
    name: Optional[str] = typer.Argument(None, help="Dataset name"),
    all_: bool = typer.Option(False, "--all", help="Create all datasets"),
    skip_existing: bool = typer.Option(False, "--skip-existing", help="Skip datasets that already have a domo_id"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
) -> None:
    """Create dataset(s) in Domo from catalog definitions."""
    from datagen.uploader import create_domo_dataset
    from datagen.catalog_loader import load_all as load_all_catalogs

    state = _get_state(ctx)

    if not all_ and not name:
        console.print("[red]Specify a dataset name or use --all[/red]")
        raise typer.Exit(1)

    if all_:
        definitions = load_all_catalogs(catalog_dir)
        created = []
        for n, defn in definitions.items():
            result = create_domo_dataset(n, definition=defn, catalog_dir=catalog_dir, skip_existing=skip_existing)
            if result:
                created.append({"name": n, "domo_id": result})
        emit({"created": len(created), "datasets": created}, state.output_format)
    else:
        dataset_id = create_domo_dataset(name, catalog_dir=catalog_dir, skip_existing=skip_existing)
        if dataset_id:
            emit({"name": name, "domo_id": dataset_id}, state.output_format)
        else:
            emit({"name": name, "skipped": True}, state.output_format)


# --- roll-dates ---


@app.command("roll-dates")
def roll_dates(
    ctx: typer.Context,
    anchor_date: Optional[str] = typer.Option(
        None, "--anchor-date", help="Target date (YYYY-MM-DD). Defaults to today."
    ),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir"),
) -> None:
    """Shift all rolling date columns to stay current."""
    from datagen.date_roller import roll_all
    from datagen.catalog_loader import load_all as load_all_catalogs

    state = _get_state(ctx)
    anchor = None
    if anchor_date:
        anchor = date.fromisoformat(anchor_date)

    definitions = load_all_catalogs(catalog_dir)
    rolled = roll_all(definitions, anchor_date=anchor, data_dir=data_dir)
    emit({"rolled": len(rolled), "datasets": rolled}, state.output_format)


# --- list ---


@app.command("list")
def list_datasets(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show column details"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
) -> None:
    """List all dataset definitions in the catalog."""
    from datagen.catalog_loader import load_all as load_all_catalogs

    state = _get_state(ctx)
    definitions = load_all_catalogs(catalog_dir)

    if not definitions:
        emit([], state.output_format)
        return

    datasets = []
    for stem, defn in definitions.items():
        entry: dict = {
            "key": stem,
            "name": defn.dataset.name,
            "source_type": defn.dataset.source_type,
            "row_count": defn.dataset.row_count,
            "columns": len(defn.schema_),
            "domo_id": defn.dataset.domo_id or None,
        }
        if verbose:
            entry["schema"] = [
                {
                    "name": col.name,
                    "type": col.type,
                    "generator": col.generator,
                    "rolling": col.rolling,
                }
                for col in defn.schema_
            ]
        datasets.append(entry)

    emit(datasets, state.output_format)


# --- pool ---


@pool_app.command("regenerate")
def pool_regenerate(
    ctx: typer.Context,
    seed: int = typer.Option(42, "--seed", help="Random seed"),
    company_count: Optional[int] = typer.Option(None, "--company-count"),
    person_count: Optional[int] = typer.Option(None, "--person-count"),
    product_count: Optional[int] = typer.Option(None, "--product-count"),
    sales_rep_count: Optional[int] = typer.Option(None, "--sales-rep-count"),
    campaign_count: Optional[int] = typer.Option(None, "--campaign-count"),
) -> None:
    """Regenerate the shared entity pool."""
    from datagen.entity_pool import generate_pool, save_pool

    state = _get_state(ctx)
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

    result = {
        "seed": seed,
        "entities": {k: len(v) for k, v in pool.entities.items()},
    }
    emit(result, state.output_format)


@pool_app.command("show")
def pool_show(ctx: typer.Context) -> None:
    """Show entity pool summary."""
    from datagen.entity_pool import load_pool

    state = _get_state(ctx)
    try:
        pool = load_pool()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    result = {
        "generated_at": pool.generated_at,
        "seed": pool.seed,
        "entities": {k: len(v) for k, v in pool.entities.items()},
    }
    emit(result, state.output_format)


# --- status ---


@app.command()
def status(
    ctx: typer.Context,
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir"),
) -> None:
    """Show generation status for all datasets."""
    from datagen.catalog_loader import load_all as load_all_catalogs
    from datagen.date_roller import load_metadata

    state = _get_state(ctx)
    d_dir = data_dir or DATA_DIR
    definitions = load_all_catalogs(catalog_dir)
    meta = load_metadata()

    datasets = []
    for stem, defn in definitions.items():
        csv_path = d_dir / f"{stem}.csv"
        exists = csv_path.exists()
        csv_rows = None
        if exists:
            with open(csv_path) as f:
                csv_rows = sum(1 for _ in f) - 1

        datasets.append({
            "key": stem,
            "name": defn.dataset.name,
            "csv_exists": exists,
            "csv_rows": csv_rows,
            "expected_rows": defn.dataset.row_count,
            "domo_id": defn.dataset.domo_id or None,
        })

    result = {
        "generated_at": meta.get("generated_at"),
        "datasets": datasets,
    }
    emit(result, state.output_format)


# --- discover-types ---


@app.command("discover-types")
def discover_types(
    ctx: typer.Context,
    search: Optional[str] = typer.Argument(None, help="Search term to filter providers (e.g. 'salesforce', 'google')"),
) -> None:
    """Search Domo's available connector/provider types to find the correct key for icon mapping."""
    from datagen.domo_client import DomoClient, SOURCE_TYPE_MAP

    state = _get_state(ctx)
    client = DomoClient()
    try:
        providers = client.list_providers(search=search)
    except Exception as e:
        console.print(f"[red]Error fetching providers: {e}[/red]")
        raise typer.Exit(1)

    mapped_keys = set(SOURCE_TYPE_MAP.values())
    result = [
        {"key": p["key"], "name": p["name"], "mapped": p["key"] in mapped_keys}
        for p in providers
    ]
    emit(result, state.output_format)


# --- set-type ---


@app.command("set-type")
def set_type(
    ctx: typer.Context,
    name: str = typer.Argument(help="Dataset name (YAML filename stem)"),
    provider_key: Optional[str] = typer.Option(None, "--provider-key", help="Override the provider key instead of using SOURCE_TYPE_MAP"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
) -> None:
    """Set the connector type/icon on an existing Domo dataset."""
    from datagen.catalog_loader import load_one
    from datagen.domo_client import DomoClient, SOURCE_TYPE_MAP

    state = _get_state(ctx)
    defn = load_one(name, catalog_dir)
    if not defn.dataset.domo_id:
        console.print(f"[red]Dataset '{name}' has no domo_id. Run 'datagen create-dataset {name}' first.[/red]")
        raise typer.Exit(1)

    key = provider_key or SOURCE_TYPE_MAP.get(defn.dataset.source_type)
    if not key:
        console.print(
            f"[red]No provider key for source_type '{defn.dataset.source_type}'. "
            f"Use --provider-key or run 'datagen discover-types {defn.dataset.source_type}' to find it.[/red]"
        )
        raise typer.Exit(1)

    client = DomoClient()
    success = client.set_dataset_type(
        defn.dataset.domo_id, defn.dataset.source_type, provider_key_override=provider_key
    )
    emit({"name": name, "domo_id": defn.dataset.domo_id, "provider_key": key, "success": success}, state.output_format)


@app.command("set-type-all")
def set_type_all(
    ctx: typer.Context,
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
) -> None:
    """Set the connector type/icon on all Domo datasets that have a domo_id."""
    from datagen.catalog_loader import load_all as load_all_catalogs
    from datagen.domo_client import DomoClient, SOURCE_TYPE_MAP

    state = _get_state(ctx)
    definitions = load_all_catalogs(catalog_dir)
    client = DomoClient()
    results = []

    for stem, defn in definitions.items():
        if not defn.dataset.domo_id:
            results.append({"name": stem, "status": "skipped", "reason": "no domo_id"})
            continue

        key = SOURCE_TYPE_MAP.get(defn.dataset.source_type)
        if not key:
            results.append({"name": stem, "status": "skipped", "reason": f"no mapping for '{defn.dataset.source_type}'"})
            continue

        success = client.set_dataset_type(defn.dataset.domo_id, defn.dataset.source_type)
        results.append({"name": stem, "provider_key": key, "status": "success" if success else "failed"})

    emit(results, state.output_format)


# --- Entry points ---


def run() -> None:
    """Entry point with error handling."""
    try:
        app()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def cli() -> None:
    """Legacy entry point."""
    run()


if __name__ == "__main__":
    run()

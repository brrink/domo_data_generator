"""Orchestrate data generation and upload to Domo."""

from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from datagen.catalog_loader import load_all, load_one, save_domo_id
from datagen.config import DATA_DIR
from datagen.date_roller import save_metadata, load_metadata
from datagen.domo_client import DomoClient
from datagen.entity_pool import load_pool
from datagen.generators.base import generate_column
from datagen.models import DatasetDefinition, EntityPool

# Import source-specific generators to register them
import datagen.generators.salesforce  # noqa: F401
import datagen.generators.google_analytics  # noqa: F401
import datagen.generators.financial  # noqa: F401
import datagen.generators.marketing  # noqa: F401
import datagen.generators.health  # noqa: F401

logger = logging.getLogger(__name__)


def generate_dataset(
    definition: DatasetDefinition,
    pool: EntityPool,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate a DataFrame from a dataset definition and entity pool."""
    if seed is not None:
        random.seed(seed)

    row_count = definition.dataset.row_count
    context: dict[str, list] = {}
    data: dict[str, list] = {}

    for col in definition.schema_:
        values = generate_column(col, row_count, pool=pool, context=context)
        data[col.name] = values
        context[col.name] = values

    return pd.DataFrame(data)


def generate_and_save(
    name: str,
    definition: DatasetDefinition | None = None,
    pool: EntityPool | None = None,
    data_dir: Path | None = None,
    catalog_dir: Path | None = None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate a dataset and save it as CSV."""
    data_dir = data_dir or DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    if definition is None:
        definition = load_one(name, catalog_dir)
    if pool is None:
        pool = load_pool()

    df = generate_dataset(definition, pool, seed=seed)

    csv_path = data_dir / f"{name}.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Generated {len(df)} rows -> {csv_path}")

    return df


def generate_all(
    catalog_dir: Path | None = None,
    data_dir: Path | None = None,
    seed: int | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate all datasets defined in the catalog."""
    definitions = load_all(catalog_dir)
    pool = load_pool()
    results = {}

    for name, defn in definitions.items():
        df = generate_and_save(name, defn, pool, data_dir=data_dir, seed=seed)
        results[name] = df

    # Save generation metadata
    meta = load_metadata()
    meta["generated_at"] = datetime.now(timezone.utc).isoformat()
    meta["datasets"] = {name: len(df) for name, df in results.items()}
    save_metadata(meta)

    return results


def upload_dataset(
    name: str,
    client: DomoClient | None = None,
    definition: DatasetDefinition | None = None,
    data_dir: Path | None = None,
    catalog_dir: Path | None = None,
) -> None:
    """Upload a single dataset to Domo (full replace)."""
    data_dir = data_dir or DATA_DIR
    client = client or DomoClient()

    if definition is None:
        definition = load_one(name, catalog_dir)

    dataset_id = definition.dataset.domo_id
    if not dataset_id:
        raise ValueError(
            f"Dataset '{name}' has no domo_id. Run 'datagen create-dataset {name}' first."
        )

    csv_path = data_dir / f"{name}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"No generated data for '{name}'. Run 'datagen generate {name}' first."
        )

    df = pd.read_csv(csv_path)
    client.replace_data(dataset_id, df)
    logger.info(f"Uploaded {len(df)} rows to dataset {dataset_id} ({name})")


def upload_all(
    client: DomoClient | None = None,
    catalog_dir: Path | None = None,
    data_dir: Path | None = None,
) -> list[str]:
    """Upload all datasets to Domo. Returns list of uploaded dataset names."""
    client = client or DomoClient()
    definitions = load_all(catalog_dir)
    uploaded = []

    for name, defn in definitions.items():
        if not defn.dataset.domo_id:
            logger.warning(f"Skipping '{name}' - no domo_id set")
            continue
        try:
            upload_dataset(name, client=client, definition=defn, data_dir=data_dir)
            uploaded.append(name)
        except Exception as e:
            logger.error(f"Failed to upload '{name}': {e}")

    return uploaded


def create_domo_dataset(
    name: str,
    client: DomoClient | None = None,
    definition: DatasetDefinition | None = None,
    catalog_dir: Path | None = None,
    skip_existing: bool = False,
) -> str | None:
    """Create a dataset in Domo and write the ID back to the YAML catalog.

    Returns the dataset ID, or None if skipped.
    """
    client = client or DomoClient()

    if definition is None:
        definition = load_one(name, catalog_dir)

    if skip_existing and definition.dataset.domo_id:
        logger.info(f"Skipping '{name}' - already has domo_id: {definition.dataset.domo_id}")
        return None

    dataset_id = client.create_dataset(definition)
    save_domo_id(name, dataset_id, catalog_dir)
    logger.info(f"Created Domo dataset for '{name}': {dataset_id}")
    return dataset_id

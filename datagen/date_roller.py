"""Date rolling: shift date columns to keep data looking current."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from datagen.config import DATA_DIR, METADATA_PATH
from datagen.models import DatasetDefinition


def load_metadata(path: Path | None = None) -> dict:
    """Load generation metadata (tracks generated_at date)."""
    path = path or METADATA_PATH
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_metadata(meta: dict, path: Path | None = None) -> None:
    """Save generation metadata."""
    path = path or METADATA_PATH
    with open(path, "w") as f:
        json.dump(meta, f, indent=2)


def get_rolling_columns(definition: DatasetDefinition) -> list[str]:
    """Get the names of columns marked as rolling in a dataset definition."""
    return [col.name for col in definition.schema_ if col.rolling]


def roll_dates_in_df(
    df: pd.DataFrame,
    rolling_columns: list[str],
    delta: timedelta,
) -> pd.DataFrame:
    """Shift all rolling date columns by the given timedelta."""
    df = df.copy()
    for col_name in rolling_columns:
        if col_name not in df.columns:
            continue
        col = df[col_name]
        # Try to parse as datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(col):
            col = pd.to_datetime(col, errors="coerce")
        df[col_name] = col + delta
    return df


def roll_dataset(
    name: str,
    definition: DatasetDefinition,
    anchor_date: date | None = None,
    data_dir: Path | None = None,
    metadata_path: Path | None = None,
) -> pd.DataFrame | None:
    """Roll dates in a single dataset's CSV file.

    Returns the updated DataFrame, or None if no rolling needed.
    """
    data_dir = data_dir or DATA_DIR
    csv_path = data_dir / f"{name}.csv"
    if not csv_path.exists():
        return None

    rolling_cols = get_rolling_columns(definition)
    if not rolling_cols:
        return None

    anchor = anchor_date or date.today()

    meta = load_metadata(metadata_path)
    generated_at_str = meta.get("generated_at")
    if not generated_at_str:
        return None

    generated_at = datetime.fromisoformat(generated_at_str).date()
    delta = timedelta(days=(anchor - generated_at).days)
    if delta.days == 0:
        return None

    df = pd.read_csv(csv_path)
    df = roll_dates_in_df(df, rolling_cols, delta)
    df.to_csv(csv_path, index=False)
    return df


def roll_all(
    definitions: dict[str, DatasetDefinition],
    anchor_date: date | None = None,
    data_dir: Path | None = None,
    metadata_path: Path | None = None,
) -> list[str]:
    """Roll dates in all datasets. Returns list of dataset names that were rolled."""
    anchor = anchor_date or date.today()
    rolled = []
    for name, defn in definitions.items():
        result = roll_dataset(name, defn, anchor_date=anchor, data_dir=data_dir, metadata_path=metadata_path)
        if result is not None:
            rolled.append(name)

    # Update generated_at to the anchor date
    meta = load_metadata(metadata_path)
    meta["generated_at"] = datetime(anchor.year, anchor.month, anchor.day).isoformat()
    save_metadata(meta, metadata_path)

    return rolled

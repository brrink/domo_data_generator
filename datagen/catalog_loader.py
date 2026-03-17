"""Load and validate dataset definitions from the YAML catalog."""

from __future__ import annotations

from pathlib import Path

import yaml

from datagen.config import CATALOG_DIR
from datagen.models import DatasetDefinition


def load_definition(path: Path) -> DatasetDefinition:
    """Load a single dataset definition from a YAML file."""
    with open(path) as f:
        raw = yaml.safe_load(f)
    return DatasetDefinition.model_validate(raw)


def load_all(catalog_dir: Path | None = None) -> dict[str, DatasetDefinition]:
    """Load all dataset definitions from the catalog directory.

    Returns a dict keyed by the YAML filename stem (e.g. 'salesforce_opportunities').
    """
    catalog_dir = catalog_dir or CATALOG_DIR
    definitions: dict[str, DatasetDefinition] = {}
    for path in sorted(catalog_dir.glob("*.yaml")):
        defn = load_definition(path)
        definitions[path.stem] = defn
    return definitions


def load_one(name: str, catalog_dir: Path | None = None) -> DatasetDefinition:
    """Load a single dataset definition by name (filename stem)."""
    catalog_dir = catalog_dir or CATALOG_DIR
    path = catalog_dir / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Catalog definition not found: {path}")
    return load_definition(path)


def save_domo_id(name: str, domo_id: str, catalog_dir: Path | None = None) -> None:
    """Write the Domo dataset ID back into a catalog YAML file."""
    catalog_dir = catalog_dir or CATALOG_DIR
    path = catalog_dir / f"{name}.yaml"
    with open(path) as f:
        raw = yaml.safe_load(f)
    raw["dataset"]["domo_id"] = domo_id
    with open(path, "w") as f:
        yaml.dump(raw, f, default_flow_style=False, sort_keys=False)

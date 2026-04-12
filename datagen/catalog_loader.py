"""Load and validate dataset definitions from the YAML catalog."""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

from datagen.config import CATALOG_DIR, DATA_DIR, get_bundled_catalog_dir
from datagen.models import DatasetDefinition


def _domo_ids_path() -> Path:
    """Path to the state file that stores domo_id mappings."""
    return DATA_DIR / "domo_ids.json"


def _load_domo_ids() -> dict[str, str]:
    """Load domo_id overrides from the state file."""
    path = _domo_ids_path()
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _save_domo_ids(ids: dict[str, str]) -> None:
    """Save domo_id overrides to the state file."""
    path = _domo_ids_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(ids, f, indent=2)


def _is_writable(catalog_dir: Path) -> bool:
    """Check if the catalog directory is writable (local, not bundled)."""
    bundled = get_bundled_catalog_dir()
    try:
        return catalog_dir.resolve() != bundled.resolve() and os.access(catalog_dir, os.W_OK)
    except (OSError, ValueError):
        return False


def load_definition(path: Path) -> DatasetDefinition:
    """Load a single dataset definition from a YAML file."""
    with open(path) as f:
        raw = yaml.safe_load(f)
    return DatasetDefinition.model_validate(raw)


def load_all(catalog_dir: Path | None = None) -> dict[str, DatasetDefinition]:
    """Load all dataset definitions from the catalog directory.

    Returns a dict keyed by the YAML filename stem (e.g. 'salesforce_opportunities').
    Merges domo_id overrides from the state file when using bundled catalog.
    """
    catalog_dir = catalog_dir or CATALOG_DIR
    definitions: dict[str, DatasetDefinition] = {}
    for path in sorted(catalog_dir.glob("*.yaml")):
        defn = load_definition(path)
        definitions[path.stem] = defn

    # Merge domo_id overrides from state file
    domo_ids = _load_domo_ids()
    for stem, domo_id in domo_ids.items():
        if stem in definitions and not definitions[stem].dataset.domo_id:
            definitions[stem].dataset.domo_id = domo_id

    return definitions


def load_one(name: str, catalog_dir: Path | None = None) -> DatasetDefinition:
    """Load a single dataset definition by name (filename stem)."""
    catalog_dir = catalog_dir or CATALOG_DIR
    path = catalog_dir / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Catalog definition not found: {path}")
    defn = load_definition(path)

    # Merge domo_id from state file if not set in YAML
    if not defn.dataset.domo_id:
        domo_ids = _load_domo_ids()
        if name in domo_ids:
            defn.dataset.domo_id = domo_ids[name]

    return defn


def save_domo_id(name: str, domo_id: str, catalog_dir: Path | None = None) -> None:
    """Persist a Domo dataset ID for a catalog entry.

    If the catalog is a local writable directory, writes directly to the YAML.
    Otherwise, stores in the domo_ids.json state file.
    """
    catalog_dir = catalog_dir or CATALOG_DIR

    if _is_writable(catalog_dir):
        # Local mutable catalog — write directly to YAML (original behavior)
        path = catalog_dir / f"{name}.yaml"
        with open(path) as f:
            raw = yaml.safe_load(f)
        raw["dataset"]["domo_id"] = domo_id
        with open(path, "w") as f:
            yaml.dump(raw, f, default_flow_style=False, sort_keys=False)
    else:
        # Bundled or read-only catalog — use state file
        domo_ids = _load_domo_ids()
        domo_ids[name] = domo_id
        _save_domo_ids(domo_ids)

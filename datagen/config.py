"""Configuration and environment loading."""

from __future__ import annotations

import importlib.resources
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Load .env from CWD upward — usecwd=True is required so find_dotenv
# searches from the actual working directory, not from this module's
# location (which is inside a pipx venv when installed).
load_dotenv(find_dotenv(usecwd=True))

# Domo credentials
DOMO_INSTANCE = os.getenv("DOMO_INSTANCE", "")
DOMO_DEVELOPER_TOKEN = os.getenv("DOMO_DEVELOPER_TOKEN", "")
# OAuth client credentials (optional, needed only for data upload)
DOMO_CLIENT_ID = os.getenv("DOMO_CLIENT_ID", "")
DOMO_CLIENT_SECRET = os.getenv("DOMO_CLIENT_SECRET", "")


def get_bundled_catalog_dir() -> Path:
    """Return the path to the catalog directory bundled inside the package."""
    ref = importlib.resources.files("datagen") / "catalog"
    return Path(str(ref))


def get_default_catalog_dir() -> Path:
    """Return the default catalog directory.

    Prefers a local ./catalog/ in CWD (mutable, for users who ran `datagen init`
    or cloned the repo). Falls back to the bundled read-only catalog.
    """
    local = Path.cwd() / "catalog"
    if local.is_dir():
        return local
    return get_bundled_catalog_dir()


# Default directories — can be overridden via CLI options or env vars
CATALOG_DIR = get_default_catalog_dir()
DATA_DIR = Path(os.getenv("DATAGEN_DATA_DIR", str(Path.cwd() / "data")))

ENTITY_POOL_PATH = DATA_DIR / "entity_pool.json"
METADATA_PATH = DATA_DIR / "metadata.json"

"""Configuration and environment loading."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root is the parent of the datagen package
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

# Domo credentials
DOMO_CLIENT_ID = os.getenv("DOMO_CLIENT_ID", "")
DOMO_CLIENT_SECRET = os.getenv("DOMO_CLIENT_SECRET", "")
DOMO_API_HOST = os.getenv("DOMO_API_HOST", "api.domo.com")
DOMO_INSTANCE = os.getenv("DOMO_INSTANCE", "")
DOMO_SET_CONNECTOR_TYPE = os.getenv("DOMO_SET_CONNECTOR_TYPE", "false").lower() == "true"
DOMO_DEVELOPER_TOKEN = os.getenv("DOMO_DEVELOPER_TOKEN", "")

# Directories
CATALOG_DIR = PROJECT_ROOT / "catalog"
DATA_DIR = PROJECT_ROOT / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

ENTITY_POOL_PATH = DATA_DIR / "entity_pool.json"
METADATA_PATH = DATA_DIR / "metadata.json"

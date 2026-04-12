"""Application state threaded through CLI commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppState:
    """Holds shared state for all CLI commands."""

    output_format: str = "json"
    dry_run: bool = False
    yes: bool = False
    catalog_dir: Path | None = None
    data_dir: Path | None = None

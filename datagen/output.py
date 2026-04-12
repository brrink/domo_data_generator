"""Structured output formatting for CLI commands."""

from __future__ import annotations

import json
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table

console = Console()


def emit(data: Any, output_format: str = "json") -> None:
    """Emit structured data in the requested format.

    Args:
        data: The data to emit. Should be JSON-serializable (dicts, lists, primitives).
        output_format: One of "json", "table", "yaml".
    """
    if output_format == "json":
        console.print_json(json.dumps(data, default=str))
    elif output_format == "yaml":
        console.print(yaml.safe_dump(data, default_flow_style=False, sort_keys=False), end="")
    elif output_format == "table":
        _render_table(data)
    else:
        console.print_json(json.dumps(data, default=str))


def _render_table(data: Any) -> None:
    """Render data as a Rich table."""
    if isinstance(data, list) and data and isinstance(data[0], dict):
        table = Table()
        keys = list(data[0].keys())
        for key in keys:
            table.add_column(key)
        for row in data:
            table.add_row(*[str(row.get(k, "")) for k in keys])
        console.print(table)
    elif isinstance(data, dict):
        table = Table(show_header=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        for key, value in data.items():
            table.add_row(str(key), str(value))
        console.print(table)
    else:
        console.print(data)

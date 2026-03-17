"""Pydantic models for dataset catalog definitions and entity pool."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ColumnDef(BaseModel):
    """Definition of a single column in a dataset."""

    name: str
    type: str = Field(description="Domo column type: STRING, DECIMAL, LONG, DOUBLE, DATE, DATETIME")
    generator: str = Field(description="Generator key, e.g. uuid4, random_choice, entity_ref")
    # Generator-specific parameters (passed through to the generator)
    entity: Optional[str] = None
    field: Optional[str] = None
    choices: Optional[Any] = None  # list or dict (weighted)
    min: Optional[float] = None
    max: Optional[float] = None
    precision: Optional[int] = None
    template: Optional[str] = None
    refs: Optional[list[str]] = None
    start_days_ago: Optional[int] = None
    end_days_ahead: Optional[int] = None
    rolling: bool = False
    mapping: Optional[dict[str, Any]] = None
    source_column: Optional[str] = None
    format: Optional[str] = None
    faker_method: Optional[str] = None
    faker_args: Optional[dict[str, Any]] = None

    class Config:
        extra = "allow"


class DatasetMeta(BaseModel):
    """Metadata section of a dataset definition."""

    name: str
    domo_id: Optional[str] = None
    source_type: str
    description: str = ""
    row_count: int = 1000
    tags: list[str] = Field(default_factory=list)


class DatasetDefinition(BaseModel):
    """Full dataset definition loaded from a YAML catalog file."""

    dataset: DatasetMeta
    schema_: list[ColumnDef] = Field(alias="schema")

    class Config:
        populate_by_name = True


class EntityRecord(BaseModel):
    """A single entity in the shared pool (flexible key-value)."""

    id: str
    data: dict[str, Any] = Field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        if key == "id":
            return self.id
        return self.data[key]

    def get(self, key: str, default: Any = None) -> Any:
        if key == "id":
            return self.id
        return self.data.get(key, default)


class EntityPool(BaseModel):
    """The shared entity pool persisted to disk."""

    generated_at: str
    seed: int = 42
    entities: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    pool_sizes: dict[str, int] = Field(default_factory=dict)

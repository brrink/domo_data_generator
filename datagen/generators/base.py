"""Generator registry and base generation logic."""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Callable

from faker import Faker

from datagen.models import ColumnDef, EntityPool

# Global generator registry
_GENERATORS: dict[str, Callable] = {}

fake = Faker()


def register_generator(name: str):
    """Decorator to register a generator function by name."""
    def decorator(fn: Callable):
        _GENERATORS[name] = fn
        return fn
    return decorator


def get_generator(name: str) -> Callable:
    """Look up a registered generator by name."""
    if name not in _GENERATORS:
        raise ValueError(
            f"Unknown generator '{name}'. Available: {sorted(_GENERATORS.keys())}"
        )
    return _GENERATORS[name]


def generate_column(
    col: ColumnDef,
    row_count: int,
    pool: EntityPool | None = None,
    context: dict[str, list] | None = None,
) -> list:
    """Generate values for a single column."""
    gen = get_generator(col.generator)
    return gen(col, row_count, pool=pool, context=context)


# --- Built-in generators ---


@register_generator("uuid4")
def gen_uuid4(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return [str(uuid.uuid4()) for _ in range(count)]


@register_generator("random_choice")
def gen_random_choice(col: ColumnDef, count: int, **kwargs) -> list:
    choices = col.choices
    if not choices:
        raise ValueError(f"Column '{col.name}': random_choice requires 'choices' list")
    if isinstance(choices, dict):
        choices = list(choices.keys())
    return [random.choice(choices) for _ in range(count)]


@register_generator("weighted_choice")
def gen_weighted_choice(col: ColumnDef, count: int, **kwargs) -> list:
    choices = col.choices
    if not isinstance(choices, dict):
        raise ValueError(f"Column '{col.name}': weighted_choice requires dict of choice: weight")
    keys = list(choices.keys())
    weights = list(choices.values())
    return random.choices(keys, weights=weights, k=count)


@register_generator("random_int")
def gen_random_int(col: ColumnDef, count: int, **kwargs) -> list[int]:
    lo = int(col.min or 0)
    hi = int(col.max or 100)
    return [random.randint(lo, hi) for _ in range(count)]


@register_generator("random_decimal")
def gen_random_decimal(col: ColumnDef, count: int, **kwargs) -> list[float]:
    lo = col.min or 0.0
    hi = col.max or 100.0
    prec = col.precision or 2
    return [round(random.uniform(lo, hi), prec) for _ in range(count)]


@register_generator("date_range")
def gen_date_range(col: ColumnDef, count: int, **kwargs) -> list:
    today = date.today()
    start = today - timedelta(days=col.start_days_ago or 365)
    end = today + timedelta(days=col.end_days_ahead or 0)
    delta = (end - start).days
    if delta <= 0:
        delta = 1

    is_datetime = col.type.upper() == "DATETIME"
    results = []
    for _ in range(count):
        d = start + timedelta(days=random.randint(0, delta))
        if is_datetime:
            hours = random.randint(0, 23)
            minutes = random.randint(0, 59)
            seconds = random.randint(0, 59)
            results.append(datetime(d.year, d.month, d.day, hours, minutes, seconds))
        else:
            results.append(d)
    return results


@register_generator("entity_ref")
def gen_entity_ref(col: ColumnDef, count: int, pool: EntityPool | None = None, **kwargs) -> list:
    if pool is None:
        raise ValueError(f"Column '{col.name}': entity_ref requires an entity pool")
    entity_type = col.entity
    field = col.field
    if not entity_type or not field:
        raise ValueError(f"Column '{col.name}': entity_ref requires 'entity' and 'field'")
    entities = pool.entities.get(entity_type, [])
    if not entities:
        raise ValueError(f"No entities of type '{entity_type}' in pool")
    return [random.choice(entities).get(field, "") for _ in range(count)]


@register_generator("compound")
def gen_compound(col: ColumnDef, count: int, pool: EntityPool | None = None, **kwargs) -> list[str]:
    """Generate strings from a template like '{product} - {company}'."""
    template = col.template
    if not template:
        raise ValueError(f"Column '{col.name}': compound requires 'template'")
    refs = col.refs or []
    if not pool:
        raise ValueError(f"Column '{col.name}': compound with refs requires entity pool")

    results = []
    for _ in range(count):
        replacements = {}
        for ref in refs:
            entities = pool.entities.get(ref, [])
            if entities:
                entity = random.choice(entities)
                replacements[ref] = entity.get("name", entity.get("full_name", ref))
        results.append(template.format(**replacements))
    return results


@register_generator("derived_from_date")
def gen_derived_from_date(
    col: ColumnDef, count: int, context: dict[str, list] | None = None, **kwargs
) -> list[str]:
    """Derive values from another date column (e.g., fiscal quarter)."""
    source = col.source_column
    fmt = col.format or "Q{quarter} {year}"
    if not source or not context or source not in context:
        raise ValueError(
            f"Column '{col.name}': derived_from_date requires 'source_column' "
            f"that exists in context"
        )
    source_values = context[source]
    results = []
    for val in source_values:
        if isinstance(val, (date, datetime)):
            d = val
        else:
            d = datetime.fromisoformat(str(val))
        quarter = (d.month - 1) // 3 + 1
        results.append(fmt.format(quarter=quarter, year=d.year, month=d.month, day=d.day))
    return results


@register_generator("stage_derived")
def gen_stage_derived(
    col: ColumnDef, count: int, context: dict[str, list] | None = None, **kwargs
) -> list:
    """Derive values based on a mapping from another column's values."""
    source = col.source_column
    mapping = col.mapping
    if not source or not mapping or not context or source not in context:
        raise ValueError(
            f"Column '{col.name}': stage_derived requires 'source_column', 'mapping', and context"
        )
    source_values = context[source]
    return [mapping.get(str(v), 0) for v in source_values]


@register_generator("faker")
def gen_faker(col: ColumnDef, count: int, **kwargs) -> list:
    """Pass-through to any Faker method."""
    method_name = col.faker_method
    if not method_name:
        raise ValueError(f"Column '{col.name}': faker generator requires 'faker_method'")
    method = getattr(fake, method_name, None)
    if not method:
        raise ValueError(f"Column '{col.name}': unknown Faker method '{method_name}'")
    args = col.faker_args or {}
    return [method(**args) for _ in range(count)]


@register_generator("sequence")
def gen_sequence(col: ColumnDef, count: int, **kwargs) -> list[str]:
    """Generate sequential IDs like INV-0001, INV-0002, etc."""
    template = col.template or "{i}"
    start = int(col.min or 1)
    return [template.format(i=start + i) for i in range(count)]


@register_generator("constant")
def gen_constant(col: ColumnDef, count: int, **kwargs) -> list:
    """Return a constant value for every row."""
    val = col.choices
    if isinstance(val, list):
        val = val[0] if val else ""
    return [val] * count

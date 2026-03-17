"""Salesforce-specific generators."""

from __future__ import annotations

import random

from faker import Faker

from datagen.generators.base import register_generator
from datagen.models import ColumnDef, EntityPool

fake = Faker()


@register_generator("sf_id")
def gen_sf_id(col: ColumnDef, count: int, **kwargs) -> list[str]:
    """Generate Salesforce-style 18-character IDs with a given prefix."""
    prefix = col.template or "006"
    return [f"{prefix}{fake.hexify('^' * 15, upper=True)}" for _ in range(count)]


@register_generator("sf_opportunity_name")
def gen_sf_opportunity_name(
    col: ColumnDef, count: int, pool: EntityPool | None = None, **kwargs
) -> list[str]:
    """Generate realistic opportunity names like 'Acme Corp - CloudSync Pro'."""
    if not pool:
        return [f"{fake.company()} - Deal" for _ in range(count)]
    companies = pool.entities.get("company", [])
    products = pool.entities.get("product", [])
    results = []
    for _ in range(count):
        company = random.choice(companies)["name"] if companies else fake.company()
        product = random.choice(products)["name"] if products else "Deal"
        results.append(f"{company} - {product}")
    return results


@register_generator("sf_case_subject")
def gen_sf_case_subject(col: ColumnDef, count: int, **kwargs) -> list[str]:
    """Generate realistic support case subjects."""
    prefixes = [
        "Issue with", "Cannot access", "Error in", "Request for",
        "Bug report:", "Feature request:", "Question about",
        "Performance issue in", "Login problem with", "Data missing from",
    ]
    areas = [
        "dashboard", "report", "user permissions", "data sync",
        "API integration", "billing", "export functionality",
        "mobile app", "SSO authentication", "scheduled reports",
        "data connector", "email notifications", "custom fields",
    ]
    return [f"{random.choice(prefixes)} {random.choice(areas)}" for _ in range(count)]


@register_generator("sf_lead_rating")
def gen_sf_lead_rating(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(["Hot", "Warm", "Cold"], weights=[0.2, 0.35, 0.45], k=count)

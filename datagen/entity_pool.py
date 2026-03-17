"""Shared entity pool for cross-dataset referential integrity."""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

from faker import Faker

from datagen.config import ENTITY_POOL_PATH
from datagen.models import EntityPool

DEFAULT_POOL_SIZES = {
    "company": 200,
    "person": 500,
    "product": 50,
    "sales_rep": 20,
    "campaign": 30,
}

INDUSTRIES = [
    "Technology", "Healthcare", "Finance", "Manufacturing", "Retail",
    "Education", "Real Estate", "Energy", "Media", "Consulting",
    "Telecommunications", "Transportation", "Hospitality", "Insurance",
    "Pharmaceuticals", "Automotive", "Agriculture", "Construction",
]

COMPANY_SIZES = ["SMB", "Mid-Market", "Enterprise"]

REGIONS = ["West", "East", "Central", "South", "Northeast", "Southeast", "International"]

PRODUCT_CATEGORIES = ["SaaS", "Hardware", "Services", "Support", "Training", "Consulting"]

CHANNELS = ["Email", "Social", "PPC", "Display", "Content", "Events", "Webinar", "Direct Mail"]

US_STATES = [
    ("San Francisco", "CA"), ("New York", "NY"), ("Chicago", "IL"),
    ("Austin", "TX"), ("Seattle", "WA"), ("Denver", "CO"),
    ("Boston", "MA"), ("Atlanta", "GA"), ("Portland", "OR"),
    ("Miami", "FL"), ("Nashville", "TN"), ("Phoenix", "AZ"),
    ("Minneapolis", "MN"), ("Charlotte", "NC"), ("Dallas", "TX"),
    ("Los Angeles", "CA"), ("Philadelphia", "PA"), ("Detroit", "MI"),
    ("Salt Lake City", "UT"), ("Raleigh", "NC"),
]


def generate_pool(
    seed: int = 42,
    pool_sizes: dict[str, int] | None = None,
) -> EntityPool:
    """Generate a fresh entity pool with realistic fake data."""
    sizes = {**DEFAULT_POOL_SIZES, **(pool_sizes or {})}
    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)

    entities: dict[str, list[dict]] = {}

    # Companies
    companies = []
    used_names: set[str] = set()
    for i in range(sizes["company"]):
        name = fake.company()
        while name in used_names:
            name = fake.company()
        used_names.add(name)
        city, state = random.choice(US_STATES)
        companies.append({
            "id": f"comp_{i:04d}",
            "account_id": f"001{fake.hexify('^^^^^^^^^^^^', upper=True)}",
            "name": name,
            "domain": name.lower().replace(" ", "").replace(",", "").replace("-", "") + ".com",
            "industry": random.choice(INDUSTRIES),
            "size": random.choice(COMPANY_SIZES),
            "city": city,
            "state": state,
            "annual_revenue": round(random.uniform(500_000, 50_000_000), 2),
            "employee_count": random.choice([10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]),
        })
    entities["company"] = companies

    # People (linked to companies)
    people = []
    titles = [
        "CEO", "CTO", "CFO", "VP Sales", "VP Marketing", "VP Engineering",
        "Director of Operations", "Product Manager", "Account Executive",
        "Marketing Manager", "Sales Manager", "Software Engineer",
        "Data Analyst", "HR Manager", "Customer Success Manager",
    ]
    for i in range(sizes["person"]):
        company = random.choice(companies)
        first = fake.first_name()
        last = fake.last_name()
        domain = company["domain"]
        people.append({
            "id": f"per_{i:04d}",
            "contact_id": f"003{fake.hexify('^^^^^^^^^^^^', upper=True)}",
            "first_name": first,
            "last_name": last,
            "full_name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}@{domain}",
            "company_id": company["id"],
            "company_name": company["name"],
            "title": random.choice(titles),
            "phone": fake.phone_number(),
        })
    entities["person"] = people

    # Products
    products = []
    product_adjectives = ["Cloud", "Smart", "Pro", "Elite", "Advanced", "Core", "Premium", "Ultra"]
    product_nouns = ["Sync", "Analytics", "Hub", "Suite", "Platform", "Engine", "Manager", "Connect"]
    used_product_names: set[str] = set()
    for i in range(sizes["product"]):
        name = f"{random.choice(product_adjectives)}{random.choice(product_nouns)}"
        while name in used_product_names:
            name = f"{random.choice(product_adjectives)}{random.choice(product_nouns)} {random.choice(['X', 'Plus', '2.0', 'Go'])}"
        used_product_names.add(name)
        products.append({
            "id": f"prod_{i:04d}",
            "name": name,
            "category": random.choice(PRODUCT_CATEGORIES),
            "unit_price": round(random.choice([29, 49, 99, 199, 299, 499, 999, 1999]) + random.uniform(0, 0.99), 2),
            "sku": f"{fake.lexify('???', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')}-{fake.numerify('###')}",
        })
    entities["product"] = products

    # Sales reps
    sales_reps = []
    for i in range(sizes["sales_rep"]):
        first = fake.first_name()
        last = fake.last_name()
        sales_reps.append({
            "id": f"rep_{i:04d}",
            "rep_id": f"005{fake.hexify('^^^^^^^^^^^^', upper=True)}",
            "first_name": first,
            "last_name": last,
            "full_name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}@ourcompany.com",
            "region": random.choice(REGIONS),
        })
    entities["sales_rep"] = sales_reps

    # Campaigns
    campaigns = []
    campaign_themes = [
        "Spring Launch", "Summer Sale", "Fall Promotion", "Holiday Special",
        "Product Launch", "Brand Awareness", "Lead Gen", "Webinar Series",
        "Content Blitz", "Partner Push", "Renewal Drive", "Upsell Campaign",
    ]
    for i in range(sizes["campaign"]):
        campaigns.append({
            "id": f"camp_{i:04d}",
            "name": f"{random.choice(campaign_themes)} {fake.year()}",
            "channel": random.choice(CHANNELS),
            "budget": round(random.uniform(5_000, 200_000), 2),
            "status": random.choice(["Active", "Completed", "Planned", "Paused"]),
        })
    entities["campaign"] = campaigns

    return EntityPool(
        generated_at=datetime.now(timezone.utc).isoformat(),
        seed=seed,
        entities=entities,
        pool_sizes=sizes,
    )


def save_pool(pool: EntityPool, path: Path | None = None) -> None:
    """Persist the entity pool to disk."""
    path = path or ENTITY_POOL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(pool.model_dump(), f, indent=2)


def load_pool(path: Path | None = None) -> EntityPool:
    """Load the entity pool from disk."""
    path = path or ENTITY_POOL_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Entity pool not found at {path}. Run 'datagen pool regenerate' first."
        )
    with open(path) as f:
        return EntityPool.model_validate(json.load(f))


def sample_entities(pool: EntityPool, entity_type: str, count: int) -> list[dict]:
    """Sample entities from the pool with replacement."""
    entities = pool.entities.get(entity_type, [])
    if not entities:
        raise ValueError(f"No entities of type '{entity_type}' in pool")
    return [random.choice(entities) for _ in range(count)]

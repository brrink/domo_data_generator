"""Marketing/Ads platform generators (Google Ads, Facebook Ads, HubSpot)."""

from __future__ import annotations

import random
import string

from datagen.generators.base import register_generator
from datagen.models import ColumnDef

AD_PLATFORMS = ["Google Ads", "Facebook Ads", "LinkedIn Ads", "Instagram Ads", "Twitter Ads"]
CAMPAIGN_OBJECTIVES = ["Conversions", "Traffic", "Brand Awareness", "Lead Generation", "App Installs", "Video Views"]
AD_FORMATS = ["Search", "Display", "Video", "Carousel", "Single Image", "Collection", "Stories"]
TARGETING_TYPES = ["Keywords", "Interest", "Lookalike", "Retargeting", "Custom Audience", "Demographic"]

HUBSPOT_LIFECYCLE_STAGES = ["Subscriber", "Lead", "MQL", "SQL", "Opportunity", "Customer", "Evangelist"]
HUBSPOT_LEAD_STATUSES = ["New", "Open", "In Progress", "Attempted to Contact", "Connected", "Qualified", "Unqualified"]

AD_HEADLINES = [
    "Transform Your Business Today",
    "Get Started Free",
    "See Why Teams Love Us",
    "Boost Productivity 10x",
    "Limited Time Offer",
    "The #1 Rated Solution",
    "Request Your Demo",
    "Save 30% This Month",
    "Join 10,000+ Companies",
    "Try It Risk-Free",
]

KEYWORDS = [
    "business analytics", "data visualization", "dashboard software",
    "BI tools", "reporting platform", "data integration",
    "cloud analytics", "real-time dashboards", "data warehouse",
    "self-service BI", "embedded analytics", "ETL tools",
    "KPI tracking", "business intelligence", "data connector",
]


@register_generator("ad_platform")
def gen_ad_platform(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(AD_PLATFORMS, weights=[0.35, 0.30, 0.15, 0.12, 0.08], k=count)


@register_generator("campaign_objective")
def gen_campaign_objective(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return [random.choice(CAMPAIGN_OBJECTIVES) for _ in range(count)]


@register_generator("ad_format")
def gen_ad_format(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return [random.choice(AD_FORMATS) for _ in range(count)]


@register_generator("ad_headline")
def gen_ad_headline(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return [random.choice(AD_HEADLINES) for _ in range(count)]


@register_generator("ad_keyword")
def gen_ad_keyword(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return [random.choice(KEYWORDS) for _ in range(count)]


@register_generator("targeting_type")
def gen_targeting_type(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return [random.choice(TARGETING_TYPES) for _ in range(count)]


@register_generator("impressions")
def gen_impressions(col: ColumnDef, count: int, **kwargs) -> list[int]:
    """Generate impression counts with realistic distribution."""
    lo = int(col.min or 100)
    hi = int(col.max or 100000)
    return [int(random.lognormvariate(8, 1.5)) % (hi - lo) + lo for _ in range(count)]


@register_generator("clicks_from_impressions")
def gen_clicks_from_impressions(
    col: ColumnDef, count: int, context: dict | None = None, **kwargs
) -> list[int]:
    """Generate clicks based on impressions column with realistic CTR."""
    source = col.source_column
    if source and context and source in context:
        impressions = context[source]
        return [max(0, int(imp * random.uniform(0.005, 0.08))) for imp in impressions]
    return [random.randint(5, 500) for _ in range(count)]


@register_generator("ctr")
def gen_ctr(col: ColumnDef, count: int, context: dict | None = None, **kwargs) -> list[float]:
    """Calculate CTR from clicks and impressions columns."""
    clicks_col = col.refs[0] if col.refs else None
    impressions_col = col.refs[1] if col.refs and len(col.refs) > 1 else None
    if clicks_col and impressions_col and context:
        clicks = context.get(clicks_col, [])
        impressions = context.get(impressions_col, [])
        return [
            round(c / i * 100, 2) if i > 0 else 0.0
            for c, i in zip(clicks, impressions)
        ]
    return [round(random.uniform(0.5, 8.0), 2) for _ in range(count)]


@register_generator("cost_per_click")
def gen_cost_per_click(col: ColumnDef, count: int, **kwargs) -> list[float]:
    lo = col.min or 0.20
    hi = col.max or 15.0
    return [round(random.uniform(lo, hi), 2) for _ in range(count)]


@register_generator("ad_spend")
def gen_ad_spend(col: ColumnDef, count: int, context: dict | None = None, **kwargs) -> list[float]:
    """Calculate spend from clicks * CPC."""
    clicks_col = col.refs[0] if col.refs else None
    cpc_col = col.refs[1] if col.refs and len(col.refs) > 1 else None
    if clicks_col and cpc_col and context:
        clicks = context.get(clicks_col, [])
        cpcs = context.get(cpc_col, [])
        return [round(c * cpc, 2) for c, cpc in zip(clicks, cpcs)]
    return [round(random.uniform(50, 5000), 2) for _ in range(count)]


@register_generator("conversions_from_clicks")
def gen_conversions(col: ColumnDef, count: int, context: dict | None = None, **kwargs) -> list[int]:
    """Generate conversions from clicks with a conversion rate."""
    source = col.source_column
    if source and context and source in context:
        clicks = context[source]
        return [max(0, int(c * random.uniform(0.02, 0.15))) for c in clicks]
    return [random.randint(0, 50) for _ in range(count)]


@register_generator("hubspot_lifecycle")
def gen_hubspot_lifecycle(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(
        HUBSPOT_LIFECYCLE_STAGES,
        weights=[0.25, 0.25, 0.15, 0.12, 0.08, 0.12, 0.03],
        k=count,
    )


@register_generator("hubspot_lead_status")
def gen_hubspot_lead_status(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(
        HUBSPOT_LEAD_STATUSES,
        weights=[0.20, 0.20, 0.15, 0.15, 0.10, 0.10, 0.10],
        k=count,
    )


@register_generator("ad_group_id")
def gen_ad_group_id(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return ["".join(random.choices(string.digits, k=12)) for _ in range(count)]

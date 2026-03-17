"""Google Analytics-specific generators."""

from __future__ import annotations

import random
import string

from datagen.generators.base import register_generator
from datagen.models import ColumnDef

PAGES = [
    "/", "/about", "/pricing", "/contact", "/blog", "/features",
    "/demo", "/signup", "/login", "/docs", "/support", "/careers",
    "/blog/getting-started", "/blog/best-practices", "/blog/case-study",
    "/product/overview", "/product/enterprise", "/product/integrations",
    "/resources/webinar", "/resources/whitepaper", "/resources/roi-calculator",
]

TRAFFIC_SOURCES = ["google", "direct", "facebook", "linkedin", "bing", "twitter", "email", "referral"]
MEDIUMS = ["organic", "cpc", "social", "email", "referral", "(none)"]
CAMPAIGNS = ["brand", "non-brand", "retargeting", "spring-promo", "webinar-invite", "(not set)"]
BROWSERS = ["Chrome", "Safari", "Firefox", "Edge", "Samsung Internet"]
DEVICE_CATEGORIES = ["desktop", "mobile", "tablet"]
COUNTRIES = ["United States", "United Kingdom", "Canada", "Australia", "Germany", "France", "India", "Japan", "Brazil"]
LANDING_PAGES = ["/", "/pricing", "/features", "/demo", "/blog/getting-started", "/signup"]


@register_generator("ga_session_id")
def gen_ga_session_id(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return [
        "".join(random.choices(string.digits, k=10)) + "." + "".join(random.choices(string.digits, k=10))
        for _ in range(count)
    ]


@register_generator("ga_page_path")
def gen_ga_page_path(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return [random.choice(PAGES) for _ in range(count)]


@register_generator("ga_source")
def gen_ga_source(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(TRAFFIC_SOURCES, weights=[0.35, 0.25, 0.10, 0.08, 0.05, 0.05, 0.07, 0.05], k=count)


@register_generator("ga_medium")
def gen_ga_medium(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(MEDIUMS, weights=[0.35, 0.20, 0.12, 0.10, 0.08, 0.15], k=count)


@register_generator("ga_campaign")
def gen_ga_campaign(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(CAMPAIGNS, weights=[0.25, 0.20, 0.15, 0.10, 0.05, 0.25], k=count)


@register_generator("ga_browser")
def gen_ga_browser(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(BROWSERS, weights=[0.55, 0.20, 0.10, 0.10, 0.05], k=count)


@register_generator("ga_device_category")
def gen_ga_device_category(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(DEVICE_CATEGORIES, weights=[0.55, 0.35, 0.10], k=count)


@register_generator("ga_country")
def gen_ga_country(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(COUNTRIES, weights=[0.45, 0.10, 0.08, 0.05, 0.05, 0.05, 0.10, 0.05, 0.07], k=count)


@register_generator("ga_bounce_rate")
def gen_ga_bounce_rate(col: ColumnDef, count: int, **kwargs) -> list[float]:
    """Generate bounce rates biased toward 40-70%."""
    return [round(min(1.0, max(0.0, random.gauss(0.55, 0.15))), 4) for _ in range(count)]


@register_generator("ga_session_duration")
def gen_ga_session_duration(col: ColumnDef, count: int, **kwargs) -> list[int]:
    """Generate session durations in seconds, with many short sessions."""
    results = []
    for _ in range(count):
        if random.random() < 0.3:
            results.append(random.randint(0, 10))  # bounced
        else:
            results.append(random.randint(10, 900))
    return results


@register_generator("ga_pageviews")
def gen_ga_pageviews(col: ColumnDef, count: int, **kwargs) -> list[int]:
    """Generate pageview counts per session."""
    return [max(1, int(random.expovariate(0.3))) for _ in range(count)]


@register_generator("ga_landing_page")
def gen_ga_landing_page(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(LANDING_PAGES, weights=[0.30, 0.20, 0.15, 0.15, 0.10, 0.10], k=count)

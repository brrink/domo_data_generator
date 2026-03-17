"""Financial/ERP-specific generators (QuickBooks/NetSuite style)."""

from __future__ import annotations

import random
from datetime import date

from datagen.generators.base import register_generator
from datagen.models import ColumnDef

GL_ACCOUNTS = {
    "1000": "Cash",
    "1100": "Accounts Receivable",
    "1200": "Inventory",
    "1500": "Fixed Assets",
    "2000": "Accounts Payable",
    "2100": "Accrued Liabilities",
    "3000": "Retained Earnings",
    "4000": "Revenue - Product",
    "4100": "Revenue - Services",
    "4200": "Revenue - Subscriptions",
    "5000": "Cost of Goods Sold",
    "5100": "Cost of Services",
    "6000": "Salaries & Wages",
    "6100": "Rent Expense",
    "6200": "Utilities",
    "6300": "Marketing Expense",
    "6400": "Travel & Entertainment",
    "6500": "Software & Subscriptions",
    "6600": "Insurance",
    "6700": "Depreciation",
    "7000": "Interest Expense",
    "8000": "Other Income",
    "9000": "Tax Expense",
}

PAYMENT_TERMS = ["Net 15", "Net 30", "Net 45", "Net 60", "Due on Receipt"]
PAYMENT_METHODS = ["ACH", "Wire", "Check", "Credit Card", "PayPal"]
INVOICE_STATUSES = ["Paid", "Open", "Overdue", "Partial", "Void"]
JOURNAL_TYPES = ["Standard", "Adjusting", "Closing", "Reversing"]
DEPARTMENTS = ["Sales", "Marketing", "Engineering", "Operations", "Finance", "HR", "Support"]


@register_generator("gl_account_code")
def gen_gl_account_code(col: ColumnDef, count: int, **kwargs) -> list[str]:
    codes = list(GL_ACCOUNTS.keys())
    return [random.choice(codes) for _ in range(count)]


@register_generator("gl_account_name")
def gen_gl_account_name(col: ColumnDef, count: int, context: dict | None = None, **kwargs) -> list[str]:
    """Derive GL account name from the account code column."""
    source = col.source_column
    if source and context and source in context:
        return [GL_ACCOUNTS.get(str(code), "Unknown") for code in context[source]]
    codes = list(GL_ACCOUNTS.keys())
    return [GL_ACCOUNTS[random.choice(codes)] for _ in range(count)]


@register_generator("invoice_number")
def gen_invoice_number(col: ColumnDef, count: int, **kwargs) -> list[str]:
    prefix = col.template or "INV"
    start = int(col.min or 10001)
    return [f"{prefix}-{start + i}" for i in range(count)]


@register_generator("payment_terms")
def gen_payment_terms(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(PAYMENT_TERMS, weights=[0.10, 0.40, 0.20, 0.15, 0.15], k=count)


@register_generator("payment_method")
def gen_payment_method(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(PAYMENT_METHODS, weights=[0.30, 0.15, 0.15, 0.30, 0.10], k=count)


@register_generator("invoice_status")
def gen_invoice_status(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(INVOICE_STATUSES, weights=[0.45, 0.25, 0.15, 0.10, 0.05], k=count)


@register_generator("journal_type")
def gen_journal_type(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return random.choices(JOURNAL_TYPES, weights=[0.60, 0.20, 0.10, 0.10], k=count)


@register_generator("department")
def gen_department(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return [random.choice(DEPARTMENTS) for _ in range(count)]


@register_generator("fiscal_period")
def gen_fiscal_period(col: ColumnDef, count: int, context: dict | None = None, **kwargs) -> list[str]:
    """Generate fiscal period like 'FY2026-03' from a date column."""
    source = col.source_column
    if source and context and source in context:
        results = []
        for val in context[source]:
            if isinstance(val, date):
                results.append(f"FY{val.year}-{val.month:02d}")
            else:
                results.append(f"FY{date.today().year}-01")
        return results
    today = date.today()
    return [f"FY{today.year}-{random.randint(1,12):02d}" for _ in range(count)]


@register_generator("debit_credit")
def gen_debit_credit(col: ColumnDef, count: int, **kwargs) -> list[str]:
    return [random.choice(["Debit", "Credit"]) for _ in range(count)]

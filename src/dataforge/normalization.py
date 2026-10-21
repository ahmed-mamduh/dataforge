"""Data normalization — whitespace, price parsing, currency."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

import pandas as pd


def normalize_whitespace(value: str) -> str:
    """Strip leading/trailing whitespace and collapse internal runs."""
    if not isinstance(value, str):
        return value
    return re.sub(r"\s+", " ", value.strip())


def parse_price(value: str) -> Decimal | None:
    """Parse a price string to Decimal.

    Handles: currency symbols, thousands commas, whitespace.
    Returns None for unparseable values (N/A, bad-price, empty, etc.).
    """
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    cleaned = re.sub(r"[£€$¥]", "", cleaned).strip()

    cleaned = cleaned.replace(",", "")

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def normalize_currency(value: str) -> str:
    """Uppercase and strip a currency code."""
    if not isinstance(value, str):
        return value
    return value.strip().upper()


def normalize_quantity(value: str) -> int | None:
    """Parse a quantity string to int. Returns None for non-integer values."""
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        as_float = float(cleaned)
        as_int = int(as_float)
        if as_float != as_int:
            return None
        return as_int
    except (ValueError, OverflowError):
        return None


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply per-column normalization to a DataFrame with canonical column names."""
    df = df.copy()

    text_cols = ["sku", "product_name", "category", "supplier", "description"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda v: normalize_whitespace(v) if isinstance(v, str) else v
            )

    if "price" in df.columns:
        df["_original_price"] = df["price"]
        df["price"] = df["price"].apply(parse_price)

    if "currency" in df.columns:
        df["currency"] = df["currency"].apply(normalize_currency)

    if "quantity" in df.columns:
        df["_original_quantity"] = df["quantity"]
        df["quantity"] = df["quantity"].apply(normalize_quantity)

    return df

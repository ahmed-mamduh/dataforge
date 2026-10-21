"""Data normalization — whitespace, price parsing, currency."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

import pandas as pd

_CURRENCY_SYMBOLS = re.compile(r"[£€$¥]")
_US_THOUSANDS_ONLY = re.compile(r"^\d{1,3}(,\d{3})+$")
_US_WITH_DECIMAL = re.compile(r"^\d{1,3}(,\d{3})*\.\d+$")
_PLAIN_DECIMAL = re.compile(r"^\d+\.\d+$")
_PLAIN_INTEGER = re.compile(r"^\d+$")


def normalize_whitespace(value: str) -> str:
    """Strip leading/trailing whitespace and collapse internal runs."""
    if not isinstance(value, str):
        return value
    return re.sub(r"\s+", " ", value.strip())


def _parse_us_number_body(body: str) -> str | None:
    """Parse an unsigned US-style numeric string. Returns normalized text for Decimal."""
    if not body or not re.fullmatch(r"[\d.,]+", body):
        return None

    if "," in body and "." in body:
        if body.rfind(",") > body.rfind("."):
            return None
        if not _US_WITH_DECIMAL.fullmatch(body):
            return None
        return body.replace(",", "")

    if "," in body:
        if not _US_THOUSANDS_ONLY.fullmatch(body):
            return None
        return body.replace(",", "")

    if body.count(".") > 1:
        return None

    if "." in body:
        if not _PLAIN_DECIMAL.fullmatch(body):
            return None
        return body

    if _PLAIN_INTEGER.fullmatch(body):
        return body

    return None


def parse_price(value: str) -> Decimal | None:
    """Parse a price string to Decimal using unambiguous US number formats.

    Supports plain decimals (1234.50), US thousands separators (1,234.50),
    and currency symbols. Comma-decimal values (e.g. 12,99) and European
    grouping (e.g. 1.234,50) are rejected rather than reinterpreted.
    """
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    cleaned = _CURRENCY_SYMBOLS.sub("", cleaned).strip()
    if not cleaned:
        return None

    negative = False
    if cleaned[0] == "-":
        negative = True
        cleaned = cleaned[1:].strip()
    elif cleaned[0] == "+":
        cleaned = cleaned[1:].strip()

    if not cleaned:
        return None

    normalized = _parse_us_number_body(cleaned)
    if normalized is None:
        return None

    try:
        amount = Decimal(normalized)
    except InvalidOperation:
        return None

    return -amount if negative else amount


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

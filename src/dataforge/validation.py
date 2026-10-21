"""Row-level validation — required fields, type/range checks, reason codes."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from dataforge.config import ValidationConfig


def validate_dataframe(
    df: pd.DataFrame,
    config: ValidationConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a normalized DataFrame into valid and rejected rows.

    Returns (valid_df, rejected_df). Rejected rows include a
    '_rejection_reasons' column with a semicolon-separated list of reasons.
    """
    df = df.copy()
    reasons: list[list[str]] = [[] for _ in range(len(df))]

    for field in config.required_fields:
        if field not in df.columns:
            for r in reasons:
                r.append(f"missing_column:{field}")
            continue
        for i, val in enumerate(df[field]):
            if _is_blank(val):
                reasons[i].append(f"missing_required:{field}")

    if "price" in df.columns:
        for i, val in enumerate(df["price"]):
            if _is_blank(val):
                original = df["_original_price"].iloc[i] if "_original_price" in df.columns else ""
                reasons[i].append(f"invalid_price:{original}")
            elif isinstance(val, Decimal) and val < config.min_price:
                reasons[i].append(f"negative_price:{val}")

    if "quantity" in df.columns:
        for i, val in enumerate(df["quantity"]):
            if _is_blank(val):
                original = df["_original_quantity"].iloc[i] if "_original_quantity" in df.columns else ""
                reasons[i].append(f"invalid_quantity:{original}")
            elif isinstance(val, (int, float)) and not pd.isna(val) and val < config.min_quantity:
                reasons[i].append(f"negative_quantity:{val}")

    if "currency" in df.columns:
        for i, val in enumerate(df["currency"]):
            if isinstance(val, str) and val and val not in config.allowed_currencies:
                reasons[i].append(f"unknown_currency:{val}")

    reject_mask = [len(r) > 0 for r in reasons]

    rejected = df.loc[reject_mask].copy()
    rejected["_rejection_reasons"] = ["; ".join(r) for r in reasons if r]

    valid = df.loc[[not m for m in reject_mask]].copy()

    return valid, rejected


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    return False

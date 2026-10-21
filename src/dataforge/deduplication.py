"""Duplicate detection on configurable composite keys."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from dataforge.config import DeduplicationConfig


def deduplicate(
    df: pd.DataFrame,
    config: DeduplicationConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remove duplicate rows based on composite key fields.

    Rows with any missing key field are never considered duplicates and are
    always kept (they already failed validation or are legitimately keyless).

    Returns (unique_df, duplicate_df). Duplicate rows get a '_rejection_reasons'
    column.
    """
    df = df.copy()

    missing_key_cols = [f for f in config.key_fields if f not in df.columns]
    if missing_key_cols:
        return df, pd.DataFrame(columns=df.columns)

    def _build_key(row: pd.Series) -> str | None:
        parts = []
        for field in config.key_fields:
            val = row.get(field)
            if val is None or (isinstance(val, str) and val.strip() == ""):
                return None
            parts.append(str(val).strip().lower())
        return "|".join(parts)

    keys = df.apply(_build_key, axis=1)

    seen: set[str] = set()
    is_dup: list[bool] = []
    for key in keys:
        if key is None:
            is_dup.append(False)
        elif key in seen:
            is_dup.append(True)
        else:
            seen.add(key)
            is_dup.append(False)

    unique = df.loc[[not d for d in is_dup]].copy()
    duplicates = df.loc[is_dup].copy()

    if len(duplicates) > 0:
        duplicates["_rejection_reasons"] = "duplicate"

    return unique, duplicates

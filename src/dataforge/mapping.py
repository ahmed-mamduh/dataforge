"""Column mapping — resolve source headers to canonical field names."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from dataforge.config import ColumnMapping

logger = logging.getLogger(__name__)


class MappingError(Exception):
    pass


def select_mapping(
    source_columns: list[str],
    mappings: list[ColumnMapping],
) -> ColumnMapping:
    """Pick the mapping with the highest match score for the given columns."""
    if not mappings:
        raise MappingError("No column mappings configured")

    scored = [(m, m.match_score(source_columns)) for m in mappings]
    scored.sort(key=lambda x: x[1], reverse=True)
    best, score = scored[0]

    if score == 0:
        raise MappingError(
            f"No mapping matched any of the source columns: {source_columns}"
        )

    return best


def apply_mapping(df: pd.DataFrame, mapping: ColumnMapping) -> pd.DataFrame:
    """Rename source columns to canonical names. Unmapped columns are kept."""
    rename_map = mapping.resolve(list(df.columns))
    unmapped = [c for c in df.columns if c not in rename_map and not c.startswith("_")]
    if unmapped:
        logger.warning("Unmapped columns (kept as-is): %s", unmapped)
    return df.rename(columns=rename_map)

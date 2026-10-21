"""Tests for duplicate detection."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from dataforge.config import DeduplicationConfig
from dataforge.deduplication import deduplicate


def _make_df(**kwargs: list) -> pd.DataFrame:
    return pd.DataFrame(kwargs)


def test_exact_duplicate_removed() -> None:
    df = _make_df(
        sku=["A001", "A001"],
        supplier=["S1", "S1"],
        product_name=["W", "W"],
    )
    unique, dups = deduplicate(df, DeduplicationConfig())
    assert len(unique) == 1
    assert len(dups) == 1
    assert "duplicate" in dups["_rejection_reasons"].iloc[0]


def test_different_suppliers_not_duplicate() -> None:
    df = _make_df(
        sku=["A001", "A001"],
        supplier=["S1", "S2"],
        product_name=["W", "W"],
    )
    unique, dups = deduplicate(df, DeduplicationConfig())
    assert len(unique) == 2
    assert len(dups) == 0


def test_missing_sku_not_deduped() -> None:
    df = _make_df(
        sku=["", ""],
        supplier=["S1", "S1"],
        product_name=["W1", "W2"],
    )
    unique, dups = deduplicate(df, DeduplicationConfig())
    assert len(unique) == 2
    assert len(dups) == 0


def test_case_insensitive_key() -> None:
    df = _make_df(
        sku=["A001", "a001"],
        supplier=["Supplier A", "supplier a"],
        product_name=["W", "W"],
    )
    unique, dups = deduplicate(df, DeduplicationConfig())
    assert len(unique) == 1
    assert len(dups) == 1


def test_first_occurrence_kept() -> None:
    df = _make_df(
        sku=["A001", "A001"],
        supplier=["S1", "S1"],
        product_name=["First", "Second"],
    )
    unique, _ = deduplicate(df, DeduplicationConfig())
    assert unique["product_name"].iloc[0] == "First"


def test_configurable_key_fields() -> None:
    config = DeduplicationConfig(key_fields=["sku"])
    df = _make_df(
        sku=["A001", "A001"],
        supplier=["S1", "S2"],
        product_name=["W1", "W2"],
    )
    unique, dups = deduplicate(df, config)
    assert len(unique) == 1
    assert len(dups) == 1


def test_no_duplicates() -> None:
    df = _make_df(
        sku=["A001", "A002", "A003"],
        supplier=["S1", "S1", "S1"],
    )
    unique, dups = deduplicate(df, DeduplicationConfig())
    assert len(unique) == 3
    assert len(dups) == 0

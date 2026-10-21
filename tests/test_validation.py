"""Tests for row validation."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from dataforge.config import ValidationConfig
from dataforge.validation import validate_dataframe


def _make_df(**kwargs: list) -> pd.DataFrame:
    return pd.DataFrame(kwargs)


def test_valid_row_passes() -> None:
    df = _make_df(
        sku=["A001"],
        product_name=["Widget"],
        price=[Decimal("10.00")],
        quantity=[5],
        currency=["USD"],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(valid) == 1
    assert len(rejected) == 0


def test_missing_sku_rejected() -> None:
    df = _make_df(
        sku=[""],
        product_name=["Widget"],
        price=[Decimal("10.00")],
        quantity=[5],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(rejected) == 1
    assert "missing_required:sku" in rejected["_rejection_reasons"].iloc[0]


def test_missing_product_name_rejected() -> None:
    df = _make_df(
        sku=["A001"],
        product_name=["  "],
        price=[Decimal("10.00")],
        quantity=[5],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(rejected) == 1
    assert "missing_required:product_name" in rejected["_rejection_reasons"].iloc[0]


def test_negative_price_rejected() -> None:
    df = _make_df(
        sku=["A001"],
        product_name=["Widget"],
        price=[Decimal("-9.99")],
        quantity=[5],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(rejected) == 1
    assert "negative_price" in rejected["_rejection_reasons"].iloc[0]


def test_invalid_price_rejected() -> None:
    df = _make_df(
        sku=["A001"],
        product_name=["Widget"],
        price=[None],
        quantity=[5],
        _original_price=["bad-price"],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(rejected) == 1
    assert "invalid_price" in rejected["_rejection_reasons"].iloc[0]


def test_negative_quantity_rejected() -> None:
    df = _make_df(
        sku=["A001"],
        product_name=["Widget"],
        price=[Decimal("10.00")],
        quantity=[-3],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(rejected) == 1
    assert "negative_quantity" in rejected["_rejection_reasons"].iloc[0]


def test_invalid_quantity_rejected() -> None:
    df = _make_df(
        sku=["A001"],
        product_name=["Widget"],
        price=[Decimal("10.00")],
        quantity=[None],
        _original_quantity=["not-known"],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(rejected) == 1
    assert "invalid_quantity" in rejected["_rejection_reasons"].iloc[0]


def test_zero_quantity_valid() -> None:
    df = _make_df(
        sku=["A001"],
        product_name=["Widget"],
        price=[Decimal("10.00")],
        quantity=[0],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(valid) == 1
    assert len(rejected) == 0


def test_zero_price_valid() -> None:
    df = _make_df(
        sku=["A001"],
        product_name=["Widget"],
        price=[Decimal("0")],
        quantity=[5],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(valid) == 1


def test_multiple_reasons_on_one_row() -> None:
    df = _make_df(
        sku=[""],
        product_name=[""],
        price=[None],
        quantity=[None],
        _original_price=["x"],
        _original_quantity=["y"],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(rejected) == 1
    reasons = rejected["_rejection_reasons"].iloc[0]
    assert "missing_required:sku" in reasons
    assert "missing_required:product_name" in reasons
    assert "invalid_price" in reasons
    assert "invalid_quantity" in reasons


def test_row_count_reconciliation() -> None:
    df = _make_df(
        sku=["A001", "", "A003"],
        product_name=["W1", "W2", "W3"],
        price=[Decimal("10"), Decimal("20"), Decimal("-5")],
        quantity=[1, 2, 3],
    )
    valid, rejected = validate_dataframe(df, ValidationConfig())
    assert len(valid) + len(rejected) == len(df)

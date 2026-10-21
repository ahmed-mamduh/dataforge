"""Tests for data normalization."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from dataforge.normalization import (
    normalize_currency,
    normalize_dataframe,
    normalize_quantity,
    normalize_whitespace,
    parse_price,
)


class TestNormalizeWhitespace:
    def test_strips_leading_trailing(self) -> None:
        assert normalize_whitespace("  hello  ") == "hello"

    def test_collapses_internal(self) -> None:
        assert normalize_whitespace("hello   world") == "hello world"

    def test_preserves_case(self) -> None:
        assert normalize_whitespace("  DISH DRYING MAT  ") == "DISH DRYING MAT"

    def test_empty_string(self) -> None:
        assert normalize_whitespace("") == ""

    def test_only_whitespace(self) -> None:
        assert normalize_whitespace("   ") == ""


class TestParsePrice:
    def test_plain_number(self) -> None:
        assert parse_price("12.99") == Decimal("12.99")

    def test_dollar_sign(self) -> None:
        assert parse_price("$25.50") == Decimal("25.50")

    def test_thousands_comma(self) -> None:
        assert parse_price("$1,234.50") == Decimal("1234.50")

    def test_negative(self) -> None:
        assert parse_price("-9.99") == Decimal("-9.99")

    def test_bad_price(self) -> None:
        assert parse_price("bad-price") is None

    def test_na(self) -> None:
        assert parse_price("N/A") is None

    def test_empty(self) -> None:
        assert parse_price("") is None

    def test_euro_symbol(self) -> None:
        assert parse_price("€15.00") == Decimal("15.00")

    def test_whitespace(self) -> None:
        assert parse_price("  $10.00  ") == Decimal("10.00")

    def test_zero(self) -> None:
        assert parse_price("0") == Decimal("0")

    def test_not_a_number(self) -> None:
        assert parse_price("not-known") is None

    def test_comma_decimal_rejected(self) -> None:
        assert parse_price("12,99") is None

    def test_european_format_rejected(self) -> None:
        assert parse_price("1.234,50") is None

    def test_malformed_thousands_rejected(self) -> None:
        assert parse_price("1,234,50") is None
        assert parse_price("12,3456") is None

    def test_us_thousands_without_decimal(self) -> None:
        assert parse_price("1,234") == Decimal("1234")

    def test_plain_decimal(self) -> None:
        assert parse_price("1234.50") == Decimal("1234.50")


class TestNormalizeCurrency:
    def test_uppercase(self) -> None:
        assert normalize_currency("usd") == "USD"

    def test_strips_whitespace(self) -> None:
        assert normalize_currency("  EUR  ") == "EUR"


class TestNormalizeQuantity:
    def test_integer(self) -> None:
        assert normalize_quantity("42") == 42

    def test_zero(self) -> None:
        assert normalize_quantity("0") == 0

    def test_negative(self) -> None:
        assert normalize_quantity("-3") == -3

    def test_non_numeric(self) -> None:
        assert normalize_quantity("not-known") is None

    def test_empty(self) -> None:
        assert normalize_quantity("") is None

    def test_float_whole(self) -> None:
        assert normalize_quantity("5.0") == 5

    def test_float_fractional(self) -> None:
        assert normalize_quantity("5.5") is None


class TestNormalizeDataframe:
    def test_price_becomes_decimal(self) -> None:
        df = pd.DataFrame({"price": ["$12.99", "bad-price"]})
        result = normalize_dataframe(df)
        assert result["price"].iloc[0] == Decimal("12.99")
        assert result["price"].iloc[1] is None

    def test_whitespace_trimmed_in_text_fields(self) -> None:
        df = pd.DataFrame({"product_name": ["  Tea Infuser Mesh  "]})
        result = normalize_dataframe(df)
        assert result["product_name"].iloc[0] == "Tea Infuser Mesh"

    def test_original_price_preserved(self) -> None:
        df = pd.DataFrame({"price": ["$1,234.50"]})
        result = normalize_dataframe(df)
        assert result["_original_price"].iloc[0] == "$1,234.50"

    def test_comma_decimal_becomes_invalid_price(self) -> None:
        df = pd.DataFrame({"price": ["12,99"]})
        result = normalize_dataframe(df)
        assert result["price"].iloc[0] is None
        assert result["_original_price"].iloc[0] == "12,99"

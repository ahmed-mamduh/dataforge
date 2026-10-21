"""Tests for file ingestion."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from dataforge.ingestion import IngestionError, read_file


def test_read_csv_supplier_a(supplier_a_path: Path) -> None:
    df = read_file(supplier_a_path)
    assert len(df) == 41
    assert "_source_file" in df.columns
    assert "_source_row" in df.columns
    assert df["_source_file"].iloc[0] == "supplier_a.csv"
    assert df["_source_row"].iloc[0] == 2  # first data row


def test_read_csv_supplier_b(supplier_b_path: Path) -> None:
    df = read_file(supplier_b_path)
    assert len(df) == 42
    assert df["_source_file"].iloc[0] == "supplier_b.csv"


def test_all_columns_read_as_strings(supplier_a_path: Path) -> None:
    df = read_file(supplier_a_path)
    for col in df.columns:
        if col.startswith("_"):
            continue
        assert pd.api.types.is_string_dtype(df[col]), f"Column {col} should be string dtype"


def test_leading_zeros_preserved(tmp_path: Path) -> None:
    csv_path = tmp_path / "leading_zeros.csv"
    csv_path.write_text("SKU,Name\n001,Widget\n002,Gadget\n", encoding="utf-8")
    df = read_file(csv_path)
    assert df["SKU"].iloc[0] == "001"
    assert df["SKU"].iloc[1] == "002"


def test_unsupported_extension(tmp_path: Path) -> None:
    bad = tmp_path / "data.json"
    bad.write_text("{}")
    with pytest.raises(IngestionError, match="Unsupported"):
        read_file(bad)


def test_legacy_xls_not_supported(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.xls"
    legacy.write_bytes(b"\x00\x00")
    with pytest.raises(IngestionError, match="Unsupported"):
        read_file(legacy)


def test_file_not_found() -> None:
    with pytest.raises(IngestionError, match="not found"):
        read_file(Path("nonexistent.csv"))


def test_source_row_numbers(supplier_a_path: Path) -> None:
    df = read_file(supplier_a_path)
    assert list(df["_source_row"][:3]) == [2, 3, 4]
    assert df["_source_row"].iloc[-1] == len(df) + 1

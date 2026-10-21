"""Tests for column mapping."""

from __future__ import annotations

import pandas as pd
import pytest

from dataforge.config import SUPPLIER_A_MAPPING, SUPPLIER_B_MAPPING, DEFAULT_MAPPINGS
from dataforge.mapping import MappingError, apply_mapping, select_mapping


def test_supplier_a_mapping_resolves() -> None:
    cols = ["SKU", "Product Name", "Category", "Unit Price", "Currency", "Qty", "Supplier", "Description"]
    resolved = SUPPLIER_A_MAPPING.resolve(cols)
    assert resolved["SKU"] == "sku"
    assert resolved["Unit Price"] == "price"
    assert resolved["Qty"] == "quantity"


def test_supplier_b_mapping_resolves() -> None:
    cols = ["Item Code", "Item Name", "Product Type", "Price", "Currency Code", "Available", "Vendor", "Details"]
    resolved = SUPPLIER_B_MAPPING.resolve(cols)
    assert resolved["Item Code"] == "sku"
    assert resolved["Available"] == "quantity"
    assert resolved["Vendor"] == "supplier"


def test_auto_select_supplier_a() -> None:
    cols = ["SKU", "Product Name", "Category", "Unit Price", "Currency", "Qty", "Supplier", "Description"]
    mapping = select_mapping(cols, DEFAULT_MAPPINGS)
    assert mapping.resolve(cols)["SKU"] == "sku"


def test_auto_select_supplier_b() -> None:
    cols = ["Item Code", "Item Name", "Product Type", "Price", "Currency Code", "Available", "Vendor", "Details"]
    mapping = select_mapping(cols, DEFAULT_MAPPINGS)
    assert mapping.resolve(cols)["Item Code"] == "sku"


def test_no_matching_mapping() -> None:
    with pytest.raises(MappingError, match="No mapping matched"):
        select_mapping(["foo", "bar"], DEFAULT_MAPPINGS)


def test_apply_mapping_renames_columns() -> None:
    df = pd.DataFrame({"Item Code": ["A"], "Item Name": ["B"], "Extra": ["C"]})
    result = apply_mapping(df, SUPPLIER_B_MAPPING)
    assert "sku" in result.columns
    assert "product_name" in result.columns
    assert "Extra" in result.columns  # unmapped kept


def test_case_insensitive_matching() -> None:
    cols = ["sku", "product name", "category", "unit price", "currency", "qty", "supplier", "description"]
    mapping = select_mapping(cols, DEFAULT_MAPPINGS)
    resolved = mapping.resolve(cols)
    assert len(resolved) == 8

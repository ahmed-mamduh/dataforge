"""Tests for custom column mapping configuration loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dataforge.config import (
    CANONICAL_FIELDS,
    MappingConfigError,
    PipelineConfig,
    load_mapping_config,
)
from dataforge.engine import run_pipeline


@pytest.fixture
def valid_config_path(tmp_path: Path) -> Path:
    config = {
        "mappings": [
            {
                "mapping": {
                    "SKU": "sku",
                    "Product Name": "product_name",
                    "Category": "category",
                    "Unit Price": "price",
                    "Currency": "currency",
                    "Qty": "quantity",
                    "Supplier": "supplier",
                    "Description": "description",
                }
            }
        ]
    }
    p = tmp_path / "mapping.json"
    p.write_text(json.dumps(config), encoding="utf-8")
    return p


@pytest.fixture
def multi_mapping_config(tmp_path: Path) -> Path:
    config = {
        "mappings": [
            {
                "mapping": {
                    "SKU": "sku",
                    "Product Name": "product_name",
                    "Category": "category",
                    "Unit Price": "price",
                    "Currency": "currency",
                    "Qty": "quantity",
                    "Supplier": "supplier",
                    "Description": "description",
                }
            },
            {
                "mapping": {
                    "Item Code": "sku",
                    "Item Name": "product_name",
                    "Product Type": "category",
                    "Price": "price",
                    "Currency Code": "currency",
                    "Available": "quantity",
                    "Vendor": "supplier",
                    "Details": "description",
                }
            },
        ]
    }
    p = tmp_path / "multi_mapping.json"
    p.write_text(json.dumps(config), encoding="utf-8")
    return p


class TestLoadMappingConfig:
    def test_loads_valid_config(self, valid_config_path: Path) -> None:
        mappings = load_mapping_config(valid_config_path)
        assert len(mappings) == 1
        assert mappings[0].mapping["SKU"] == "sku"

    def test_loads_multiple_mappings(self, multi_mapping_config: Path) -> None:
        mappings = load_mapping_config(multi_mapping_config)
        assert len(mappings) == 2

    def test_file_not_found(self) -> None:
        with pytest.raises(MappingConfigError, match="not found"):
            load_mapping_config(Path("nonexistent.json"))

    def test_invalid_json(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(MappingConfigError, match="Invalid JSON"):
            load_mapping_config(p)

    def test_missing_mappings_key(self, tmp_path: Path) -> None:
        p = tmp_path / "no_key.json"
        p.write_text('{"data": []}', encoding="utf-8")
        with pytest.raises(MappingConfigError, match="'mappings' key"):
            load_mapping_config(p)

    def test_empty_mappings_list(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.json"
        p.write_text('{"mappings": []}', encoding="utf-8")
        with pytest.raises(MappingConfigError, match="non-empty"):
            load_mapping_config(p)

    def test_entry_missing_mapping_key(self, tmp_path: Path) -> None:
        p = tmp_path / "bad_entry.json"
        p.write_text('{"mappings": [{"name": "test"}]}', encoding="utf-8")
        with pytest.raises(MappingConfigError, match="'mapping' key"):
            load_mapping_config(p)

    def test_unknown_canonical_field(self, tmp_path: Path) -> None:
        config = {
            "mappings": [{"mapping": {"Col": "nonexistent_field"}}]
        }
        p = tmp_path / "unknown.json"
        p.write_text(json.dumps(config), encoding="utf-8")
        with pytest.raises(MappingConfigError, match="unknown canonical field"):
            load_mapping_config(p)

    def test_duplicate_target_field(self, tmp_path: Path) -> None:
        config = {
            "mappings": [
                {
                    "mapping": {
                        "Col A": "sku",
                        "Col B": "sku",
                    }
                }
            ]
        }
        p = tmp_path / "dup.json"
        p.write_text(json.dumps(config), encoding="utf-8")
        with pytest.raises(MappingConfigError, match="duplicate target"):
            load_mapping_config(p)

    def test_empty_mapping_object(self, tmp_path: Path) -> None:
        config = {"mappings": [{"mapping": {}}]}
        p = tmp_path / "empty_map.json"
        p.write_text(json.dumps(config), encoding="utf-8")
        with pytest.raises(MappingConfigError, match="non-empty"):
            load_mapping_config(p)


class TestCustomMappingPipeline:
    def test_cli_with_custom_mapping(
        self, valid_config_path: Path, supplier_a_path: Path, tmp_output: Path
    ) -> None:
        mappings = load_mapping_config(valid_config_path)
        config = PipelineConfig(
            input_files=[supplier_a_path],
            output_dir=tmp_output,
            column_mappings=mappings,
        )
        result = run_pipeline(config)
        assert result.stats["input_rows"] == 41
        assert result.stats["accepted"] + result.stats["rejected"] == 41

    def test_multi_mapping_both_suppliers(
        self,
        multi_mapping_config: Path,
        supplier_a_path: Path,
        supplier_b_path: Path,
        tmp_output: Path,
    ) -> None:
        mappings = load_mapping_config(multi_mapping_config)
        config = PipelineConfig(
            input_files=[supplier_a_path, supplier_b_path],
            output_dir=tmp_output,
            column_mappings=mappings,
        )
        result = run_pipeline(config)
        assert result.stats["input_rows"] == 83
        assert result.stats["accepted"] + result.stats["rejected"] == 83

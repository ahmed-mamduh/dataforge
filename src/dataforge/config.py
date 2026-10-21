"""Configuration models for the DataForge pipeline."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ColumnMapping(BaseModel):
    """Maps source column names (lowercased) to canonical field names."""

    mapping: dict[str, str]

    def resolve(self, source_columns: list[str]) -> dict[str, str]:
        """Return {source_col: canonical_col} for columns that match."""
        lookup = {k.strip().lower(): v for k, v in self.mapping.items()}
        result: dict[str, str] = {}
        for col in source_columns:
            canonical = lookup.get(col.strip().lower())
            if canonical:
                result[col] = canonical
        return result

    def match_score(self, source_columns: list[str]) -> int:
        """Count how many source columns this mapping recognizes."""
        return len(self.resolve(source_columns))


CANONICAL_FIELDS = [
    "sku",
    "product_name",
    "category",
    "price",
    "currency",
    "quantity",
    "supplier",
    "description",
]

SUPPLIER_A_MAPPING = ColumnMapping(
    mapping={
        "SKU": "sku",
        "Product Name": "product_name",
        "Category": "category",
        "Unit Price": "price",
        "Currency": "currency",
        "Qty": "quantity",
        "Supplier": "supplier",
        "Description": "description",
    }
)

SUPPLIER_B_MAPPING = ColumnMapping(
    mapping={
        "Item Code": "sku",
        "Item Name": "product_name",
        "Product Type": "category",
        "Price": "price",
        "Currency Code": "currency",
        "Available": "quantity",
        "Vendor": "supplier",
        "Details": "description",
    }
)

DEFAULT_MAPPINGS = [SUPPLIER_A_MAPPING, SUPPLIER_B_MAPPING]


class MappingConfigError(Exception):
    pass


def load_mapping_config(path: Path) -> list[ColumnMapping]:
    """Load column mappings from a JSON file.

    Expected format:
    {
      "mappings": [
        {
          "mapping": {
            "Source Column": "canonical_field",
            ...
          }
        }
      ]
    }
    """
    path = Path(path)
    if not path.exists():
        raise MappingConfigError(f"Mapping config file not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise MappingConfigError(f"Invalid JSON in mapping config: {e}") from e

    if not isinstance(data, dict) or "mappings" not in data:
        raise MappingConfigError(
            "Mapping config must be a JSON object with a 'mappings' key"
        )

    mappings_raw = data["mappings"]
    if not isinstance(mappings_raw, list) or len(mappings_raw) == 0:
        raise MappingConfigError("'mappings' must be a non-empty list")

    result: list[ColumnMapping] = []
    for i, entry in enumerate(mappings_raw):
        if not isinstance(entry, dict) or "mapping" not in entry:
            raise MappingConfigError(
                f"mappings[{i}] must be an object with a 'mapping' key"
            )

        raw_map = entry["mapping"]
        if not isinstance(raw_map, dict) or len(raw_map) == 0:
            raise MappingConfigError(f"mappings[{i}].mapping must be a non-empty object")

        targets = list(raw_map.values())
        for target in targets:
            if target not in CANONICAL_FIELDS:
                raise MappingConfigError(
                    f"mappings[{i}]: unknown canonical field '{target}'. "
                    f"Allowed: {CANONICAL_FIELDS}"
                )

        if len(set(targets)) != len(targets):
            seen: set[str] = set()
            for t in targets:
                if t in seen:
                    raise MappingConfigError(
                        f"mappings[{i}]: duplicate target field '{t}'"
                    )
                seen.add(t)

        result.append(ColumnMapping(mapping=raw_map))

    return result


class ValidationConfig(BaseModel):
    """Rules for validating cleaned records."""

    required_fields: list[str] = Field(default=["sku", "product_name"])
    allowed_currencies: list[str] = Field(default=["USD", "EUR", "GBP", "CAD", "AUD", "JPY"])
    min_price: Decimal = Field(default=Decimal("0"))
    min_quantity: int = Field(default=0)


class DeduplicationConfig(BaseModel):
    """Rules for duplicate detection."""

    key_fields: list[str] = Field(default=["sku", "supplier"])
    keep: str = Field(default="first")
    skip_if_key_missing: bool = Field(default=True)


class PipelineConfig(BaseModel):
    """Top-level configuration for a cleaning run."""

    input_files: list[Path]
    output_dir: Path = Field(default=Path("output"))
    column_mappings: list[ColumnMapping] = Field(default_factory=lambda: list(DEFAULT_MAPPINGS))
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)

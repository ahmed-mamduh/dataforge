"""End-to-end pipeline tests using the real sample data."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from dataforge.config import PipelineConfig
from dataforge.engine import run_pipeline


def test_full_pipeline_both_suppliers(
    supplier_a_path: Path,
    supplier_b_path: Path,
    tmp_output: Path,
) -> None:
    config = PipelineConfig(
        input_files=[supplier_a_path, supplier_b_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)

    total_input = result.stats["input_rows"]
    assert total_input == 41 + 42  # supplier_a + supplier_b row counts

    assert result.stats["accepted"] + result.stats["rejected"] == total_input

    assert result.stats["accepted"] > 0
    assert result.stats["rejected"] > 0
    assert result.stats["duplicates"] > 0

    cleaned = pd.read_csv(tmp_output / "cleaned.csv")
    assert "_source_file" not in cleaned.columns
    assert "_source_row" not in cleaned.columns
    assert "_rejection_reasons" not in cleaned.columns
    assert "_original_price" not in cleaned.columns

    rejected = pd.read_csv(tmp_output / "rejected.csv")
    assert "_rejection_reasons" in rejected.columns
    assert "_source_file" in rejected.columns
    assert "_source_row" in rejected.columns

    report_path = tmp_output / "quality-report.json"
    assert report_path.exists()
    with open(report_path) as f:
        report = json.load(f)
    assert report["input_rows"] == total_input
    assert report["accepted"] + report["rejected"] == total_input
    assert "supplier_a.csv" in report["per_file"]
    assert "supplier_b.csv" in report["per_file"]


def test_supplier_a_only(supplier_a_path: Path, tmp_output: Path) -> None:
    config = PipelineConfig(
        input_files=[supplier_a_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)
    assert result.stats["input_rows"] == 41
    assert result.stats["accepted"] + result.stats["rejected"] == 41


def test_supplier_b_only(supplier_b_path: Path, tmp_output: Path) -> None:
    config = PipelineConfig(
        input_files=[supplier_b_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)
    assert result.stats["input_rows"] == 42
    assert result.stats["accepted"] + result.stats["rejected"] == 42


def test_bad_price_rejected(supplier_a_path: Path, tmp_output: Path) -> None:
    """SA-0011 has 'bad-price' which must be rejected."""
    config = PipelineConfig(
        input_files=[supplier_a_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)
    rejected_skus = result.rejected_df[
        result.rejected_df["_rejection_reasons"].str.contains("invalid_price", na=False)
    ]
    assert len(rejected_skus) > 0


def test_negative_price_rejected(supplier_a_path: Path, tmp_output: Path) -> None:
    """SA-0016 has -9.99 which must be rejected."""
    config = PipelineConfig(
        input_files=[supplier_a_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)
    neg = result.rejected_df[
        result.rejected_df["_rejection_reasons"].str.contains("negative_price", na=False)
    ]
    assert len(neg) > 0


def test_missing_sku_rejected(supplier_a_path: Path, tmp_output: Path) -> None:
    """Row 23 in supplier_a has empty SKU."""
    config = PipelineConfig(
        input_files=[supplier_a_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)
    missing = result.rejected_df[
        result.rejected_df["_rejection_reasons"].str.contains("missing_required:sku", na=False)
    ]
    assert len(missing) > 0


def test_duplicate_detected(supplier_a_path: Path, tmp_output: Path) -> None:
    """SA-0007 appears twice in supplier_a."""
    config = PipelineConfig(
        input_files=[supplier_a_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)
    assert result.stats["duplicates"] >= 1


def test_na_price_rejected(supplier_b_path: Path, tmp_output: Path) -> None:
    """SB-0033 has N/A price."""
    config = PipelineConfig(
        input_files=[supplier_b_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)
    na_price = result.rejected_df[
        result.rejected_df["_rejection_reasons"].str.contains("invalid_price", na=False)
    ]
    assert len(na_price) > 0


def test_invalid_quantity_rejected(supplier_b_path: Path, tmp_output: Path) -> None:
    """SB-0036 has 'not-known' quantity."""
    config = PipelineConfig(
        input_files=[supplier_b_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)
    bad_qty = result.rejected_df[
        result.rejected_df["_rejection_reasons"].str.contains("invalid_quantity", na=False)
    ]
    assert len(bad_qty) > 0


def test_mixed_schemas_processed(
    supplier_a_path: Path,
    supplier_b_path: Path,
    tmp_output: Path,
) -> None:
    """Both files have different headers but produce the same canonical columns."""
    config = PipelineConfig(
        input_files=[supplier_a_path, supplier_b_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)
    cleaned = pd.read_csv(tmp_output / "cleaned.csv")
    assert "sku" in cleaned.columns
    assert "product_name" in cleaned.columns
    assert "price" in cleaned.columns


def test_zero_quantity_accepted(supplier_a_path: Path, tmp_output: Path) -> None:
    """SA-0015 has qty=0 which should be valid."""
    config = PipelineConfig(
        input_files=[supplier_a_path],
        output_dir=tmp_output,
    )
    result = run_pipeline(config)
    valid_skus = list(result.valid_df["sku"])
    assert "SA-0015" in valid_skus

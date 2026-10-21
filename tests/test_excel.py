"""Tests for real Excel (.xlsx) ingestion and full pipeline processing."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from dataforge.config import PipelineConfig
from dataforge.engine import run_pipeline
from dataforge.ingestion import read_file

FIXTURE_DIR = Path(__file__).parent / "fixtures"
EXCEL_FIXTURE = FIXTURE_DIR / "test_workbook.xlsx"


@pytest.fixture(autouse=True)
def _ensure_fixture() -> None:
    """Generate the Excel fixture if it doesn't exist."""
    if not EXCEL_FIXTURE.exists():
        from tests.fixtures.generate_excel_fixture import generate
        EXCEL_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        generate(EXCEL_FIXTURE)


class TestExcelIngestion:
    def test_reads_xlsx_file(self) -> None:
        df = read_file(EXCEL_FIXTURE)
        assert len(df) == 12

    def test_source_tracking(self) -> None:
        df = read_file(EXCEL_FIXTURE)
        assert df["_source_file"].iloc[0] == "test_workbook.xlsx"
        assert df["_source_row"].iloc[0] == 2

    def test_leading_zeros_preserved(self) -> None:
        df = read_file(EXCEL_FIXTURE)
        skus = list(df["SKU"])
        assert "0001" in skus
        assert "0010" in skus

    def test_all_columns_are_strings(self) -> None:
        df = read_file(EXCEL_FIXTURE)
        for col in df.columns:
            if col.startswith("_"):
                continue
            assert pd.api.types.is_string_dtype(df[col]), (
                f"Column {col} should be string dtype, got {df[col].dtype}"
            )

    def test_none_cells_read_as_empty(self) -> None:
        """openpyxl reads None cells; with keep_default_na=False they should be empty strings."""
        df = read_file(EXCEL_FIXTURE)
        row_with_none_sku = df[df["Product Name"] == "Orphan Product"]
        assert len(row_with_none_sku) == 1
        sku_val = row_with_none_sku["SKU"].iloc[0]
        assert sku_val == "" or sku_val == "None"


class TestExcelPipeline:
    def test_full_pipeline(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        result = run_pipeline(config)

        assert result.stats["input_rows"] == 12
        assert result.stats["accepted"] + result.stats["rejected"] == 12
        assert result.stats["accepted"] > 0
        assert result.stats["rejected"] > 0
        assert result.stats["duplicates"] >= 1

    def test_leading_zero_sku_preserved_in_output(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        result = run_pipeline(config)
        valid_skus = list(result.valid_df["sku"])
        assert "0010" in valid_skus

    def test_invalid_price_text_rejected(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        result = run_pipeline(config)
        bad_price = result.rejected_df[
            result.rejected_df["_rejection_reasons"].str.contains("invalid_price", na=False)
        ]
        assert len(bad_price) >= 1

    def test_negative_price_rejected(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        result = run_pipeline(config)
        neg = result.rejected_df[
            result.rejected_df["_rejection_reasons"].str.contains("negative_price", na=False)
        ]
        assert len(neg) >= 1

    def test_negative_quantity_rejected(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        result = run_pipeline(config)
        neg_qty = result.rejected_df[
            result.rejected_df["_rejection_reasons"].str.contains("negative_quantity", na=False)
        ]
        assert len(neg_qty) >= 1

    def test_zero_quantity_accepted(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        result = run_pipeline(config)
        assert "0005" in list(result.valid_df["sku"])

    def test_blank_product_name_rejected(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        result = run_pipeline(config)
        blank_name = result.rejected_df[
            result.rejected_df["_rejection_reasons"].str.contains("missing_required:product_name", na=False)
        ]
        assert len(blank_name) >= 1

    def test_duplicate_detected(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        result = run_pipeline(config)
        dups = result.rejected_df[
            result.rejected_df["_rejection_reasons"].str.contains("duplicate", na=False)
        ]
        assert len(dups) >= 1

    def test_whitespace_trimmed(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        result = run_pipeline(config)
        padded = result.valid_df[result.valid_df["sku"] == "0009"]
        assert len(padded) == 1
        assert padded["product_name"].iloc[0] == "Padded Name"

    def test_output_files_created(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        run_pipeline(config)
        assert (tmp_output / "cleaned.csv").exists()
        assert (tmp_output / "rejected.csv").exists()
        assert (tmp_output / "quality-report.json").exists()

    def test_quality_report_structure(self, tmp_output: Path) -> None:
        config = PipelineConfig(
            input_files=[EXCEL_FIXTURE],
            output_dir=tmp_output,
        )
        run_pipeline(config)
        with open(tmp_output / "quality-report.json") as f:
            report = json.load(f)
        assert report["input_rows"] == 12
        assert report["accepted"] + report["rejected"] == 12
        assert "test_workbook.xlsx" in report["per_file"]

"""Output generation — cleaned CSV, rejected CSV, quality report JSON."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pandas as pd

from dataforge.config import CANONICAL_FIELDS


def _format_quantity_col(df: pd.DataFrame) -> None:
    """Convert quantity column values to int where possible, in-place."""
    if "quantity" not in df.columns:
        return
    vals = []
    for v in df["quantity"]:
        if pd.notna(v) and isinstance(v, (int, float)):
            try:
                iv = int(v)
                vals.append(iv if v == iv else v)
            except (ValueError, OverflowError):
                vals.append(v)
        else:
            vals.append(v)
    df["quantity"] = pd.array(vals, dtype=object)


class _DecimalEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


def write_outputs(
    valid_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
    stats: dict,
    output_dir: Path,
) -> dict[str, Path]:
    """Write cleaned.csv, rejected.csv, and quality-report.json."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_path = output_dir / "cleaned.csv"
    rejected_path = output_dir / "rejected.csv"
    report_path = output_dir / "quality-report.json"

    clean_cols = [c for c in CANONICAL_FIELDS if c in valid_df.columns]
    out_valid = valid_df[clean_cols].copy()
    _format_quantity_col(out_valid)
    out_valid.to_csv(cleaned_path, index=False)

    reject_cols = (
        [c for c in CANONICAL_FIELDS if c in rejected_df.columns]
        + ["_rejection_reasons", "_source_file", "_source_row"]
    )
    reject_cols = [c for c in reject_cols if c in rejected_df.columns]
    out_rejected = rejected_df[reject_cols].copy()
    _format_quantity_col(out_rejected)
    out_rejected.to_csv(rejected_path, index=False)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, cls=_DecimalEncoder)

    return {
        "cleaned": cleaned_path,
        "rejected": rejected_path,
        "report": report_path,
    }

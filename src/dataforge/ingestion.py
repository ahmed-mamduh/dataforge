"""File ingestion — CSV and Excel reading with source tracking."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}
CSV_ENCODINGS = ["utf-8-sig", "utf-8", "latin-1"]


class IngestionError(Exception):
    pass


def read_file(path: Path) -> pd.DataFrame:
    """Read a CSV or Excel file into a DataFrame with source tracking columns.

    All columns are read as strings to preserve leading zeros and avoid
    silent type coercion.
    """
    path = Path(path)
    if not path.exists():
        raise IngestionError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise IngestionError(f"Unsupported file type: {ext}")

    if ext == ".csv":
        df = _read_csv(path)
    elif ext == ".xlsx":
        df = _read_excel(path)
    else:
        raise IngestionError(f"Unsupported file type: {ext}")

    df["_source_file"] = path.name
    df["_source_row"] = range(2, len(df) + 2)  # 1-based, header is row 1
    return df


def _read_csv(path: Path) -> pd.DataFrame:
    """Try multiple encodings for CSV files."""
    for encoding in CSV_ENCODINGS:
        try:
            return pd.read_csv(path, dtype=str, encoding=encoding, keep_default_na=False)
        except UnicodeDecodeError:
            continue
    raise IngestionError(f"Could not decode CSV with supported encodings: {path}")


def _read_excel(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, dtype=str, keep_default_na=False, engine="openpyxl")

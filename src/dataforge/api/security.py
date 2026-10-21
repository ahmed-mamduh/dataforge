"""Upload validation and CSV safety utilities."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_FILES_PER_REQUEST = 3

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def validate_extension(filename: str) -> str | None:
    """Return None if valid, error message if not."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    return None


def validate_file_size(size: int, filename: str) -> str | None:
    """Return None if valid, error message if not."""
    if size > MAX_FILE_SIZE:
        mb = size / (1024 * 1024)
        return f"File '{filename}' is {mb:.1f} MB, exceeds 10 MB limit"
    return None


def safe_filename(filename: str) -> str:
    """Sanitize a filename: strip path components, replace unsafe chars."""
    name = Path(filename).name
    name = re.sub(r"[^\w.\-]", "_", name)
    if not name or name.startswith("."):
        name = "upload" + name
    return name


def sanitize_csv_value(value: str) -> str:
    """Prevent spreadsheet formula injection in CSV cell values.

    If a cell starts with a formula-triggering character, prefix with a
    single quote so spreadsheet applications treat it as text.
    """
    if isinstance(value, str) and value and value[0] in FORMULA_PREFIXES:
        return "'" + value
    return value


def sanitize_csv_file(input_path: Path, output_path: Path) -> None:
    """Rewrite a CSV file with formula-injection protection."""
    with open(input_path, "r", encoding="utf-8", newline="") as fin:
        reader = csv.reader(fin)
        rows = list(reader)

    with open(output_path, "w", encoding="utf-8", newline="") as fout:
        writer = csv.writer(fout)
        for i, row in enumerate(rows):
            if i == 0:
                writer.writerow(row)
            else:
                writer.writerow([sanitize_csv_value(cell) for cell in row])

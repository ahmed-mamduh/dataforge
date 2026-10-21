"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "sample_data"
SUPPLIER_A = SAMPLE_DATA_DIR / "supplier_a.csv"
SUPPLIER_B = SAMPLE_DATA_DIR / "supplier_b.csv"


@pytest.fixture
def supplier_a_path() -> Path:
    return SUPPLIER_A


@pytest.fixture
def supplier_b_path() -> Path:
    return SUPPLIER_B


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    out = tmp_path / "output"
    out.mkdir()
    return out

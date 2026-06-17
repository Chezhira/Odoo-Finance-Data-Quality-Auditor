from __future__ import annotations

from pathlib import Path

import pytest

from odoo_finance_data_auditor.loader import load_csv_exports


@pytest.fixture
def sample_data_dir() -> Path:
    return Path("data/sample")


@pytest.fixture
def sample_data(sample_data_dir):
    data = load_csv_exports(sample_data_dir)
    return {name: frame.copy() for name, frame in data.items()}

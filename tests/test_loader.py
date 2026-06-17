from __future__ import annotations

import pandas as pd
import pytest

from odoo_finance_data_auditor.loader import SchemaValidationError, load_csv_exports, validate_schemas


def test_load_sample_csv_exports(sample_data_dir):
    data = load_csv_exports(sample_data_dir)

    assert set(data) == {"accounts", "journal_entries", "vendor_bills", "bank_statement_lines"}


def test_validate_schemas_reports_missing_columns(sample_data):
    broken = dict(sample_data)
    broken["vendor_bills"] = pd.DataFrame({"bill_id": ["VB001"]})

    with pytest.raises(SchemaValidationError, match="vendor_bills.csv missing required columns"):
        validate_schemas(broken)

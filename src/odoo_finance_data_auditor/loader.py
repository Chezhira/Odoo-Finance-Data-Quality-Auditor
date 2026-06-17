from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS: dict[str, set[str]] = {
    "accounts": {
        "account_id",
        "code",
        "name",
        "type",
        "active",
        "is_suspense",
        "is_deprecated",
        "requires_analytic_tag",
    },
    "journal_entries": {
        "entry_id",
        "line_id",
        "date",
        "state",
        "journal_type",
        "account_id",
        "partner_id",
        "partner_name",
        "reference",
        "debit",
        "credit",
        "analytic_tags",
        "is_foreign_currency",
        "currency",
        "fx_rate",
    },
    "vendor_bills": {
        "bill_id",
        "vendor_id",
        "vendor_name",
        "bill_date",
        "state",
        "reference",
        "total_amount",
        "tax_evidence_document",
        "tax_registration",
    },
    "customer_invoices": {
        "invoice_id",
        "customer_id",
        "customer_name",
        "invoice_date",
        "state",
        "reference",
        "total_amount",
        "tax_code",
    },
    "bank_statement_lines": {
        "line_id",
        "date",
        "bank_account",
        "description",
        "amount",
        "is_reconciled",
    },
    "inventory_valuation": {
        "valuation_id",
        "date",
        "product_id",
        "product_name",
        "quantity",
        "value",
        "source_document",
    },
}


class SchemaValidationError(ValueError):
    """Raised when a CSV export is missing required columns."""


def load_csv_exports(data_dir: Path) -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for name in REQUIRED_COLUMNS:
        path = data_dir / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Required CSV not found: {path}")
        data[name] = pd.read_csv(path)

    validate_schemas(data)
    return data


def validate_schemas(data: dict[str, pd.DataFrame]) -> None:
    for name, required_columns in REQUIRED_COLUMNS.items():
        if name not in data:
            raise SchemaValidationError(f"Missing dataset: {name}")

        missing = sorted(required_columns - set(data[name].columns))
        if missing:
            missing_list = ", ".join(missing)
            raise SchemaValidationError(f"{name}.csv missing required columns: {missing_list}")

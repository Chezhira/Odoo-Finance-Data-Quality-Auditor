from __future__ import annotations

from datetime import date

import pandas as pd

from odoo_finance_data_auditor.config import AuditConfig
from odoo_finance_data_auditor.exceptions import AuditException


def suspense_after_close_date(data: dict[str, pd.DataFrame], config: AuditConfig) -> list[AuditException]:
    accounts = data["accounts"].copy()
    entries = data["journal_entries"].copy()

    suspense_account_ids = set(accounts.loc[_as_bool(accounts["is_suspense"]), "account_id"].astype(str))
    entries["date"] = pd.to_datetime(entries["date"]).dt.date
    entries["account_id"] = entries["account_id"].astype(str)

    matches = entries[
        (entries["state"] == "posted")
        & (entries["date"] > config.close_date)
        & (entries["account_id"].isin(suspense_account_ids))
    ]

    return [
        AuditException(
            rule_id="FIN-001",
            rule_name="Posted suspense entries after close date",
            severity="high",
            source="journal_entries",
            record_id=str(row.line_id),
            message=f"Posted suspense line {row.line_id} is dated after close date {config.close_date.isoformat()}.",
            amount=float(row.debit) - float(row.credit),
            date=row.date,
            metadata={"entry_id": row.entry_id, "account_id": row.account_id, "reference": row.reference},
        )
        for row in matches.itertuples(index=False)
    ]


def duplicate_vendor_bill_references(data: dict[str, pd.DataFrame], config: AuditConfig) -> list[AuditException]:
    del config
    bills = data["vendor_bills"].copy()
    posted = bills[(bills["state"] == "posted") & bills["reference"].notna()].copy()
    posted["reference_key"] = posted["reference"].astype(str).str.strip().str.lower()

    duplicates = posted[posted.duplicated(["vendor_id", "reference_key"], keep=False)]

    return [
        AuditException(
            rule_id="FIN-002",
            rule_name="Duplicate vendor bill reference",
            severity="high",
            source="vendor_bills",
            record_id=str(row.bill_id),
            message=f"Vendor {row.vendor_name} has duplicate posted bill reference {row.reference}.",
            amount=float(row.total_amount),
            date=_parse_date(row.bill_date),
            metadata={"vendor_id": row.vendor_id, "reference": row.reference},
        )
        for row in duplicates.sort_values(["vendor_id", "reference_key", "bill_id"]).itertuples(index=False)
    ]


def unreconciled_old_bank_lines(data: dict[str, pd.DataFrame], config: AuditConfig) -> list[AuditException]:
    lines = data["bank_statement_lines"].copy()
    lines["date"] = pd.to_datetime(lines["date"]).dt.date
    cutoff = config.as_of_date.toordinal() - config.bank_line_age_days

    matches = lines[
        (~_as_bool(lines["is_reconciled"]))
        & (lines["date"].map(date.toordinal) < cutoff)
    ]

    return [
        AuditException(
            rule_id="FIN-003",
            rule_name="Unreconciled old bank statement line",
            severity="medium",
            source="bank_statement_lines",
            record_id=str(row.line_id),
            message=f"Bank line {row.line_id} is unreconciled and older than {config.bank_line_age_days} days.",
            amount=float(row.amount),
            date=row.date,
            metadata={"bank_account": row.bank_account, "description": row.description},
        )
        for row in matches.itertuples(index=False)
    ]


def customer_invoices_missing_tax_codes(data: dict[str, pd.DataFrame], config: AuditConfig) -> list[AuditException]:
    del config
    invoices = data["customer_invoices"].copy()
    matches = invoices[(invoices["state"] == "posted") & _is_blank(invoices["tax_code"])]

    return [
        AuditException(
            rule_id="FIN-004",
            rule_name="Customer invoice missing tax code",
            severity="high",
            source="customer_invoices",
            record_id=str(row.invoice_id),
            message=f"Posted customer invoice {row.invoice_id} is missing a tax code.",
            amount=float(row.total_amount),
            date=_parse_date(row.invoice_date),
            metadata={"customer_id": row.customer_id, "reference": row.reference},
        )
        for row in matches.itertuples(index=False)
    ]


def vendor_bills_missing_tax_evidence(data: dict[str, pd.DataFrame], config: AuditConfig) -> list[AuditException]:
    del config
    bills = data["vendor_bills"].copy()
    matches = bills[
        (bills["state"] == "posted")
        & (_is_blank(bills["tax_evidence_document"]) | _is_blank(bills["tax_registration"]))
    ]

    return [
        AuditException(
            rule_id="FIN-005",
            rule_name="Vendor bill missing tax evidence",
            severity="high",
            source="vendor_bills",
            record_id=str(row.bill_id),
            message=f"Posted vendor bill {row.bill_id} is missing tax evidence fields.",
            amount=float(row.total_amount),
            date=_parse_date(row.bill_date),
            metadata={
                "vendor_id": row.vendor_id,
                "reference": row.reference,
                "missing_fields": _missing_fields(row, ["tax_evidence_document", "tax_registration"]),
            },
        )
        for row in matches.itertuples(index=False)
    ]


def negative_inventory_valuation_records(data: dict[str, pd.DataFrame], config: AuditConfig) -> list[AuditException]:
    del config
    valuations = data["inventory_valuation"].copy()
    matches = valuations[(valuations["quantity"].astype(float) < 0) | (valuations["value"].astype(float) < 0)]

    return [
        AuditException(
            rule_id="FIN-006",
            rule_name="Negative inventory valuation quantity or value",
            severity="high",
            source="inventory_valuation",
            record_id=str(row.valuation_id),
            message=f"Inventory valuation {row.valuation_id} has a negative quantity or value.",
            amount=float(row.value),
            date=_parse_date(row.date),
            metadata={
                "product_id": row.product_id,
                "product_name": row.product_name,
                "quantity": float(row.quantity),
                "source_document": row.source_document,
            },
        )
        for row in matches.itertuples(index=False)
    ]


def posted_entries_to_inactive_or_deprecated_accounts(
    data: dict[str, pd.DataFrame], config: AuditConfig
) -> list[AuditException]:
    del config
    accounts = data["accounts"].copy()
    entries = data["journal_entries"].copy()

    restricted_accounts = accounts[_as_bool(accounts["is_deprecated"]) | (~_as_bool(accounts["active"]))].copy()
    restricted_accounts["account_id"] = restricted_accounts["account_id"].astype(str)
    entries["account_id"] = entries["account_id"].astype(str)

    matches = entries[entries["state"].eq("posted")].merge(
        restricted_accounts[["account_id", "code", "name", "active", "is_deprecated"]],
        on="account_id",
        how="inner",
    )

    return [
        AuditException(
            rule_id="FIN-007",
            rule_name="Posted journal entry to inactive or deprecated account",
            severity="high",
            source="journal_entries",
            record_id=str(row.line_id),
            message=f"Posted journal line {row.line_id} uses inactive or deprecated account {row.code}.",
            amount=float(row.debit) - float(row.credit),
            date=_parse_date(row.date),
            metadata={
                "entry_id": row.entry_id,
                "account_id": row.account_id,
                "account_name": row.name,
                "active": row.active,
                "is_deprecated": row.is_deprecated,
            },
        )
        for row in matches.itertuples(index=False)
    ]


def run_all_rules(data: dict[str, pd.DataFrame], config: AuditConfig) -> list[AuditException]:
    exceptions: list[AuditException] = []
    for rule in (
        suspense_after_close_date,
        duplicate_vendor_bill_references,
        unreconciled_old_bank_lines,
        customer_invoices_missing_tax_codes,
        vendor_bills_missing_tax_evidence,
        negative_inventory_valuation_records,
        posted_entries_to_inactive_or_deprecated_accounts,
    ):
        exceptions.extend(rule(data, config))
    return exceptions


def _as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


def _is_blank(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype(str).str.strip().eq("")


def _missing_fields(row: object, field_names: list[str]) -> list[str]:
    return [field_name for field_name in field_names if pd.isna(getattr(row, field_name)) or str(getattr(row, field_name)).strip() == ""]


def _parse_date(value: object) -> date:
    return pd.to_datetime(value).date()

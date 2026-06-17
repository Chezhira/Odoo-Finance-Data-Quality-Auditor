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


def run_all_rules(data: dict[str, pd.DataFrame], config: AuditConfig) -> list[AuditException]:
    exceptions: list[AuditException] = []
    for rule in (
        suspense_after_close_date,
        duplicate_vendor_bill_references,
        unreconciled_old_bank_lines,
    ):
        exceptions.extend(rule(data, config))
    return exceptions


def _as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


def _parse_date(value: object) -> date:
    return pd.to_datetime(value).date()

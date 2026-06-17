from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

import pandas as pd

from odoo_finance_data_auditor.config import AuditConfig
from odoo_finance_data_auditor.exceptions import AuditException


RuleFunction = Callable[[dict[str, pd.DataFrame], AuditConfig], list[AuditException]]


@dataclass(frozen=True)
class CheckDefinition:
    check_id: str
    name: str
    description: str
    risk_level: str
    source_model: str
    recommended_action: str
    run: RuleFunction


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
        _build_exception(
            check_id="FIN-001",
            entity="journal_entry_line",
            record_id=str(row.line_id),
            issue_type="Posted suspense after close date",
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
        _build_exception(
            check_id="FIN-002",
            entity="vendor_bill",
            record_id=str(row.bill_id),
            issue_type="Duplicate vendor bill reference",
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
        _build_exception(
            check_id="FIN-003",
            entity="bank_statement_line",
            record_id=str(row.line_id),
            issue_type="Unreconciled old bank statement line",
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
        _build_exception(
            check_id="FIN-004",
            entity="customer_invoice",
            record_id=str(row.invoice_id),
            issue_type="Missing customer invoice tax code",
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
        _build_exception(
            check_id="FIN-005",
            entity="vendor_bill",
            record_id=str(row.bill_id),
            issue_type="Missing vendor bill tax evidence",
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
        _build_exception(
            check_id="FIN-006",
            entity="inventory_valuation",
            record_id=str(row.valuation_id),
            issue_type="Negative inventory quantity or value",
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
        _build_exception(
            check_id="FIN-007",
            entity="journal_entry_line",
            record_id=str(row.line_id),
            issue_type="Posting to inactive or deprecated account",
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
    for check in CHECK_REGISTRY:
        exceptions.extend(check.run(data, config))
    return exceptions


CHECK_REGISTRY: tuple[CheckDefinition, ...] = (
    CheckDefinition(
        check_id="FIN-001",
        name="Posted suspense entries after close date",
        description="Finds posted journal lines using suspense accounts after the configured finance close date.",
        risk_level="high",
        source_model="journal_entries",
        recommended_action="Review the journal entry, clear the suspense balance, or reverse and repost into the correct period/account.",
        run=suspense_after_close_date,
    ),
    CheckDefinition(
        check_id="FIN-002",
        name="Duplicate vendor bill references",
        description="Finds posted vendor bills with the same supplier invoice reference for the same vendor.",
        risk_level="high",
        source_model="vendor_bills",
        recommended_action="Confirm whether the duplicate is valid; cancel, credit, or correct the duplicate bill before payment.",
        run=duplicate_vendor_bill_references,
    ),
    CheckDefinition(
        check_id="FIN-003",
        name="Unreconciled old bank statement lines",
        description="Finds unreconciled bank statement lines older than the configured age threshold.",
        risk_level="medium",
        source_model="bank_statement_lines",
        recommended_action="Investigate the bank line and reconcile, write off, or escalate the open item.",
        run=unreconciled_old_bank_lines,
    ),
    CheckDefinition(
        check_id="FIN-004",
        name="Customer invoices missing tax codes",
        description="Finds posted customer invoices without a tax code.",
        risk_level="high",
        source_model="customer_invoices",
        recommended_action="Add the correct tax code or credit and reissue the invoice if tax treatment is wrong.",
        run=customer_invoices_missing_tax_codes,
    ),
    CheckDefinition(
        check_id="FIN-005",
        name="Vendor bills missing tax evidence",
        description="Finds posted vendor bills missing tax evidence documents or supplier tax registration details.",
        risk_level="high",
        source_model="vendor_bills",
        recommended_action="Request the missing tax evidence and update the bill before reclaiming or reporting tax.",
        run=vendor_bills_missing_tax_evidence,
    ),
    CheckDefinition(
        check_id="FIN-006",
        name="Negative inventory valuation records",
        description="Finds inventory valuation records with negative quantity or negative value.",
        risk_level="high",
        source_model="inventory_valuation",
        recommended_action="Review stock moves and valuation layers, then correct costing or stock adjustments.",
        run=negative_inventory_valuation_records,
    ),
    CheckDefinition(
        check_id="FIN-007",
        name="Posted entries to inactive or deprecated accounts",
        description="Finds posted journal lines using inactive or deprecated accounts.",
        risk_level="high",
        source_model="journal_entries",
        recommended_action="Move the posting to an active account and restrict deprecated accounts from future use.",
        run=posted_entries_to_inactive_or_deprecated_accounts,
    ),
)

CHECKS_BY_ID = {check.check_id: check for check in CHECK_REGISTRY}


def _build_exception(
    check_id: str,
    entity: str,
    record_id: str,
    issue_type: str,
    message: str,
    recommended_action: str | None = None,
    amount: float | None = None,
    date: date | None = None,
    metadata: dict[str, object] | None = None,
) -> AuditException:
    check = CHECKS_BY_ID[check_id]
    return AuditException(
        check_id=check.check_id,
        check_name=check.name,
        risk_level=check.risk_level,
        source_model=check.source_model,
        entity=entity,
        record_id=record_id,
        issue_type=issue_type,
        message=message,
        recommended_action=recommended_action or check.recommended_action,
        amount=amount,
        date=date,
        metadata=metadata,
    )


def _as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


def _is_blank(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype(str).str.strip().eq("")


def _missing_fields(row: object, field_names: list[str]) -> list[str]:
    return [field_name for field_name in field_names if pd.isna(getattr(row, field_name)) or str(getattr(row, field_name)).strip() == ""]


def _parse_date(value: object) -> date:
    return pd.to_datetime(value).date()

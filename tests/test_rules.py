from __future__ import annotations

import pandas as pd

from odoo_finance_data_auditor.config import AuditConfig
from odoo_finance_data_auditor.reporting import export_exception_report
from odoo_finance_data_auditor.rules import (
    CHECK_REGISTRY,
    customer_invoices_missing_tax_codes,
    duplicate_vendor_bill_references,
    fx_entries_missing_currency_or_rate_metadata,
    manual_journals_above_threshold,
    missing_analytic_tags_on_selected_accounts,
    negative_inventory_valuation_records,
    posted_entries_to_inactive_or_deprecated_accounts,
    run_all_rules,
    suspense_after_close_date,
    unreconciled_old_bank_lines,
    vendor_bills_missing_tax_evidence,
)


def test_check_registry_contains_metadata_for_current_rules():
    assert len(CHECK_REGISTRY) == 10
    assert [check.check_id for check in CHECK_REGISTRY] == [
        "FIN-001",
        "FIN-002",
        "FIN-003",
        "FIN-004",
        "FIN-005",
        "FIN-006",
        "FIN-007",
        "FIN-008",
        "FIN-009",
        "FIN-010",
    ]
    assert all(check.name for check in CHECK_REGISTRY)
    assert all(check.description for check in CHECK_REGISTRY)
    assert all(check.risk_level in {"high", "medium", "low"} for check in CHECK_REGISTRY)
    assert all(check.source_model for check in CHECK_REGISTRY)
    assert all(check.recommended_action for check in CHECK_REGISTRY)


def test_suspense_after_close_date_flags_only_posted_late_suspense(sample_data):
    exceptions = suspense_after_close_date(sample_data, AuditConfig())

    assert [exception.record_id for exception in exceptions] == ["JL001"]


def test_suspense_after_close_date_has_negative_path(sample_data):
    sample_data["journal_entries"]["account_id"] = "6000"

    assert suspense_after_close_date(sample_data, AuditConfig()) == []


def test_duplicate_vendor_bill_references_flags_same_vendor_posted_duplicates(sample_data):
    exceptions = duplicate_vendor_bill_references(sample_data, AuditConfig())

    assert [exception.record_id for exception in exceptions] == ["VB001", "VB002"]


def test_duplicate_vendor_bill_references_ignores_unique_refs(sample_data):
    sample_data["vendor_bills"].loc[1, "reference"] = "INV-101"

    assert duplicate_vendor_bill_references(sample_data, AuditConfig()) == []


def test_unreconciled_old_bank_lines_flags_only_old_unreconciled_lines(sample_data):
    exceptions = unreconciled_old_bank_lines(sample_data, AuditConfig())

    assert [exception.record_id for exception in exceptions] == ["BNK001"]


def test_unreconciled_old_bank_lines_has_negative_path(sample_data):
    sample_data["bank_statement_lines"]["is_reconciled"] = "true"

    assert unreconciled_old_bank_lines(sample_data, AuditConfig()) == []


def test_customer_invoices_missing_tax_codes_flags_posted_invoice(sample_data):
    exceptions = customer_invoices_missing_tax_codes(sample_data, AuditConfig())

    assert [exception.record_id for exception in exceptions] == ["CI002"]


def test_customer_invoices_missing_tax_codes_ignores_drafts(sample_data):
    sample_data["customer_invoices"]["tax_code"] = ""
    sample_data["customer_invoices"]["state"] = "draft"

    assert customer_invoices_missing_tax_codes(sample_data, AuditConfig()) == []


def test_vendor_bills_missing_tax_evidence_flags_posted_missing_fields(sample_data):
    exceptions = vendor_bills_missing_tax_evidence(sample_data, AuditConfig())

    assert [exception.record_id for exception in exceptions] == ["VB005", "VB006"]
    assert exceptions[0].metadata["missing_fields"] == ["tax_evidence_document"]
    assert exceptions[1].metadata["missing_fields"] == ["tax_registration"]


def test_vendor_bills_missing_tax_evidence_ignores_complete_records(sample_data):
    sample_data["vendor_bills"]["tax_evidence_document"] = "evidence.pdf"
    sample_data["vendor_bills"]["tax_registration"] = "GB123456789"

    assert vendor_bills_missing_tax_evidence(sample_data, AuditConfig()) == []


def test_negative_inventory_valuation_records_flags_negative_quantity_or_value(sample_data):
    exceptions = negative_inventory_valuation_records(sample_data, AuditConfig())

    assert [exception.record_id for exception in exceptions] == ["IV002", "IV003"]


def test_negative_inventory_valuation_records_has_negative_path(sample_data):
    sample_data["inventory_valuation"]["quantity"] = 1
    sample_data["inventory_valuation"]["value"] = 100

    assert negative_inventory_valuation_records(sample_data, AuditConfig()) == []


def test_posted_entries_to_inactive_or_deprecated_accounts_flags_posted_lines(sample_data):
    exceptions = posted_entries_to_inactive_or_deprecated_accounts(sample_data, AuditConfig())

    assert [exception.record_id for exception in exceptions] == ["JL005"]


def test_posted_entries_to_inactive_or_deprecated_accounts_ignores_active_accounts(sample_data):
    sample_data["accounts"]["active"] = "true"
    sample_data["accounts"]["is_deprecated"] = "false"

    assert posted_entries_to_inactive_or_deprecated_accounts(sample_data, AuditConfig()) == []


def test_missing_analytic_tags_on_selected_accounts_flags_selected_account_lines(sample_data):
    exceptions = missing_analytic_tags_on_selected_accounts(sample_data, AuditConfig())

    assert [exception.record_id for exception in exceptions] == ["JL006"]


def test_missing_analytic_tags_on_selected_accounts_ignores_non_selected_accounts(sample_data):
    sample_data["accounts"]["requires_analytic_tag"] = "false"

    assert missing_analytic_tags_on_selected_accounts(sample_data, AuditConfig()) == []


def test_fx_entries_missing_currency_or_rate_metadata_flags_fx_related_lines(sample_data):
    exceptions = fx_entries_missing_currency_or_rate_metadata(sample_data, AuditConfig())

    assert [exception.record_id for exception in exceptions] == ["JL007"]


def test_fx_entries_missing_currency_or_rate_metadata_ignores_complete_fx_metadata(sample_data):
    sample_data["journal_entries"]["currency"] = "USD"
    sample_data["journal_entries"]["fx_rate"] = "1.25"

    assert fx_entries_missing_currency_or_rate_metadata(sample_data, AuditConfig()) == []


def test_manual_journals_above_threshold_flags_posted_manual_journals(sample_data):
    exceptions = manual_journals_above_threshold(sample_data, AuditConfig())

    assert [exception.record_id for exception in exceptions] == ["JL008"]


def test_manual_journals_above_threshold_uses_configured_threshold(sample_data):
    config = AuditConfig(manual_journal_threshold=20000.0)

    assert manual_journals_above_threshold(sample_data, config) == []


def test_run_all_rules_and_export_report(sample_data, tmp_path):
    exceptions = run_all_rules(sample_data, AuditConfig())
    output_path = tmp_path / "exception_report.xlsx"

    export_exception_report(exceptions, output_path)

    assert len(exceptions) == 13
    assert output_path.exists()
    workbook = pd.ExcelFile(output_path)
    assert workbook.sheet_names == ["Summary", "Exceptions"]


def test_export_report_uses_business_facing_columns(sample_data, tmp_path):
    exceptions = run_all_rules(sample_data, AuditConfig())
    output_path = tmp_path / "exception_report.xlsx"

    export_exception_report(exceptions, output_path)

    summary = pd.read_excel(output_path, sheet_name="Summary")
    exception_rows = pd.read_excel(output_path, sheet_name="Exceptions")

    assert list(summary.columns) == ["risk_level", "issue_type", "exception_count"]
    assert set(summary["risk_level"]) == {"high", "medium"}
    assert exception_rows.columns[:9].tolist() == [
        "check_name",
        "risk_level",
        "entity",
        "source_model",
        "record_id",
        "issue_type",
        "date",
        "amount",
        "recommended_action",
    ]
    assert exception_rows["recommended_action"].notna().all()

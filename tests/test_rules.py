from __future__ import annotations

import pandas as pd

from odoo_finance_data_auditor.config import AuditConfig
from odoo_finance_data_auditor.reporting import export_exception_report
from odoo_finance_data_auditor.rules import (
    duplicate_vendor_bill_references,
    run_all_rules,
    suspense_after_close_date,
    unreconciled_old_bank_lines,
)


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


def test_run_all_rules_and_export_report(sample_data, tmp_path):
    exceptions = run_all_rules(sample_data, AuditConfig())
    output_path = tmp_path / "exception_report.xlsx"

    export_exception_report(exceptions, output_path)

    assert len(exceptions) == 4
    assert output_path.exists()
    workbook = pd.ExcelFile(output_path)
    assert workbook.sheet_names == ["Summary", "Exceptions"]

from __future__ import annotations

from openpyxl import load_workbook

from odoo_finance_data_auditor.config import AuditConfig
from odoo_finance_data_auditor.reporting import export_exception_report
from odoo_finance_data_auditor.rules import run_all_rules


def test_export_report_freezes_headers_and_sets_column_widths(sample_data, tmp_path):
    output_path = tmp_path / "exception_report.xlsx"

    export_exception_report(run_all_rules(sample_data, AuditConfig()), output_path)

    workbook = load_workbook(output_path)
    for sheet_name in ["Summary", "Exceptions"]:
        worksheet = workbook[sheet_name]
        assert worksheet.freeze_panes == "A2"
        assert worksheet["A1"].font.bold
        assert worksheet.column_dimensions["A"].width > 10

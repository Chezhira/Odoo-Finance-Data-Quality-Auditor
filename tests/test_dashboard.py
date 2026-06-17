from __future__ import annotations

from io import BytesIO

from openpyxl import load_workbook

from odoo_finance_data_auditor.dashboard import (
    apply_exception_filters,
    build_kpis,
    load_dashboard_results,
    workbook_bytes,
)


def test_dashboard_results_load_registered_checks(sample_data_dir):
    exceptions, exception_rows = load_dashboard_results(sample_data_dir)

    assert len(exceptions) == 13
    assert len(exception_rows) == 13
    assert {"risk_level", "issue_type", "source_model", "recommended_action"}.issubset(exception_rows.columns)


def test_dashboard_kpis_count_current_sample_exceptions(sample_data_dir):
    _, exception_rows = load_dashboard_results(sample_data_dir)

    assert build_kpis(exception_rows) == {
        "total_checks": 10,
        "total_exceptions": 13,
        "high_risk_exceptions": 10,
        "exception_types": 10,
    }


def test_dashboard_filters_by_risk_issue_and_source(sample_data_dir):
    _, exception_rows = load_dashboard_results(sample_data_dir)

    filtered = apply_exception_filters(
        exception_rows,
        risk_levels=["medium"],
        issue_types=["Manual journal above configured threshold"],
        source_models=["journal_entries"],
    )

    assert filtered["record_id"].tolist() == ["JL008"]


def test_dashboard_workbook_bytes_are_excel_file(sample_data_dir):
    _, exception_rows = load_dashboard_results(sample_data_dir)

    payload = workbook_bytes(exception_rows)

    assert payload[:2] == b"PK"
    workbook = load_workbook(filename=BytesIO(payload))
    assert workbook.sheetnames == ["Summary", "Exceptions"]

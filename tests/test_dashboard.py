from __future__ import annotations

from io import BytesIO

from openpyxl import load_workbook

from odoo_finance_data_auditor.dashboard import (
    apply_exception_filters,
    build_kpis,
    count_by_dimension,
    friendly_source_model,
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


def test_friendly_source_model_labels_known_and_fallback_values():
    assert friendly_source_model("journal_entries") == "Journal Entries"
    assert friendly_source_model("bank_statement_lines") == "Bank Statement Lines"
    assert friendly_source_model("custom_model_name") == "Custom Model Name"


def test_count_by_dimension_sorts_issue_types_and_formats_sources(sample_data_dir):
    _, exception_rows = load_dashboard_results(sample_data_dir)

    issue_counts = count_by_dimension(exception_rows, "issue_type", "Issue Type")
    source_counts = count_by_dimension(
        exception_rows,
        "source_model",
        "ERP Area",
        friendly_labels=True,
    )

    assert issue_counts.iloc[0]["exception_count"] == 2
    assert "Vendor Bills" in source_counts["ERP Area"].tolist()
    assert "Journal Entries" in source_counts["ERP Area"].tolist()


def test_dashboard_workbook_bytes_are_excel_file(sample_data_dir):
    _, exception_rows = load_dashboard_results(sample_data_dir)

    payload = workbook_bytes(exception_rows)

    assert payload[:2] == b"PK"
    workbook = load_workbook(filename=BytesIO(payload))
    assert workbook.sheetnames == ["Summary", "Exceptions"]

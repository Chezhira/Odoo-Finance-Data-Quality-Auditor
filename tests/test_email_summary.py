from __future__ import annotations

from datetime import datetime, timezone

from odoo_finance_data_auditor.config import load_audit_config
from odoo_finance_data_auditor.email_summary import build_email_summary, write_email_summary
from odoo_finance_data_auditor.loader import load_csv_exports
from odoo_finance_data_auditor.rules import run_all_rules


def test_build_email_summary_includes_run_metadata_and_counts(sample_data_dir):
    config = load_audit_config()
    exceptions = run_all_rules(load_csv_exports(sample_data_dir), config)

    summary = build_email_summary(
        exceptions=exceptions,
        config=config,
        checks_run=10,
        workbook_path=None,
        run_at=datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc),
    )

    assert "Run date/time: 2026-04-15T12:00:00+00:00" in summary
    assert "Checks run: 10" in summary
    assert "Total exceptions found: 13" in summary
    assert "## Exceptions By Risk" in summary
    assert "## Top Recommended Follow-Up Actions" in summary


def test_write_email_summary_creates_markdown_file(sample_data_dir, tmp_path):
    config = load_audit_config(profile="manufacturing")
    exceptions = run_all_rules(load_csv_exports(sample_data_dir), config)
    output_path = tmp_path / "email_summary.md"

    write_email_summary(
        exceptions=exceptions,
        output_path=output_path,
        config=config,
        checks_run=10,
        workbook_path=tmp_path / "report.xlsx",
    )

    assert output_path.exists()
    text = output_path.read_text(encoding="utf-8")
    assert "manufacturing" in text
    assert "Excel exception workbook" in text

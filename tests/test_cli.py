from __future__ import annotations

from odoo_finance_data_auditor.cli import main


def test_cli_backward_compatible_defaults(capsys, tmp_path):
    output_path = tmp_path / "exception_report.xlsx"

    main(["--sample-data", "data/sample", "--output", str(output_path)])

    output = capsys.readouterr().out
    assert "Ran 10 checks and found 13 exceptions." in output
    assert output_path.exists()


def test_cli_profile_and_email_summary(capsys, tmp_path):
    output_path = tmp_path / "manufacturing_exception_report.xlsx"
    summary_path = tmp_path / "manufacturing_email_summary.md"

    main(
        [
            "--sample-data",
            "data/sample",
            "--profile",
            "manufacturing",
            "--output",
            str(output_path),
            "--email-summary",
            str(summary_path),
        ]
    )

    output = capsys.readouterr().out
    assert "Ran 10 checks and found 13 exceptions." in output
    assert output_path.exists()
    assert summary_path.exists()

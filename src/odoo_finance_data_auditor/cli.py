from __future__ import annotations

import argparse
from pathlib import Path

from odoo_finance_data_auditor.config import load_audit_config
from odoo_finance_data_auditor.email_summary import write_email_summary
from odoo_finance_data_auditor.loader import load_csv_exports
from odoo_finance_data_auditor.reporting import export_exception_report
from odoo_finance_data_auditor.rules import CHECK_REGISTRY, run_all_rules


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Odoo-style finance data quality checks.")
    parser.add_argument("--sample-data", type=Path, default=Path("data/sample"))
    parser.add_argument("--output", type=Path, default=Path("reports/exception_report.xlsx"))
    parser.add_argument("--config", type=Path, help="Path to a rules YAML config. Takes priority over --profile.")
    parser.add_argument("--profile", help="Named profile from config/profiles, for example manufacturing.")
    parser.add_argument("--email-summary", type=Path, help="Write an email-ready Markdown exception summary.")
    args = parser.parse_args(argv)

    data = load_csv_exports(args.sample_data)
    config = load_audit_config(config_path=args.config, profile=args.profile)
    exceptions = run_all_rules(data, config)
    checks_run = len(config.enabled_checks or CHECK_REGISTRY)
    export_exception_report(exceptions, args.output)
    if args.email_summary:
        write_email_summary(
            exceptions=exceptions,
            output_path=args.email_summary,
            config=config,
            checks_run=checks_run,
            workbook_path=args.output,
        )

    print(f"Ran {checks_run} checks and found {len(exceptions)} exceptions.")
    print(f"Exception report written to {args.output}")
    if args.email_summary:
        print(f"Email-ready summary written to {args.email_summary}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from pathlib import Path

from odoo_finance_data_auditor.config import AuditConfig
from odoo_finance_data_auditor.loader import load_csv_exports
from odoo_finance_data_auditor.reporting import export_exception_report
from odoo_finance_data_auditor.rules import CHECK_REGISTRY, run_all_rules


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Odoo-style finance data quality checks.")
    parser.add_argument("--sample-data", type=Path, default=Path("data/sample"))
    parser.add_argument("--output", type=Path, default=Path("reports/exception_report.xlsx"))
    args = parser.parse_args()

    data = load_csv_exports(args.sample_data)
    exceptions = run_all_rules(data, AuditConfig())
    export_exception_report(exceptions, args.output)

    print(f"Ran {len(CHECK_REGISTRY)} checks and found {len(exceptions)} exceptions.")
    print(f"Exception report written to {args.output}")


if __name__ == "__main__":
    main()

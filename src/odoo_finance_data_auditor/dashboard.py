from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd

from odoo_finance_data_auditor.config import AuditConfig
from odoo_finance_data_auditor.loader import load_csv_exports
from odoo_finance_data_auditor.reporting import exceptions_to_dataframe, write_exception_workbook
from odoo_finance_data_auditor.rules import CHECK_REGISTRY, run_all_rules


def load_dashboard_results(sample_data_dir: Path) -> tuple[list[object], pd.DataFrame]:
    data = load_csv_exports(sample_data_dir)
    exceptions = run_all_rules(data, AuditConfig())
    return exceptions, exceptions_to_dataframe(exceptions)


def build_kpis(exception_rows: pd.DataFrame) -> dict[str, int]:
    if exception_rows.empty:
        return {
            "total_checks": len(CHECK_REGISTRY),
            "total_exceptions": 0,
            "high_risk_exceptions": 0,
            "exception_types": 0,
        }

    return {
        "total_checks": len(CHECK_REGISTRY),
        "total_exceptions": int(len(exception_rows)),
        "high_risk_exceptions": int(exception_rows["risk_level"].eq("high").sum()),
        "exception_types": int(exception_rows["issue_type"].nunique()),
    }


def apply_exception_filters(
    exception_rows: pd.DataFrame,
    risk_levels: list[str] | None = None,
    issue_types: list[str] | None = None,
    source_models: list[str] | None = None,
) -> pd.DataFrame:
    filtered = exception_rows.copy()

    if risk_levels:
        filtered = filtered[filtered["risk_level"].isin(risk_levels)]
    if issue_types:
        filtered = filtered[filtered["issue_type"].isin(issue_types)]
    if source_models:
        filtered = filtered[filtered["source_model"].isin(source_models)]

    return filtered


def workbook_bytes(exception_rows: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    write_exception_workbook(exception_rows, buffer)
    return buffer.getvalue()

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd

from odoo_finance_data_auditor.config import AuditConfig
from odoo_finance_data_auditor.loader import REQUIRED_COLUMNS, load_csv_exports, validate_schemas
from odoo_finance_data_auditor.reporting import exceptions_to_dataframe, write_exception_workbook
from odoo_finance_data_auditor.rules import CHECK_REGISTRY, run_all_rules


SOURCE_MODEL_LABELS = {
    "journal_entries": "Journal Entries",
    "vendor_bills": "Vendor Bills",
    "customer_invoices": "Customer Invoices",
    "inventory_valuation": "Inventory Valuation",
    "bank_statement_lines": "Bank Statement Lines",
}

REQUIRED_UPLOAD_DATASETS = (
    "accounts",
    "journal_entries",
    "vendor_bills",
    "customer_invoices",
    "inventory_valuation",
    "bank_statement_lines",
)


def load_dashboard_results(sample_data_dir: Path) -> tuple[list[object], pd.DataFrame]:
    data = load_csv_exports(sample_data_dir)
    return run_dashboard_results(data)


def run_dashboard_results(data: dict[str, pd.DataFrame]) -> tuple[list[object], pd.DataFrame]:
    exceptions = run_all_rules(data, AuditConfig())
    return exceptions, exceptions_to_dataframe(exceptions)


def required_csv_filenames() -> list[str]:
    return [f"{dataset_name}.csv" for dataset_name in REQUIRED_UPLOAD_DATASETS]


def match_uploaded_csv_files(uploaded_files: list[object] | None) -> dict[str, object]:
    matched: dict[str, object] = {}
    for uploaded_file in uploaded_files or []:
        filename = Path(getattr(uploaded_file, "name", "")).name.lower()
        if filename in required_csv_filenames():
            matched[filename] = uploaded_file
    return matched


def missing_required_csv_files(matched_files: dict[str, object]) -> list[str]:
    return [filename for filename in required_csv_filenames() if filename not in matched_files]


def upload_status_rows(matched_files: dict[str, object]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "required_file": filename,
                "status": "Uploaded" if filename in matched_files else "Missing",
            }
            for filename in required_csv_filenames()
        ]
    )


def load_uploaded_csv_exports(uploaded_files: list[object] | None) -> dict[str, pd.DataFrame]:
    matched_files = match_uploaded_csv_files(uploaded_files)
    missing_files = missing_required_csv_files(matched_files)
    if missing_files:
        missing_list = ", ".join(missing_files)
        raise FileNotFoundError(f"Missing required CSV files: {missing_list}")

    data: dict[str, pd.DataFrame] = {}
    for dataset_name in REQUIRED_COLUMNS:
        uploaded_file = matched_files[f"{dataset_name}.csv"]
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        data[dataset_name] = pd.read_csv(uploaded_file)

    validate_schemas(data)
    return data


def load_uploaded_dashboard_results(uploaded_files: list[object] | None) -> tuple[list[object], pd.DataFrame]:
    return run_dashboard_results(load_uploaded_csv_exports(uploaded_files))


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


def friendly_source_model(source_model: str) -> str:
    return SOURCE_MODEL_LABELS.get(source_model, source_model.replace("_", " ").title())


def count_by_dimension(
    exception_rows: pd.DataFrame,
    column: str,
    label_column: str,
    friendly_labels: bool = False,
    risk_order: bool = False,
) -> pd.DataFrame:
    if exception_rows.empty:
        return pd.DataFrame(columns=[label_column, "exception_count"])

    counts = (
        exception_rows[column]
        .value_counts()
        .rename_axis(column)
        .reset_index(name="exception_count")
    )

    if risk_order:
        order = {"high": 0, "medium": 1, "low": 2}
        counts = counts.sort_values(by=column, key=lambda values: values.map(order).fillna(99))
    else:
        counts = counts.sort_values(["exception_count", column], ascending=[False, True])

    counts[label_column] = (
        counts[column].map(friendly_source_model)
        if friendly_labels
        else counts[column].astype(str)
    )
    return counts[[label_column, "exception_count"]]


def chart_height(row_count: int, base: int = 80, row_height: int = 34, maximum: int = 420) -> int:
    return min(max(base + (row_count * row_height), 180), maximum)


def integer_tick_values(max_count: int) -> list[int]:
    return list(range(0, max(int(max_count), 0) + 1))

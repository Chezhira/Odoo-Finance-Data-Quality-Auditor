from __future__ import annotations

from pathlib import Path

import pandas as pd

from odoo_finance_data_auditor.exceptions import AuditException


def exceptions_to_dataframe(exceptions: list[AuditException]) -> pd.DataFrame:
    columns = [
        "rule_id",
        "rule_name",
        "severity",
        "source",
        "record_id",
        "message",
        "amount",
        "date",
        "metadata",
    ]
    return pd.DataFrame([exception.to_dict() for exception in exceptions], columns=columns)


def export_exception_report(exceptions: list[AuditException], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exception_rows = exceptions_to_dataframe(exceptions)

    summary = (
        exception_rows.groupby(["rule_id", "rule_name", "severity"], dropna=False)
        .size()
        .reset_index(name="exception_count")
        if not exception_rows.empty
        else pd.DataFrame(columns=["rule_id", "rule_name", "severity", "exception_count"])
    )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        exception_rows.to_excel(writer, sheet_name="Exceptions", index=False)

    return output_path

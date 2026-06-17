from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd
from openpyxl.styles import Font

from odoo_finance_data_auditor.exceptions import AuditException


EXCEPTION_COLUMNS = [
    "check_name",
    "risk_level",
    "entity",
    "source_model",
    "record_id",
    "issue_type",
    "date",
    "amount",
    "recommended_action",
    "message",
    "check_id",
    "metadata",
]


def exceptions_to_dataframe(exceptions: list[AuditException]) -> pd.DataFrame:
    return pd.DataFrame([exception.to_dict() for exception in exceptions], columns=EXCEPTION_COLUMNS)


def export_exception_report(exceptions: list[AuditException], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_exception_workbook(exceptions_to_dataframe(exceptions), output_path)

    return output_path


def write_exception_workbook(exception_rows: pd.DataFrame, output: Path | str | BinaryIO) -> None:
    summary = exception_summary(exception_rows)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        exception_rows.to_excel(writer, sheet_name="Exceptions", index=False)
        for worksheet in writer.book.worksheets:
            _format_worksheet(worksheet)


def exception_summary(exception_rows: pd.DataFrame) -> pd.DataFrame:
    return (
        exception_rows.groupby(["risk_level", "issue_type"], dropna=False)
        .size()
        .reset_index(name="exception_count")
        if not exception_rows.empty
        else pd.DataFrame(columns=["risk_level", "issue_type", "exception_count"])
    )


def _format_worksheet(worksheet) -> None:
    worksheet.freeze_panes = "A2"

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for column_cells in worksheet.columns:
        header = str(column_cells[0].value or "")
        values = [str(cell.value or "") for cell in column_cells[:50]]
        width = min(max([len(header), *(len(value) for value in values)]) + 2, 60)
        worksheet.column_dimensions[column_cells[0].column_letter].width = width

# Odoo Finance Data Quality Auditor

CSV-first finance control checks for synthetic Odoo-style exports. The first
vertical slice loads sample data, validates required schemas, runs three finance
data quality rules, and exports a basic Excel exception report.

## Included checks

1. Posted entries using suspense accounts after the finance close date
2. Duplicate vendor bill references for the same vendor
3. Unreconciled bank statement lines older than the configured threshold

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m odoo_finance_data_auditor.cli --sample-data data\sample --output reports\sample_exception_report.xlsx
```

The committed sample data is synthetic only.

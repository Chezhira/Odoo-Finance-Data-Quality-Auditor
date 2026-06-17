# Odoo Finance Data Quality Auditor

CSV-first finance control checks for synthetic Odoo-style exports. The current
vertical slice loads sample data, validates required schemas, runs seven finance
data quality checks, and exports a readable Excel exception report.

## Included checks

1. Posted suspense entries after the finance close date
2. Duplicate vendor bill references for the same vendor
3. Unreconciled bank statement lines older than the configured threshold
4. Customer invoices with missing tax codes
5. Vendor bills with missing tax evidence fields
6. Inventory valuation records with negative quantity or negative value
7. Posted journal entries to inactive or deprecated accounts

Each check has a central registry entry with its name, description, risk level,
source model, and recommended action. The CLI uses this registry so the reported
check count stays aligned with the implemented checks.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest-tmp
.\.venv\Scripts\python.exe -m odoo_finance_data_auditor.cli --sample-data data\sample --output reports\sample_exception_report.xlsx
```

The sample command writes an Excel workbook with:

- `Summary`: exception counts by risk level and issue type
- `Exceptions`: check name, risk level, entity, source model, record ID, issue
  type, date, amount, recommended action, message, check ID, and metadata

The committed sample data is synthetic only. Generated reports are written under
`reports/` and ignored by git, except for `reports/.gitkeep`.

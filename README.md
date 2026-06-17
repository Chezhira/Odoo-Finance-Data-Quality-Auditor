# Odoo Finance Data Quality Auditor

A finance controls and audit-readiness tool for reviewing Odoo-compatible accounting exports. The project validates ERP finance data, flags control exceptions, and produces an Excel exception review workbook for finance, audit, reconciliation, and systems cleanup workflows.

## Why This Exists

Finance teams often need a fast way to assess close readiness before month-end reporting, audit fieldwork, ERP cleanup, or finance systems assurance reviews. This project turns representative ERP finance data extracts into a practical exception review:

- close readiness checks for journals, suspense, bank reconciliation, and manual adjustments
- audit trail review for inactive accounts, deprecated accounts, and high-risk postings
- tax evidence checks for customer invoices and vendor bills
- inventory valuation review for negative quantity or value records
- reconciliation follow-up for aged unreconciled bank lines
- ERP data quality review for analytics, FX metadata, and duplicate references

## Portfolio Signal

This project demonstrates finance systems judgement and practical engineering delivery across:

- Odoo and ERP accounting data understanding
- audit-style exception reporting and recommended actions
- automated validation discipline with positive and negative pytest coverage
- CI/CD-ready project structure and repeatable smoke tests
- finance controls thinking across close readiness, tax evidence, reconciliation, inventory valuation, and ERP cleanup
- portfolio-ready delivery for Odoo Functional Consultant, ERP Business Analyst, Finance Systems Analyst, and Accounting Systems Consultant roles

## Current Checks

The validation engine currently runs 10 registered checks:

1. Posted suspense entries after the finance close date
2. Duplicate vendor bill references for the same vendor
3. Unreconciled bank statement lines older than the configured threshold
4. Customer invoices with missing tax codes
5. Vendor bills with missing tax evidence fields
6. Inventory valuation records with negative quantity or negative value
7. Posted journal entries to inactive or deprecated accounts
8. Missing analytic tags on selected expense or project accounts
9. FX entries missing currency or exchange rate metadata
10. Manual journals above the configured review threshold

Each check has a central registry entry with its name, description, risk level, source model, and recommended action. The CLI and dashboard both use this registry so check counts stay aligned with the implemented controls.

## Streamlit Dashboard

The dashboard provides a finance control tower style review screen for sample ERP finance exports. It shows:

- KPI cards for checks run, exceptions found, high-risk exceptions, and issue types
- exception breakdowns by risk level, issue type, and source model
- filters for risk level, issue type, and source model
- a detailed exception review table with recommended actions
- an Excel workbook download for the current filtered exception set

The dashboard is intended for executive-facing audit-readiness review: a viewer can see the size of the exception population, where risk is concentrated, which source models need cleanup, and what remediation action is recommended.

Run it with:

```powershell
$env:PYTHONPATH='src'; streamlit run app.py
```

## CLI Usage

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest-tmp
$env:PYTHONPATH='src'; python -m odoo_finance_data_auditor.cli --sample-data data\sample --output reports\sample_exception_report.xlsx
```

The CLI writes an Excel exception review workbook with:

- `Summary`: exception counts by risk level and issue type
- `Exceptions`: check name, risk level, entity, source model, record ID, issue type, date, amount, recommended action, message, check ID, and metadata

With the included sample data, the CLI currently runs 10 checks and produces 13 intentionally triggered exceptions.

## Sample Data And Privacy

This repository includes synthetic sample data for demonstration and testing purposes. The sample files are designed to resemble common Odoo finance exports, but they do not contain employer, client, or production data.

Generated reports are written under `reports/` and ignored by git, except for `reports/.gitkeep`.

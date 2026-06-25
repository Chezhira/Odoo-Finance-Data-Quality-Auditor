# Case Study: Odoo Finance Data Quality Auditor

## Context

Finance teams using ERP systems often face close delays and audit-readiness issues because data-quality problems are discovered late. Common examples include unreconciled bank transactions, duplicate vendor bill references, missing tax evidence, negative inventory valuation records, inactive accounts used in postings, incomplete FX metadata, and high-value manual journals without clear review evidence.

## Objective

Build a lightweight finance systems control tool that can review Odoo-compatible accounting exports before month-end close and produce a clear exception workflow for finance managers, ERP analysts, and audit teams.

## Approach

The project maps common ERP accounting risks into repeatable validation checks. It accepts Odoo-compatible sample exports, runs finance-control checks, classifies issues by risk area, and produces both an interactive Streamlit dashboard and an Excel exception workbook. Rule thresholds and enabled checks can be adjusted through YAML configuration files or company-specific profiles for contexts such as manufacturing, multi-company operations, and audit preparation.

The workflow was designed around practical finance review questions:

- Are there suspense or clearing-account balances that need close review?
- Are there duplicate vendor bill references?
- Are old bank transactions still unreconciled?
- Are tax codes or vendor tax evidence missing?
- Are inactive accounts still being used?
- Are there negative inventory valuation records?
- Are high-value manual journals supported by review evidence?

## Output

The tool produces:

- Streamlit dashboard for exception review
- Risk-ranked exception summary
- Excel remediation workbook
- CLI execution option
- Configurable thresholds and company-specific rule profiles
- Email-ready Markdown exception summary for scheduled reporting workflows
- Synthetic sample data for demonstration
- Automated test coverage and GitHub Actions validation

## Skills Demonstrated

- Finance systems analysis
- ERP data-quality review
- Odoo-compatible accounting data interpretation
- Internal controls and audit-readiness thinking
- Python automation
- Streamlit dashboarding
- Excel exception reporting
- Configurable finance controls and profile design
- Testing and CI discipline
- Finance-to-technology translation

## Business Value

The project demonstrates how finance teams can identify ERP data-quality issues earlier in the close cycle, reduce manual review effort, improve audit readiness, and give finance systems teams a clearer remediation list. The email-ready Markdown output can be handed to Windows Task Scheduler, cron, GitHub Actions, n8n, or another external scheduling tool without requiring the application to send emails directly.

## Relevance to Target Roles

This case study is relevant to:

- Finance Systems Analyst
- ERP Business Analyst
- Odoo Functional Consultant
- Finance Transformation Analyst
- Finance Automation Specialist
- Accounting Systems Consultant
- Finance Data Quality Analyst

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from odoo_finance_data_auditor.dashboard import (
    apply_exception_filters,
    build_kpis,
    load_dashboard_results,
    workbook_bytes,
)
from odoo_finance_data_auditor.reporting import exception_summary
from odoo_finance_data_auditor.rules import CHECK_REGISTRY


SAMPLE_DATA_DIR = Path("data/sample")


st.set_page_config(
    page_title="Odoo Finance Data Quality Auditor",
    layout="wide",
)


def main() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .hero {
            border-left: 5px solid #2563eb;
            padding: 0.2rem 0 0.7rem 1rem;
            margin-bottom: 1.2rem;
        }
        .hero h1 { margin: 0; font-size: 2rem; letter-spacing: 0; }
        .hero p { margin: 0.35rem 0 0; color: #475569; font-size: 1rem; max-width: 60rem; }
        .kpi {
            border: 1px solid #d8dee8;
            border-radius: 8px;
            padding: 1rem;
            background: #ffffff;
            min-height: 7rem;
        }
        .kpi-label { color: #64748b; font-size: 0.82rem; text-transform: uppercase; }
        .kpi-value { font-size: 2rem; font-weight: 700; color: #0f172a; }
        .section-note { color: #64748b; font-size: 0.95rem; margin-top: -0.6rem; }
        .export-panel {
            border: 1px solid #d8dee8;
            border-radius: 8px;
            padding: 1rem;
            background: #f8fafc;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="hero">
            <h1>Odoo Finance Data Quality Auditor</h1>
            <p>Finance controls and audit-readiness review for Odoo-compatible accounting exports, focused on close readiness, exception follow-up, tax evidence, reconciliation, and ERP cleanup.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.header("Review Scope")
    sample_data_dir = Path(
        st.sidebar.text_input("ERP export folder", value=str(SAMPLE_DATA_DIR))
    )
    st.sidebar.caption("Uses the registered validation checks and produces the same exception workbook as the CLI.")

    _, exception_rows = load_dashboard_results(sample_data_dir)
    kpis = build_kpis(exception_rows)

    st.caption(f"Loaded `{sample_data_dir}` and ran {len(CHECK_REGISTRY)} registered finance control checks.")

    kpi_cols = st.columns(4)
    _kpi_card(kpi_cols[0], "Checks run", kpis["total_checks"])
    _kpi_card(kpi_cols[1], "Exceptions found", kpis["total_exceptions"])
    _kpi_card(kpi_cols[2], "High risk", kpis["high_risk_exceptions"])
    _kpi_card(kpi_cols[3], "Issue types", kpis["exception_types"])

    st.divider()

    st.subheader("Scope Exception Review")
    st.markdown(
        '<div class="section-note">Filter the review population before exporting the workbook or inspecting individual follow-up actions.</div>',
        unsafe_allow_html=True,
    )
    filter_cols = st.columns(3)
    selected_risks = filter_cols[0].multiselect(
        "Risk level",
        options=_sorted_unique(exception_rows, "risk_level"),
        default=_sorted_unique(exception_rows, "risk_level"),
    )
    selected_issues = filter_cols[1].multiselect(
        "Issue type",
        options=_sorted_unique(exception_rows, "issue_type"),
        default=_sorted_unique(exception_rows, "issue_type"),
    )
    selected_sources = filter_cols[2].multiselect(
        "Source model",
        options=_sorted_unique(exception_rows, "source_model"),
        default=_sorted_unique(exception_rows, "source_model"),
    )

    filtered = apply_exception_filters(exception_rows, selected_risks, selected_issues, selected_sources)
    st.caption(f"Showing {len(filtered)} of {len(exception_rows)} exceptions after filters.")

    st.subheader("Control Breakdowns")
    st.markdown(
        '<div class="section-note">Use these views to see where cleanup effort is concentrated by risk, issue type, and source model.</div>',
        unsafe_allow_html=True,
    )
    left, middle, right = st.columns(3)
    with left:
        st.subheader("Risk Level")
        st.bar_chart(_count_by(filtered, "risk_level"))
    with middle:
        st.subheader("Issue Type")
        st.dataframe(
            exception_summary(filtered).sort_values("exception_count", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
    with right:
        st.subheader("Source Model")
        st.bar_chart(_count_by(filtered, "source_model"))

    st.subheader("Exception Review")
    st.markdown(
        '<div class="section-note">Recommended actions are included so finance and systems owners can move directly from review to remediation.</div>',
        unsafe_allow_html=True,
    )
    review_columns = [
        "risk_level",
        "issue_type",
        "source_model",
        "record_id",
        "date",
        "amount",
        "recommended_action",
        "message",
    ]
    st.dataframe(
        filtered[review_columns].sort_values(["risk_level", "source_model", "record_id"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "risk_level": st.column_config.TextColumn("Risk"),
            "issue_type": st.column_config.TextColumn("Issue Type", width="medium"),
            "source_model": st.column_config.TextColumn("Source Model"),
            "record_id": st.column_config.TextColumn("Record ID"),
            "date": st.column_config.TextColumn("Date"),
            "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
            "recommended_action": st.column_config.TextColumn("Recommended Action", width="large"),
            "message": st.column_config.TextColumn("Exception Detail", width="large"),
        },
    )

    st.markdown(
        """
        <div class="export-panel">
            <strong>Export exception workbook</strong><br>
            Download the current filtered exception set for audit trail review, reconciliation follow-up, or ERP cleanup planning.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.download_button(
        "Download Excel exception workbook",
        data=workbook_bytes(filtered),
        file_name="sample_exception_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )


def _kpi_card(column, label: str, value: int) -> None:
    column.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _sorted_unique(rows: pd.DataFrame, column: str) -> list[str]:
    if rows.empty:
        return []
    return sorted(rows[column].dropna().astype(str).unique().tolist())


def _count_by(rows: pd.DataFrame, column: str) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame({"count": []})
    counts = rows[column].value_counts().rename_axis(column).reset_index(name="count")
    if column == "risk_level":
        order = {"high": 0, "medium": 1, "low": 2}
        counts = counts.sort_values(by=column, key=lambda values: values.map(order).fillna(99))
    return counts.set_index(column)


if __name__ == "__main__":
    main()

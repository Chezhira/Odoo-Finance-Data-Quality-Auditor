from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from odoo_finance_data_auditor.dashboard import (
    apply_exception_filters,
    build_kpis,
    count_by_dimension,
    friendly_source_model,
    load_dashboard_results,
    workbook_bytes,
)
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
        div[data-testid="stHeadingWithActionElements"] h3 { font-size: 1.05rem; }
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
        "ERP area",
        options=_sorted_unique(exception_rows, "source_model"),
        default=_sorted_unique(exception_rows, "source_model"),
        format_func=friendly_source_model,
    )

    filtered = apply_exception_filters(exception_rows, selected_risks, selected_issues, selected_sources)
    st.caption(f"Showing {len(filtered)} of {len(exception_rows)} exceptions after filters.")

    st.subheader("Control Breakdowns")
    st.markdown(
        '<div class="section-note">Use these views to see where cleanup effort is concentrated by risk, issue type, and source model.</div>',
        unsafe_allow_html=True,
    )
    left, middle, right = st.columns([1, 1.45, 1.1])
    with left:
        st.subheader("Risk Concentration")
        _horizontal_bar_chart(
            count_by_dimension(filtered, "risk_level", "Risk", risk_order=True),
            label_column="Risk",
            height=230,
        )
    with middle:
        st.subheader("Top Exception Types")
        _horizontal_bar_chart(
            count_by_dimension(filtered, "issue_type", "Issue Type"),
            label_column="Issue Type",
            height=390,
        )
    with right:
        st.subheader("Affected ERP Areas")
        _horizontal_bar_chart(
            count_by_dimension(filtered, "source_model", "ERP Area", friendly_labels=True),
            label_column="ERP Area",
            height=300,
        )

    st.subheader("Exception Review")
    st.markdown(
        '<div class="section-note">Recommended actions are included so finance and systems owners can move directly from review to remediation.</div>',
        unsafe_allow_html=True,
    )
    review_columns = [
        "risk_level",
        "issue_type",
        "source_model",
        "source_label",
        "record_id",
        "date",
        "amount",
        "recommended_action",
        "message",
    ]
    review_rows = filtered.copy()
    review_rows["source_label"] = review_rows["source_model"].map(friendly_source_model)
    st.dataframe(
        review_rows[review_columns].sort_values(["risk_level", "source_label", "record_id"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "risk_level": st.column_config.TextColumn("Risk"),
            "issue_type": st.column_config.TextColumn("Issue Type", width="medium"),
            "source_model": None,
            "source_label": st.column_config.TextColumn("ERP Area"),
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


def _horizontal_bar_chart(rows: pd.DataFrame, label_column: str, height: int) -> None:
    if rows.empty:
        st.info("No exceptions match the current filters.")
        return

    chart_rows = rows.sort_values("exception_count", ascending=True)
    st.bar_chart(
        chart_rows,
        x="exception_count",
        y=label_column,
        horizontal=True,
        height=height,
        use_container_width=True,
    )


if __name__ == "__main__":
    main()

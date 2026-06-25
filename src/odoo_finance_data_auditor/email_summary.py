from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

from odoo_finance_data_auditor.config import AuditConfig
from odoo_finance_data_auditor.exceptions import AuditException


def write_email_summary(
    exceptions: list[AuditException],
    output_path: Path,
    config: AuditConfig,
    checks_run: int,
    workbook_path: Path | None = None,
    run_at: datetime | None = None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_email_summary(
            exceptions=exceptions,
            config=config,
            checks_run=checks_run,
            workbook_path=workbook_path,
            run_at=run_at,
        ),
        encoding="utf-8",
    )
    return output_path


def build_email_summary(
    exceptions: list[AuditException],
    config: AuditConfig,
    checks_run: int,
    workbook_path: Path | None = None,
    run_at: datetime | None = None,
) -> str:
    run_at = run_at or datetime.now().astimezone()
    risk_counts = Counter(exception.risk_level for exception in exceptions)
    check_counts = Counter(exception.check_name for exception in exceptions)
    action_counts = Counter(exception.recommended_action for exception in exceptions)

    lines = [
        "# Odoo Finance Data Quality Auditor Exception Summary",
        "",
        f"- Run date/time: {run_at.isoformat(timespec='seconds')}",
        f"- Profile/config: {config.profile_name} ({config.config_source})",
        f"- Checks run: {checks_run}",
        f"- Total exceptions found: {len(exceptions)}",
    ]
    if workbook_path is not None:
        lines.append(f"- Excel exception workbook: {workbook_path}")

    lines.extend(["", "## Exceptions By Risk", ""])
    lines.extend(_count_lines(risk_counts, empty_label="No exceptions by risk."))

    lines.extend(["", "## Exceptions By Check", ""])
    lines.extend(_count_lines(check_counts, empty_label="No exceptions by check."))

    lines.extend(["", "## Top Recommended Follow-Up Actions", ""])
    for action, count in action_counts.most_common(5):
        lines.append(f"- {action}: {count}")
    if not action_counts:
        lines.append("- No follow-up actions required.")

    lines.append("")
    return "\n".join(lines)


def _count_lines(counts: Counter[str], empty_label: str) -> list[str]:
    if not counts:
        return [f"- {empty_label}"]
    return [f"- {name}: {count}" for name, count in counts.most_common()]

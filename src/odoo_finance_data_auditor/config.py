from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AuditConfig:
    close_date: date = date(2026, 3, 31)
    bank_line_age_days: int = 60
    as_of_date: date = date(2026, 4, 15)
    manual_journal_threshold: float = 10000.0

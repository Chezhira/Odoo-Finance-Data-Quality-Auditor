from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class AuditException:
    check_id: str
    check_name: str
    risk_level: str
    source_model: str
    entity: str
    record_id: str
    issue_type: str
    message: str
    recommended_action: str
    amount: float | None = None
    date: date | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["date"] = self.date.isoformat() if self.date else None
        row["metadata"] = self.metadata or {}
        return row

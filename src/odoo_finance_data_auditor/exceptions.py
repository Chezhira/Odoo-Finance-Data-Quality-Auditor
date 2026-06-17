from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class AuditException:
    rule_id: str
    rule_name: str
    severity: str
    source: str
    record_id: str
    message: str
    amount: float | None = None
    date: date | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["date"] = self.date.isoformat() if self.date else None
        row["metadata"] = self.metadata or {}
        return row

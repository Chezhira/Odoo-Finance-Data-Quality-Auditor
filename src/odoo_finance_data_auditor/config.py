from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "rules.default.yml"
PROFILE_DIR = PROJECT_ROOT / "config" / "profiles"


@dataclass(frozen=True)
class AuditConfig:
    close_date: date = date(2026, 3, 31)
    bank_line_age_days: int = 60
    as_of_date: date = date(2026, 4, 15)
    manual_journal_threshold: float = 10000.0
    negative_inventory_tolerance: float = 0.0
    enabled_checks: tuple[str, ...] | None = None
    profile_name: str = "default"
    config_source: str = "built-in defaults"


def load_audit_config(config_path: Path | None = None, profile: str | None = None) -> AuditConfig:
    path = resolve_config_path(config_path=config_path, profile=profile)
    if path is None:
        return AuditConfig()

    raw_config = _read_yaml(path)
    return audit_config_from_mapping(raw_config, source=path)


def resolve_config_path(config_path: Path | None = None, profile: str | None = None) -> Path | None:
    if config_path is not None:
        return config_path
    if profile:
        return PROFILE_DIR / f"{profile}.yml"
    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH
    return None


def list_available_profiles(profile_dir: Path = PROFILE_DIR) -> list[str]:
    if not profile_dir.exists():
        return []
    return sorted(path.stem for path in profile_dir.glob("*.yml"))


def audit_config_from_mapping(raw_config: dict[str, Any], source: Path | str) -> AuditConfig:
    thresholds = raw_config.get("thresholds", {}) or {}
    defaults = AuditConfig()
    enabled_checks = raw_config.get("enabled_checks")

    return AuditConfig(
        close_date=_parse_date(thresholds.get("close_date", defaults.close_date)),
        bank_line_age_days=int(thresholds.get("bank_line_age_days", defaults.bank_line_age_days)),
        as_of_date=_parse_date(thresholds.get("as_of_date", defaults.as_of_date)),
        manual_journal_threshold=float(
            thresholds.get("manual_journal_threshold", defaults.manual_journal_threshold)
        ),
        negative_inventory_tolerance=float(
            thresholds.get("negative_inventory_tolerance", defaults.negative_inventory_tolerance)
        ),
        enabled_checks=tuple(enabled_checks) if enabled_checks else None,
        profile_name=str(raw_config.get("profile_name", "custom")),
        config_source=str(source),
    )


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _parse_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))

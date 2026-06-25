from __future__ import annotations

from datetime import date

from odoo_finance_data_auditor.config import (
    audit_config_from_mapping,
    list_available_profiles,
    load_audit_config,
)
from odoo_finance_data_auditor.loader import load_csv_exports
from odoo_finance_data_auditor.rules import run_all_rules


def test_default_config_loading_uses_yaml_defaults():
    config = load_audit_config()

    assert config.profile_name == "default"
    assert config.close_date == date(2026, 3, 31)
    assert config.bank_line_age_days == 60
    assert config.manual_journal_threshold == 10000.0
    assert config.negative_inventory_tolerance == 0.0
    assert config.enabled_checks and len(config.enabled_checks) == 10


def test_profile_loading_uses_named_profile_thresholds():
    config = load_audit_config(profile="manufacturing")

    assert config.profile_name == "manufacturing"
    assert config.bank_line_age_days == 45
    assert config.manual_journal_threshold == 7500.0


def test_available_profiles_include_expected_company_contexts():
    assert list_available_profiles() == ["audit_prep", "default", "manufacturing", "multi_company"]


def test_threshold_override_changes_manual_journal_result(sample_data_dir, tmp_path):
    config_path = tmp_path / "custom.yml"
    config_path.write_text(
        """
profile_name: custom
thresholds:
  manual_journal_threshold: 20000
enabled_checks:
  - FIN-010
""",
        encoding="utf-8",
    )

    data = load_csv_exports(sample_data_dir)
    exceptions = run_all_rules(data, load_audit_config(config_path=config_path))

    assert exceptions == []


def test_config_path_takes_priority_over_profile(tmp_path):
    config_path = tmp_path / "custom.yml"
    config_path.write_text(
        """
profile_name: explicit_config
thresholds:
  bank_line_age_days: 99
""",
        encoding="utf-8",
    )

    config = load_audit_config(config_path=config_path, profile="manufacturing")

    assert config.profile_name == "explicit_config"
    assert config.bank_line_age_days == 99


def test_audit_config_from_mapping_supports_partial_thresholds():
    config = audit_config_from_mapping({"thresholds": {"negative_inventory_tolerance": 10}}, source="unit")

    assert config.negative_inventory_tolerance == 10.0
    assert config.manual_journal_threshold == 10000.0

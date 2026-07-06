from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import POLICY_READINESS_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_policy_readiness_default_preserves_local_first_boundaries() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "policy", "readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_policy_readiness", payload)["ok"] is True
    assert payload["contract_version"] == "governance_policy_readiness.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["governance"]["team_enforcement_ready"] is False
    assert payload["governance"]["current_permissions_enforced"] is False
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["cloud_sync"] is False
    assert payload["readiness"]["overall_status"] == "not_ready_for_team_enforcement"
    assert payload["readiness"]["safe_to_keep_local_cli"] is True
    assert payload["readiness"]["safe_to_enable_team_enforcement"] is False
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["privacy_first"] is True
    assert payload["diagnostics"]["business_commands_instrumented"] is True
    assert payload["diagnostics"]["instrumented_command_count"] == 16
    assert payload["diagnostics"]["automatic_audit_now"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_policy_readiness_config_enabled_still_requires_missing_team_prerequisites(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(app, ["governance", "policy", "readiness", "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_policy_readiness", payload)["ok"] is True
    assert payload["governance"]["enabled"] is True
    assert payload["governance"]["mode"] == "local_opt_in"
    assert payload["governance"]["team_enforcement_ready"] is False
    assert payload["readiness"]["safe_to_enable_team_enforcement"] is False
    assert "server_identity_model" in payload["readiness"]["missing_prerequisites"]
    assert "central_policy_store" in payload["readiness"]["missing_prerequisites"]


def test_policy_readiness_lists_prerequisites_blockers_and_command_categories() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "policy", "readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "local_audit_log" in payload["readiness"]["implemented_prerequisites"]
    assert "permission_preflight" in payload["readiness"]["implemented_prerequisites"]
    assert "enforcement_gap_inventory" in payload["readiness"]["implemented_prerequisites"]
    assert "enforcement_dry_run" in payload["readiness"]["implemented_prerequisites"]
    assert "automatic_command_preflight" in payload["readiness"]["missing_prerequisites"]
    assert "automatic_command_audit" in payload["readiness"]["missing_prerequisites"]
    assert payload["readiness"]["blocking_count"] == len(payload["blockers"])
    blocker_codes = {item["code"] for item in payload["blockers"]}
    assert "server_identity_model_missing" in blocker_codes
    assert "business_command_instrumentation_missing" in blocker_codes
    categories = {item["name"]: item for item in payload["command_categories"]}
    assert "raw_transcript" in categories
    assert "export_backup" in categories
    assert "restore_retention" in categories
    assert "external_model" in categories
    assert categories["export_backup"]["automatic_preflight"] is False
    assert categories["export_backup"]["ready_for_team_enforcement"] is False
    assert "threadvault export" in categories["export_backup"]["commands"]


def test_policy_readiness_capabilities_reference_existing_governance_workflows() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "policy", "readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["capabilities"]["audit_log"]["implemented"] is True
    assert payload["capabilities"]["audit_log"]["centralized"] is False
    assert payload["capabilities"]["permission_preflight"]["implemented"] is True
    assert payload["capabilities"]["permission_preflight"]["automatic_for_business_commands"] is True
    assert len(payload["capabilities"]["permission_preflight"]["instrumented_commands"]) == 16
    assert "threadvault client export-preview" in payload["capabilities"]["permission_preflight"]["instrumented_commands"]
    assert "threadvault backup" in payload["capabilities"]["permission_preflight"]["instrumented_commands"]
    assert payload["capabilities"]["enforcement_gap_inventory"]["schema"] == "governance_enforcement_gaps"
    assert payload["capabilities"]["enforcement_dry_run"]["schema"] == "governance_enforcement_check"
    assert payload["diagnostics"]["inventory_command_count"] >= 16


def test_policy_readiness_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance policy readiness" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_policy_readiness"] is True

    guide = robot_guide()
    assert guide["governance"]["policy_readiness_contract_version"] == "governance_policy_readiness.v1"
    assert guide["governance"]["policy_readiness_schema"] == "governance_policy_readiness"
    assert POLICY_READINESS_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_policy_readiness" in schemas
    assert get_schema("governance_policy_readiness")["type"] == "object"
    assert Path("docs/schemas/governance_policy_readiness.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-12-governance-policy-readiness/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-12-governance-policy-readiness/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-12-governance-policy-readiness/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

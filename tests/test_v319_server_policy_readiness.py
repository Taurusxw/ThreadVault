from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import SERVER_POLICY_READINESS_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_server_policy_readiness_default_preserves_local_first_boundaries() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "server", "policy-readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_server_policy_readiness", payload)["ok"] is True
    assert payload["contract_version"] == "governance_server_policy_readiness.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["governance"]["team_enforcement_ready"] is False
    assert payload["governance"]["shared_enforcement_ready"] is False
    assert payload["governance"]["current_permissions_enforced"] is False
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_available"] is True
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["readiness"]["overall_status"] == "not_ready_for_shared_enforcement"
    assert payload["readiness"]["safe_to_keep_local_cli"] is True
    assert payload["readiness"]["safe_to_enable_server_mode"] is False
    assert payload["readiness"]["safe_to_enable_team_enforcement"] is False
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["privacy_first"] is True
    assert payload["diagnostics"]["server_required"] is False
    assert payload["diagnostics"]["business_commands_instrumented"] is True
    assert payload["diagnostics"]["instrumented_command_count"] == 16
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_server_policy_readiness_config_enabled_still_not_shared_ready(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(app, ["governance", "server", "policy-readiness", "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_server_policy_readiness", payload)["ok"] is True
    assert payload["governance"]["enabled"] is True
    assert payload["governance"]["mode"] == "local_opt_in"
    assert payload["governance"]["shared_enforcement_ready"] is False
    assert payload["server"]["implemented"] is True
    assert payload["server"]["read_only_shared_prototype_ready"] is True
    assert payload["server"]["required_for_local_cli"] is False
    assert payload["policy"]["central_store_implemented"] is True
    assert payload["policy"]["central_store_available"] is False
    assert payload["identity"]["identity_provider_implemented"] is True
    assert payload["identity"]["actor_binding_implemented"] is True
    assert payload["identity"]["sufficient_for_shared_enforcement"] is False
    assert payload["readiness"]["safe_to_enable_server_mode"] is False


def test_server_policy_readiness_lists_identity_policy_audit_backup_and_outbound_blockers() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "server", "policy-readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    blocker_codes = {item["code"] for item in payload["blockers"]}
    assert "identity_provider_missing" not in blocker_codes
    assert "actor_binding_missing" not in blocker_codes
    assert "role_mapping_missing" not in blocker_codes
    assert "central_policy_store_missing" not in blocker_codes
    assert "policy_versioning_missing" not in blocker_codes
    assert "automatic_command_instrumentation_missing" not in blocker_codes
    assert "centralized_audit_retention_missing" not in blocker_codes
    assert "centralized_backup_restore_policy_missing" not in blocker_codes
    assert "outbound_external_model_policy_missing" in blocker_codes
    assert payload["readiness"]["blocking_count"] == len(payload["blockers"])
    assert "configured_central_policy_document" in payload["policy"]["missing"]
    assert "authenticated_provider" in payload["identity"]["missing"]
    assert payload["instrumentation"]["preflight_contracts_available"] is True
    assert payload["instrumentation"]["automatic_business_preflight"] is True
    assert payload["audit"]["local_jsonl_available"] is True
    assert payload["audit"]["centralized_store_implemented"] is True
    assert payload["audit"]["centralized_store_available"] is False
    assert payload["audit"]["retention_policy_implemented"] is True
    assert payload["backup_restore"]["local_backup_restore_available"] is True
    assert payload["backup_restore"]["centralized_policy_implemented"] is True
    assert payload["backup_restore"]["centralized_policy_available"] is False
    assert payload["outbound_policy"]["external_model_preflight_available"] is True
    assert payload["outbound_policy"]["default_external_calls_enabled"] is False


def test_server_policy_readiness_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance server policy-readiness" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_server_policy_readiness"] is True

    guide = robot_guide()
    assert (
        guide["governance"]["server_policy_readiness_contract_version"]
        == "governance_server_policy_readiness.v1"
    )
    assert guide["governance"]["server_policy_readiness_schema"] == "governance_server_policy_readiness"
    assert SERVER_POLICY_READINESS_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_server_policy_readiness" in schemas
    assert get_schema("governance_server_policy_readiness")["type"] == "object"
    assert Path("docs/schemas/governance_server_policy_readiness.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-19-server-policy-readiness/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-19-server-policy-readiness/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-19-server-policy-readiness/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

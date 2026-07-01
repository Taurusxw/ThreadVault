from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import CENTRAL_BACKUP_READINESS_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_central_backup_readiness_default_preserves_local_first_boundaries() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "backup", "central-readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_central_backup_readiness", payload)["ok"] is True
    assert payload["contract_version"] == "governance_central_backup_readiness.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["governance"]["central_backup_ready"] is False
    assert payload["governance"]["shared_restore_ready"] is False
    assert payload["governance"]["team_enforcement_ready"] is False
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["readiness"]["overall_status"] == "not_ready_for_centralized_backup_restore_policy"
    assert payload["readiness"]["safe_to_keep_local_cli"] is True
    assert payload["readiness"]["safe_to_use_local_backup_restore"] is True
    assert payload["readiness"]["safe_to_enable_central_backup"] is False
    assert payload["readiness"]["safe_to_enable_shared_restore"] is False
    assert payload["local_backup"]["backup_command_available"] is True
    assert payload["local_backup"]["restore_command_available"] is True
    assert payload["local_backup"]["sufficient_for_local_use"] is True
    assert payload["local_backup"]["sufficient_for_shared_policy"] is False
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["privacy_first"] is True
    assert payload["diagnostics"]["server_required"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_central_backup_readiness_config_enabled_still_not_central_ready(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["governance", "backup", "central-readiness", "--config", str(config), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_central_backup_readiness", payload)["ok"] is True
    assert payload["governance"]["enabled"] is True
    assert payload["governance"]["mode"] == "local_opt_in"
    assert payload["governance"]["central_backup_ready"] is False
    assert payload["central_backup"]["repository_implemented"] is True
    assert payload["central_backup"]["repository_available"] is False
    assert payload["policy"]["backup_policy_implemented"] is True
    assert payload["policy"]["policy_valid"] is False
    assert payload["restore"]["approval_workflow_implemented"] is True
    assert payload["retention"]["legal_hold_implemented"] is True
    assert payload["audit"]["authenticated_actor_provenance"] is False
    assert payload["dependencies"]["central_policy_ready"] is False
    assert payload["recovery_testing"]["shared_restore_smoke_available"] is False


def test_central_backup_readiness_lists_shared_backup_blockers_and_invariants() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "backup", "central-readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    blocker_codes = {item["code"] for item in payload["blockers"]}
    assert "central_backup_policy_not_configured" in blocker_codes
    assert "centralized_audit_store_not_ready" in blocker_codes
    assert "identity_dependency_missing" not in blocker_codes
    assert "central_policy_dependency_missing" not in blocker_codes
    assert payload["readiness"]["blocking_count"] == len(payload["blockers"])
    assert "local_backup_command" in payload["readiness"]["implemented_prerequisites"]
    assert "central_policy_readiness_manifest" in payload["readiness"]["implemented_prerequisites"]
    assert "central_policy_store_runtime" in payload["readiness"]["implemented_prerequisites"]
    assert "central_backup_policy_runtime" in payload["readiness"]["implemented_prerequisites"]
    assert "configured_central_backup_policy" in payload["central_backup"]["missing"]
    assert "configured_central_backup_policy" in payload["policy"]["missing"]
    assert "configured_central_backup_policy" in payload["restore"]["missing"]
    assert "configured_central_backup_policy" in payload["retention"]["missing"]
    assert "authenticated_actor_provenance" in payload["audit"]["missing"]
    assert payload["dependencies"]["identity_binding_ready"] is True
    assert "authenticated_actor_provenance" in payload["dependencies"]["missing"]
    assert "shared_restore_smoke" in payload["recovery_testing"]["missing"]
    assert payload["diagnostics"]["business_commands_instrumented"] is False
    assert payload["diagnostics"]["automatic_backup_policy_enforcement"] is False


def test_central_backup_readiness_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance backup central-readiness" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_central_backup_readiness"] is True

    guide = robot_guide()
    assert guide["governance"]["central_backup_readiness_contract_version"] == "governance_central_backup_readiness.v1"
    assert guide["governance"]["central_backup_readiness_schema"] == "governance_central_backup_readiness"
    assert CENTRAL_BACKUP_READINESS_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_central_backup_readiness" in schemas
    assert get_schema("governance_central_backup_readiness")["type"] == "object"
    assert Path("docs/schemas/governance_central_backup_readiness.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-24-centralized-backup-restore-policy-readiness/plan.md"),
        Path("docs/v3/phases/phase-24-centralized-backup-restore-policy-readiness/design-notes.md"),
        Path("docs/v3/phases/phase-24-centralized-backup-restore-policy-readiness/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

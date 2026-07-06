from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import CENTRALIZED_AUDIT_READINESS_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_centralized_audit_readiness_default_preserves_local_first_boundaries() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "audit", "centralized-readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_centralized_audit_readiness", payload)["ok"] is True
    assert payload["contract_version"] == "governance_centralized_audit_readiness.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["governance"]["centralized_audit_ready"] is False
    assert payload["readiness"]["overall_status"] == "not_ready_for_centralized_audit"
    assert payload["readiness"]["safe_to_keep_local_jsonl_audit"] is True
    assert payload["readiness"]["safe_to_enable_centralized_audit"] is False
    assert payload["readiness"]["safe_to_enable_shared_audit_retention"] is False
    assert payload["local_audit"]["available"] is True
    assert payload["local_audit"]["local_only"] is True
    assert payload["local_audit"]["server_required"] is False
    assert payload["centralized_audit"]["store_implemented"] is True
    assert payload["centralized_audit"]["store_available"] is False
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["privacy_first"] is True
    assert payload["diagnostics"]["server_required"] is False
    assert payload["diagnostics"]["cloud_sync"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_centralized_audit_readiness_config_enabled_still_not_centralized_ready(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["governance", "audit", "centralized-readiness", "--config", str(config), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_centralized_audit_readiness", payload)["ok"] is True
    assert payload["governance"]["enabled"] is True
    assert payload["governance"]["mode"] == "local_opt_in"
    assert payload["governance"]["centralized_audit_ready"] is False
    assert payload["centralized_audit"]["adapter_implemented"] is True
    assert payload["identity"]["actor_binding_implemented"] is True
    assert payload["identity"]["authenticated_actor_provenance"] is False
    assert payload["retention"]["policy_implemented"] is True
    assert payload["retention"]["policy_available"] is False
    assert payload["review"]["query_workflow_implemented"] is True
    assert payload["backup_export"]["backup_policy_implemented"] is True
    assert payload["backup_export"]["policy_available"] is False
    assert payload["instrumentation"]["automatic_business_audit"] is False


def test_centralized_audit_readiness_lists_required_blockers_and_invariants() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "audit", "centralized-readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    blocker_codes = {item["code"] for item in payload["blockers"]}
    assert "centralized_audit_store_missing" not in blocker_codes
    assert "centralized_audit_store_not_configured" in blocker_codes
    assert "actor_binding_missing" not in blocker_codes
    assert "append_only_integrity_missing" not in blocker_codes
    assert "audit_retention_policy_missing" not in blocker_codes
    assert "audit_review_workflow_missing" not in blocker_codes
    assert "audit_backup_export_policy_missing" not in blocker_codes
    assert "automatic_audit_instrumentation_missing" not in blocker_codes
    assert payload["readiness"]["blocking_count"] == len(payload["blockers"])
    assert "local_audit_log" in payload["readiness"]["implemented_prerequisites"]
    assert "centralized_audit_store_runtime" in payload["readiness"]["implemented_prerequisites"]
    assert "central_backup_policy_runtime" in payload["readiness"]["implemented_prerequisites"]
    assert "configured_centralized_audit_store" in payload["centralized_audit"]["missing"]
    assert "authenticated_actor_provenance" in payload["identity"]["missing"]
    assert "configured_central_backup_policy" in payload["retention"]["missing"]
    assert payload["integrity"]["append_only_contract_available"] is True
    assert payload["integrity"]["tamper_evidence_implemented"] is True
    assert payload["integrity"]["record_hashing_implemented"] is True
    assert payload["instrumentation"]["manual_audit_append_available"] is True
    assert payload["instrumentation"]["instrumented_command_count"] == 16
    assert payload["instrumentation"]["automatic_preflight_audit"] is True
    assert payload["diagnostics"]["business_commands_instrumented"] is True
    assert payload["diagnostics"]["instrumented_command_count"] == 16
    assert payload["diagnostics"]["automatic_audit_now"] is True


def test_centralized_audit_readiness_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance audit centralized-readiness" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_centralized_audit_readiness"] is True

    guide = robot_guide()
    assert (
        guide["governance"]["centralized_audit_readiness_contract_version"]
        == "governance_centralized_audit_readiness.v1"
    )
    assert guide["governance"]["centralized_audit_readiness_schema"] == "governance_centralized_audit_readiness"
    assert CENTRALIZED_AUDIT_READINESS_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_centralized_audit_readiness" in schemas
    assert get_schema("governance_centralized_audit_readiness")["type"] == "object"
    assert Path("docs/schemas/governance_centralized_audit_readiness.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-20-centralized-audit-retention-readiness/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-20-centralized-audit-retention-readiness/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-20-centralized-audit-retention-readiness/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

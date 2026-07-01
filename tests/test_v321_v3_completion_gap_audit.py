from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import V3_COMPLETION_GAP_AUDIT_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_v3_completion_gap_audit_reports_complete_and_preserves_defaults() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "v3", "gap-audit", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_v3_completion_gap_audit", payload)["ok"] is True
    assert payload["contract_version"] == "governance_v3_completion_gap_audit.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["completion"]["overall_status"] == "complete"
    assert payload["completion"]["v3_complete"] is True
    assert payload["completion"]["accepted_phase_count"] == 33
    assert payload["completion"]["current_phase"] == "phase-33-v3-final-acceptance-smoke"
    assert payload["completion"]["safe_to_keep_local_cli"] is True
    assert payload["completion"]["safe_to_claim_shared_deployment_ready"] is False
    assert payload["completion"]["safe_to_run_final_v3_acceptance"] is True
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["privacy_first"] is True
    assert payload["diagnostics"]["server_required"] is False
    assert payload["diagnostics"]["v2_retrieval_accepted"] is True
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_v3_completion_gap_audit_maps_roadmap_acceptance_criteria() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "v3", "gap-audit", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    criteria = {item["code"]: item for item in payload["acceptance_criteria"]}
    assert criteria["local_cli_without_server"]["status"] == "satisfied"
    assert criteria["richer_client_browse_search_export"]["status"] == "satisfied"
    assert criteria["shared_access_separation"]["status"] == "satisfied"
    assert criteria["audit_records_for_sensitive_operations"]["status"] == "satisfied"
    assert criteria["external_model_cloud_explicit"]["status"] == "satisfied"
    assert "client_export_preview" in criteria["richer_client_browse_search_export"]["evidence"]
    assert "client_tui_runtime" in criteria["richer_client_browse_search_export"]["evidence"]
    assert "server_policy_readiness_manifest" in criteria["shared_access_separation"]["evidence"]
    assert "read_only_shared_server_prototype" in criteria["shared_access_separation"]["evidence"]

    milestones = {item["version"]: item for item in payload["milestones"]}
    assert milestones["v3.0"]["status"] == "accepted"
    assert milestones["v3.1"]["status"] == "accepted"
    assert milestones["v3.2"]["status"] == "accepted"
    assert milestones["v3.3"]["status"] == "partial"
    assert milestones["v3.4"]["status"] == "partial"
    assert milestones["v3.5"]["status"] == "accepted"
    assert milestones["v3.6"]["status"] == "accepted"


def test_v3_completion_gap_audit_lists_completion_blockers_and_next_steps() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "v3", "gap-audit", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    blocker_codes = {item["code"] for item in payload["blockers"]}
    assert "richer_client_runtime_not_accepted" not in blocker_codes
    assert "optional_shared_server_runtime_missing" not in blocker_codes
    assert "identity_actor_binding_missing" not in blocker_codes
    assert "central_policy_store_missing" not in blocker_codes
    assert "centralized_audit_store_missing" not in blocker_codes
    assert "centralized_backup_restore_policy_missing" not in blocker_codes
    assert "automatic_governance_instrumentation_missing" not in blocker_codes
    assert "automatic_governance_instrumentation_incomplete" not in blocker_codes
    assert "v3_acceptance_smoke_missing" not in blocker_codes
    assert payload["completion"]["blocking_count"] == len(payload["blockers"])
    assert payload["completion"]["remaining_gap_count"] == len(payload["remaining_gaps"])
    assert "accepted_v2_retrieval_interfaces" in payload["implemented_capabilities"]
    assert "centralized_audit_readiness" in payload["implemented_capabilities"]
    assert "read_only_shared_server_prototype" in payload["implemented_capabilities"]
    assert "client_tui_runtime" in payload["implemented_capabilities"]
    assert "identity_actor_binding_runtime" in payload["implemented_capabilities"]
    assert "central_policy_store_runtime" in payload["implemented_capabilities"]
    assert "centralized_audit_store_runtime" in payload["implemented_capabilities"]
    assert "central_backup_policy_runtime" in payload["implemented_capabilities"]
    assert "v3_acceptance_smoke" in payload["implemented_capabilities"]
    assert "client_export_preview_governance_instrumentation" in payload["implemented_capabilities"]
    gap_codes = {item["code"] for item in payload["remaining_gaps"]}
    assert "shared_read_only_deployment" in gap_codes
    gaps = {item["code"]: item for item in payload["remaining_gaps"]}
    assert gaps["richer_client_runtime"]["status"] == "accepted_minimal_tui_runtime"
    assert gaps["shared_read_only_deployment"]["status"] == "prototype_accepted"
    assert gaps["team_identity_and_policy"]["status"] == "identity_and_policy_store_accepted_enforcement_pending"
    assert gaps["centralized_audit_and_retention"]["status"] == "store_policy_and_instrumentation_accepted"
    assert gaps["centralized_backup_restore_policy"]["status"] == "accepted_local_policy_runtime"
    assert gaps["automatic_instrumentation"]["status"] == "accepted_broad_command_instrumentation"
    assert gaps["v3_acceptance_smoke"]["status"] == "accepted"
    assert "team_identity_and_policy" in gap_codes
    assert "v3_acceptance_smoke" in gap_codes


def test_v3_completion_gap_audit_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance v3 gap-audit" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_v3_completion_gap_audit"] is True

    guide = robot_guide()
    assert guide["governance"]["v3_completion_gap_audit_contract_version"] == "governance_v3_completion_gap_audit.v1"
    assert guide["governance"]["v3_completion_gap_audit_schema"] == "governance_v3_completion_gap_audit"
    assert V3_COMPLETION_GAP_AUDIT_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_v3_completion_gap_audit" in schemas
    assert get_schema("governance_v3_completion_gap_audit")["type"] == "object"
    assert Path("docs/schemas/governance_v3_completion_gap_audit.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-21-v3-completion-gap-audit/plan.md"),
        Path("docs/v3/phases/phase-21-v3-completion-gap-audit/design-notes.md"),
        Path("docs/v3/phases/phase-21-v3-completion-gap-audit/gap-audit.md"),
        Path("docs/v3/phases/phase-21-v3-completion-gap-audit/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

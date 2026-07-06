from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import IDENTITY_ACTOR_READINESS_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_identity_actor_readiness_default_preserves_local_first_boundaries() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "identity", "actor-readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_identity_actor_readiness", payload)["ok"] is True
    assert payload["contract_version"] == "governance_identity_actor_readiness.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["governance"]["team_enforcement_ready"] is False
    assert payload["governance"]["identity_binding_ready"] is False
    assert payload["governance"]["current_permissions_enforced"] is False
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["readiness"]["overall_status"] == "not_ready_for_identity_binding"
    assert payload["readiness"]["safe_to_keep_local_cli"] is True
    assert payload["readiness"]["safe_to_use_manual_local_actor_labels"] is True
    assert payload["readiness"]["safe_to_enable_shared_identity_binding"] is False
    assert payload["readiness"]["safe_to_enable_team_enforcement"] is False
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["privacy_first"] is True
    assert payload["diagnostics"]["server_required"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_identity_actor_readiness_config_enabled_still_not_actor_ready(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text(
        """
[governance]
enabled = true

[governance.identity]
actors = [
  { id = "reviewer@example", roles = ["reviewer"] },
]
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["governance", "identity", "actor-readiness", "--config", str(config), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_identity_actor_readiness", payload)["ok"] is True
    assert payload["governance"]["enabled"] is True
    assert payload["governance"]["mode"] == "local_opt_in"
    assert payload["governance"]["identity_binding_ready"] is True
    assert payload["identity_provider"]["implemented"] is True
    assert payload["identity_provider"]["configured_actor_count"] == 1
    assert payload["actor_binding"]["implemented"] is True
    assert payload["role_mapping"]["team_role_mapping_implemented"] is True
    assert payload["request_attribution"]["implemented"] is True
    assert payload["audit_provenance"]["authenticated_actor_provenance"] is False
    assert payload["local_fallback"]["sufficient_for_shared_enforcement"] is False


def test_identity_actor_readiness_lists_identity_binding_blockers_and_invariants() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "identity", "actor-readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    blocker_codes = {item["code"] for item in payload["blockers"]}
    assert "authenticated_identity_provider_missing" in blocker_codes
    assert "centralized_actor_provenance_missing" in blocker_codes
    assert "shared_request_context_missing" in blocker_codes
    assert "actor_binding_missing" not in blocker_codes
    assert payload["readiness"]["blocking_count"] == len(payload["blockers"])
    assert "manual_local_actor_labels" in payload["readiness"]["implemented_prerequisites"]
    assert "authenticated_provider" in payload["identity_provider"]["missing"]
    assert "automatic_command_actor_binding" in payload["actor_binding"]["missing"]
    assert "central_policy_role_resolution" in payload["role_mapping"]["missing"]
    assert "authenticated_actor_provenance" in payload["audit_provenance"]["missing"]
    assert payload["role_mapping"]["local_role_vocabulary_available"] is True
    assert payload["audit_provenance"]["manual_actor_field_available"] is True
    assert payload["local_fallback"]["manual_actor_labels_available"] is True
    assert payload["diagnostics"]["business_commands_instrumented"] is False
    assert payload["diagnostics"]["automatic_audit_now"] is False


def test_identity_actor_readiness_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance identity actor-readiness" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_identity_actor_readiness"] is True

    guide = robot_guide()
    assert guide["governance"]["identity_actor_readiness_contract_version"] == "governance_identity_actor_readiness.v1"
    assert guide["governance"]["identity_actor_readiness_schema"] == "governance_identity_actor_readiness"
    assert IDENTITY_ACTOR_READINESS_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_identity_actor_readiness" in schemas
    assert get_schema("governance_identity_actor_readiness")["type"] == "object"
    assert Path("docs/schemas/governance_identity_actor_readiness.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-22-identity-actor-binding-readiness/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-22-identity-actor-binding-readiness/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-22-identity-actor-binding-readiness/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

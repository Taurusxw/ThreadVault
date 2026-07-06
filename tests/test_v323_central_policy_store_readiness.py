from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import CENTRAL_POLICY_READINESS_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_central_policy_readiness_default_preserves_local_first_boundaries() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "policy", "central-readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_central_policy_readiness", payload)["ok"] is True
    assert payload["contract_version"] == "governance_central_policy_readiness.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["governance"]["central_policy_ready"] is False
    assert payload["governance"]["team_enforcement_ready"] is False
    assert payload["governance"]["current_permissions_enforced"] is False
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["readiness"]["overall_status"] == "not_ready_for_central_policy_store"
    assert payload["readiness"]["safe_to_keep_local_cli"] is True
    assert payload["readiness"]["safe_to_use_local_static_policy"] is True
    assert payload["readiness"]["safe_to_enable_central_policy_store"] is False
    assert payload["readiness"]["safe_to_enable_team_enforcement"] is False
    assert payload["local_policy"]["role_vocabulary_available"] is True
    assert payload["local_policy"]["sufficient_for_local_preflight"] is True
    assert payload["local_policy"]["sufficient_for_shared_enforcement"] is False
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["privacy_first"] is True
    assert payload["diagnostics"]["server_required"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_central_policy_readiness_config_enabled_still_not_central_ready(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["governance", "policy", "central-readiness", "--config", str(config), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_central_policy_readiness", payload)["ok"] is True
    assert payload["governance"]["enabled"] is True
    assert payload["governance"]["mode"] == "local_opt_in"
    assert payload["governance"]["central_policy_ready"] is False
    assert payload["central_policy"]["store_implemented"] is True
    assert payload["central_policy"]["store_available"] is False
    assert payload["adapter"]["interface_defined"] is True
    assert payload["adapter"]["local_adapter_implemented"] is True
    assert payload["versioning"]["policy_versioning_implemented"] is True
    assert payload["provenance"]["review_recorded"] is False
    assert payload["migration"]["rollback_implemented"] is False
    assert payload["identity_dependency"]["identity_binding_ready"] is True
    assert payload["identity_dependency"]["role_mapping_ready"] is True
    assert payload["identity_dependency"]["actor_policy_resolution_ready"] is False


def test_central_policy_readiness_lists_policy_blockers_and_invariants() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "policy", "central-readiness", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    blocker_codes = {item["code"] for item in payload["blockers"]}
    assert "central_policy_store_missing" not in blocker_codes
    assert "central_policy_document_missing" in blocker_codes
    assert "policy_adapter_missing" not in blocker_codes
    assert "policy_versioning_missing" not in blocker_codes
    assert "policy_provenance_missing" not in blocker_codes
    assert "policy_migration_missing" not in blocker_codes
    assert "policy_rollback_missing" not in blocker_codes
    assert "identity_actor_dependency_missing" not in blocker_codes
    assert "automatic_policy_enforcement_missing" not in blocker_codes
    assert payload["readiness"]["blocking_count"] == len(payload["blockers"])
    assert "local_governance_role_vocabulary" in payload["readiness"]["implemented_prerequisites"]
    assert "identity_actor_readiness_manifest" in payload["readiness"]["implemented_prerequisites"]
    assert "identity_actor_binding_runtime" in payload["readiness"]["implemented_prerequisites"]
    assert "central_policy_store_runtime" in payload["readiness"]["implemented_prerequisites"]
    assert "central_policy_document" in payload["central_policy"]["missing"]
    assert "server_policy_adapter" in payload["adapter"]["missing"]
    assert "configured_policy_version" in payload["versioning"]["missing"]
    assert "configured_policy_provenance" in payload["provenance"]["missing"]
    assert "policy_rollback" in payload["migration"]["missing"]
    assert payload["identity_dependency"]["identity_actor_readiness_available"] is True
    assert payload["fallback"]["central_policy_required_for_local_cli"] is False
    assert payload["fallback"]["central_policy_required_for_shared_enforcement"] is True
    assert payload["diagnostics"]["business_commands_instrumented"] is False
    assert payload["diagnostics"]["automatic_policy_enforcement"] is False


def test_central_policy_readiness_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance policy central-readiness" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_central_policy_readiness"] is True

    guide = robot_guide()
    assert guide["governance"]["central_policy_readiness_contract_version"] == "governance_central_policy_readiness.v1"
    assert guide["governance"]["central_policy_readiness_schema"] == "governance_central_policy_readiness"
    assert CENTRAL_POLICY_READINESS_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_central_policy_readiness" in schemas
    assert get_schema("governance_central_policy_readiness")["type"] == "object"
    assert Path("docs/schemas/governance_central_policy_readiness.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-23-centralized-policy-store-readiness/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-23-centralized-policy-store-readiness/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-23-centralized-policy-store-readiness/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

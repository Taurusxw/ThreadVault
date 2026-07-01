from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import ArchiveStore, capabilities, robot_guide, robot_schemas


def write_identity_config(path: Path, roles: str = '"reviewer"') -> None:
    path.write_text(
        f"""
[governance]
enabled = true

[governance.identity]
actors = [
  {{ id = "reviewer@example", display = "Reviewer", roles = [{roles}], source = "local-static" }},
]
""",
        encoding="utf-8",
    )


def test_identity_actor_binding_missing_config_is_unbound_and_local_first() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "identity", "bind", "--actor", "reviewer@example", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_identity_actor_binding", payload)["ok"] is True
    assert payload["contract_version"] == "governance_identity_actor_binding.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["governance"]["identity_binding_ready"] is False
    assert payload["governance"]["server_required"] is False
    assert payload["identity_provider"]["implemented"] is False
    assert payload["actor"]["configured"] is False
    assert payload["binding"]["bound"] is False
    assert payload["binding"]["failure_reason"] == "actor_not_configured"
    assert payload["binding"]["sufficient_for_shared_enforcement"] is False
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_identity_actor_binding_resolves_configured_actor_roles(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    write_identity_config(config)

    result = runner.invoke(
        app,
        [
            "governance",
            "identity",
            "bind",
            "--config",
            str(config),
            "--actor",
            "reviewer@example",
            "--command",
            "threadvault client export-preview",
            "--operation",
            "export_archive",
            "--target-type",
            "session",
            "--target-id",
            "sess-current",
            "--client-id",
            "threadvault-local-tui",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_identity_actor_binding", payload)["ok"] is True
    assert payload["governance"]["enabled"] is True
    assert payload["governance"]["identity_binding_ready"] is True
    assert payload["identity_provider"]["implemented"] is True
    assert payload["actor"]["configured"] is True
    assert payload["actor"]["display"] == "Reviewer"
    assert payload["binding"]["bound"] is True
    assert payload["binding"]["status"] == "bound"
    assert payload["role_mapping"]["roles"] == ["reviewer"]
    assert payload["role_mapping"]["invalid_roles"] == []
    assert payload["request_attribution"]["command"] == "threadvault client export-preview"
    assert payload["request_attribution"]["operation"] == "export_archive"
    assert payload["request_attribution"]["target"] == {"type": "session", "id": "sess-current"}
    assert payload["request_attribution"]["client_id"] == "threadvault-local-tui"


def test_identity_actor_binding_unknown_actor_does_not_grant_roles(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    write_identity_config(config)

    result = runner.invoke(
        app,
        ["governance", "identity", "bind", "--config", str(config), "--actor", "unknown@example", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_identity_actor_binding", payload)["ok"] is True
    assert payload["binding"]["bound"] is False
    assert payload["binding"]["failure_reason"] == "actor_not_configured"
    assert payload["role_mapping"]["roles"] == []


def test_identity_actor_binding_reports_invalid_configured_role(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    write_identity_config(config, roles='"reviewer", "not-a-role"')

    result = runner.invoke(
        app,
        ["governance", "identity", "bind", "--config", str(config), "--actor", "reviewer@example", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_identity_actor_binding", payload)["ok"] is True
    assert payload["binding"]["bound"] is False
    assert payload["binding"]["status"] == "invalid_role_mapping"
    assert payload["binding"]["failure_reason"] == "invalid_role_mapping"
    assert payload["role_mapping"]["roles"] == ["reviewer"]
    assert payload["role_mapping"]["invalid_roles"] == ["not-a-role"]


def test_identity_actor_binding_can_write_audit_record(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    log = tmp_path / "audit.jsonl"
    write_identity_config(config)

    result = runner.invoke(
        app,
        [
            "governance",
            "identity",
            "bind",
            "--config",
            str(config),
            "--actor",
            "reviewer@example",
            "--command",
            "threadvault client export-preview",
            "--operation",
            "export_archive",
            "--target-type",
            "session",
            "--target-id",
            "sess-current",
            "--audit-log",
            str(log),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_identity_actor_binding", payload)["ok"] is True
    assert payload["audit"]["written"] is True
    assert payload["audit"]["record"]["operation"] == "identity_actor_binding"
    assert payload["audit"]["record"]["actor"] == "reviewer@example"
    assert payload["audit"]["record"]["status"] == "bound"
    assert payload["audit"]["record"]["metadata"]["roles"] == "reviewer"
    assert payload["audit"]["record"]["metadata"]["command"] == "threadvault client export-preview"
    assert log.exists()

    list_result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])
    assert list_result.exit_code == 0, list_result.output
    listed = json.loads(list_result.output)
    assert listed["records"][0]["operation"] == "identity_actor_binding"


def test_identity_actor_binding_discovery_docs_and_gap_audit() -> None:
    caps = capabilities()
    assert "governance identity bind" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_identity_actor_binding"] is True

    guide = robot_guide()
    assert guide["governance"]["identity_actor_binding_contract_version"] == "governance_identity_actor_binding.v1"
    assert guide["governance"]["identity_actor_binding_schema"] == "governance_identity_actor_binding"
    assert "threadvault governance identity bind --actor ACTOR --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_identity_actor_binding" in schemas
    assert get_schema("governance_identity_actor_binding")["type"] == "object"
    assert Path("docs/schemas/governance_identity_actor_binding.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-28-identity-actor-binding-runtime/plan.md"),
        Path("docs/v3/phases/phase-28-identity-actor-binding-runtime/design-notes.md"),
        Path("docs/v3/phases/phase-28-identity-actor-binding-runtime/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

    gap = ArchiveStore(Path("unused.db")).governance_v3_completion_gap_audit()
    blocker_codes = {item["code"] for item in gap["blockers"]}
    gaps = {item["code"]: item for item in gap["remaining_gaps"]}
    assert "identity_actor_binding_missing" not in blocker_codes
    assert "identity_actor_binding_runtime" in gap["implemented_capabilities"]
    assert gaps["team_identity_and_policy"]["status"] == "identity_and_policy_store_accepted_enforcement_pending"
    assert gap["completion"]["accepted_phase_count"] == 33
    assert gap["completion"]["current_phase"] == "phase-33-v3-final-acceptance-smoke"
    assert gap["completion"]["v3_complete"] is True

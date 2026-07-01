from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import RESTORE_RETENTION_PREFLIGHT_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_restore_retention_preflight_maintainer_restore_would_allow_without_side_effects() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "restore-retention",
            "--command",
            "threadvault restore",
            "--role",
            "maintainer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_restore_retention_preflight", payload)["ok"] is True
    assert payload["contract_version"] == "governance_restore_retention_preflight.v1"
    assert payload["scope"]["in_scope"] is True
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "restore_backup"
    assert payload["command_policy"]["access_level"] == "restore"
    assert payload["permission"]["would_allow"] is True
    assert payload["enforcement"]["preflight_status"] == "would_allow"
    assert payload["recovery"]["restore_plan_expected_before_execution"] is True
    assert payload["recovery"]["pre_restore_backup_expected"] is True
    assert payload["recovery"]["manual_confirmation_expected"] is True
    assert payload["audit"]["required_before_execution"] is True
    assert payload["audit"]["automatic_audit_now"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["restore_applied"] is False
    assert payload["execution"]["retention_applied"] is False
    assert payload["execution"]["files_deleted"] is False
    assert payload["execution"]["history_rewritten"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_restore_retention_preflight_reader_prune_would_block_if_enforced() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "restore-retention",
            "--command",
            "threadvault audit-history prune",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_restore_retention_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is True
    assert payload["command_policy"]["operation"] == "delete_or_prune"
    assert payload["permission"]["would_allow"] is False
    assert payload["enforcement"]["would_block_if_enforced"] is True
    assert payload["enforcement"]["preflight_status"] == "would_block"
    assert payload["recovery"]["retention_policy_expected"] is True
    assert payload["execution"]["files_deleted"] is False


def test_restore_retention_preflight_config_enabled_reports_governance_but_still_no_execution(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "restore-retention",
            "--config",
            str(config),
            "--command",
            "threadvault backup-history prune",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_restore_retention_preflight", payload)["ok"] is True
    assert payload["diagnostics"]["governance_enabled"] is True
    assert payload["permission"]["enforced"] is True
    assert payload["permission"]["allowed"] is False
    assert payload["enforcement"]["current_enforced"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["retention_applied"] is False
    assert payload["execution"]["history_rewritten"] is False


def test_restore_retention_preflight_out_of_scope_command_is_structured() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "restore-retention",
            "--command",
            "threadvault export",
            "--role",
            "reviewer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_restore_retention_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is False
    assert payload["scope"]["reason"] == "out_of_scope_command"
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "export_archive"
    assert payload["enforcement"]["preflight_status"] == "out_of_scope"
    assert payload["enforcement"]["out_of_scope"] is True
    assert payload["execution"]["business_command_executed"] is False


def test_restore_retention_preflight_can_write_audit_record_for_preflight_only(tmp_path: Path) -> None:
    runner = CliRunner()
    log = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "restore-retention",
            "--command",
            "threadvault restore-history prune",
            "--role",
            "reader",
            "--audit-log",
            str(log),
            "--actor",
            "reader@example",
            "--target-type",
            "history",
            "--target-id",
            "restore-history",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_restore_retention_preflight", payload)["ok"] is True
    assert payload["audit"]["preflight_record_written"] is True
    assert payload["audit"]["record"]["operation"] == "restore_retention_preflight"
    assert payload["audit"]["record"]["status"] == "would_block"
    assert payload["audit"]["record"]["metadata"]["checked_command"] == "threadvault restore-history prune"
    assert payload["audit"]["record"]["metadata"]["business_command_executed"] == "false"
    assert payload["execution"]["files_deleted"] is False
    assert log.exists()

    list_result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])
    assert list_result.exit_code == 0, list_result.output
    listed = json.loads(list_result.output)
    assert listed["records"][0]["operation"] == "restore_retention_preflight"


def test_restore_retention_preflight_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance preflight restore-retention" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_restore_retention_preflight"] is True

    guide = robot_guide()
    assert (
        guide["governance"]["restore_retention_preflight_contract_version"]
        == "governance_restore_retention_preflight.v1"
    )
    assert guide["governance"]["restore_retention_preflight_schema"] == "governance_restore_retention_preflight"
    assert RESTORE_RETENTION_PREFLIGHT_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_restore_retention_preflight" in schemas
    assert get_schema("governance_restore_retention_preflight")["type"] == "object"
    assert Path("docs/schemas/governance_restore_retention_preflight.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-14-restore-retention-governance-preflight/plan.md"),
        Path("docs/v3/phases/phase-14-restore-retention-governance-preflight/design-notes.md"),
        Path("docs/v3/phases/phase-14-restore-retention-governance-preflight/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

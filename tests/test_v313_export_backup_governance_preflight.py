from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import EXPORT_BACKUP_PREFLIGHT_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_export_backup_preflight_reviewer_export_would_allow_without_side_effects() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "export-backup",
            "--command",
            "threadvault export",
            "--role",
            "reviewer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_export_backup_preflight", payload)["ok"] is True
    assert payload["contract_version"] == "governance_export_backup_preflight.v1"
    assert payload["scope"]["in_scope"] is True
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "export_archive"
    assert payload["permission"]["would_allow"] is True
    assert payload["enforcement"]["preflight_status"] == "would_allow"
    assert payload["privacy"]["privacy_scan_expected_before_execution"] is True
    assert payload["privacy"]["redaction_or_fail_policy_required_for_shared_export"] is True
    assert payload["audit"]["required_before_execution"] is True
    assert payload["audit"]["automatic_audit_now"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["files_written"] is False
    assert payload["execution"]["backup_created"] is False
    assert payload["execution"]["server_required"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_export_backup_preflight_reader_backup_would_block_if_enforced() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "export-backup",
            "--command",
            "threadvault backup",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_export_backup_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is True
    assert payload["permission"]["would_allow"] is False
    assert payload["enforcement"]["would_block_if_enforced"] is True
    assert payload["enforcement"]["preflight_status"] == "would_block"
    assert "role_would_be_blocked" in payload["enforcement"]["reasons"]
    assert payload["execution"]["backup_created"] is False


def test_export_backup_preflight_config_enabled_reports_governance_but_still_no_execution(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "export-backup",
            "--config",
            str(config),
            "--command",
            "threadvault export-target skill",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_export_backup_preflight", payload)["ok"] is True
    assert payload["diagnostics"]["governance_enabled"] is True
    assert payload["permission"]["enforced"] is True
    assert payload["permission"]["allowed"] is False
    assert payload["enforcement"]["current_enforced"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["files_written"] is False


def test_export_backup_preflight_out_of_scope_command_is_structured() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "export-backup",
            "--command",
            "threadvault restore",
            "--role",
            "maintainer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_export_backup_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is False
    assert payload["scope"]["reason"] == "out_of_scope_command"
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "restore_backup"
    assert payload["enforcement"]["preflight_status"] == "out_of_scope"
    assert payload["enforcement"]["out_of_scope"] is True
    assert payload["execution"]["business_command_executed"] is False


def test_export_backup_preflight_can_write_audit_record_for_preflight_only(tmp_path: Path) -> None:
    runner = CliRunner()
    log = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "export-backup",
            "--command",
            "threadvault backup",
            "--role",
            "reader",
            "--audit-log",
            str(log),
            "--actor",
            "reader@example",
            "--target-type",
            "backup",
            "--target-id",
            "backup-1",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_export_backup_preflight", payload)["ok"] is True
    assert payload["audit"]["preflight_record_written"] is True
    assert payload["audit"]["record"]["operation"] == "export_backup_preflight"
    assert payload["audit"]["record"]["status"] == "would_block"
    assert payload["audit"]["record"]["metadata"]["checked_command"] == "threadvault backup"
    assert payload["audit"]["record"]["metadata"]["business_command_executed"] == "false"
    assert payload["execution"]["backup_created"] is False
    assert log.exists()

    list_result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])
    assert list_result.exit_code == 0, list_result.output
    listed = json.loads(list_result.output)
    assert listed["records"][0]["operation"] == "export_backup_preflight"


def test_export_backup_preflight_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance preflight export-backup" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_export_backup_preflight"] is True

    guide = robot_guide()
    assert guide["governance"]["export_backup_preflight_contract_version"] == "governance_export_backup_preflight.v1"
    assert guide["governance"]["export_backup_preflight_schema"] == "governance_export_backup_preflight"
    assert EXPORT_BACKUP_PREFLIGHT_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_export_backup_preflight" in schemas
    assert get_schema("governance_export_backup_preflight")["type"] == "object"
    assert Path("docs/schemas/governance_export_backup_preflight.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-13-export-backup-governance-preflight/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-13-export-backup-governance-preflight/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-13-export-backup-governance-preflight/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

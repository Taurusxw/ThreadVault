from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import ENFORCEMENT_CHECK_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_enforcement_check_default_is_dry_run_and_does_not_enforce() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["governance", "enforcement", "check", "--command", "threadvault export", "--role", "reader", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_enforcement_check", payload)["ok"] is True
    assert payload["contract_version"] == "governance_enforcement_check.v1"
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "export_archive"
    assert payload["command_policy"]["access_level"] == "export"
    assert payload["permission"]["would_allow"] is False
    assert payload["permission"]["allowed"] is True
    assert payload["enforcement"]["dry_run"] is True
    assert payload["enforcement"]["current_enforced"] is False
    assert payload["enforcement"]["would_block_if_enforced"] is True
    assert payload["enforcement"]["status"] == "would_block"
    assert "dry_run_only" in payload["enforcement"]["reasons"]
    assert payload["diagnostics"]["business_command_executed"] is False
    assert payload["diagnostics"]["server_required"] is False
    assert payload["diagnostics"]["cloud_sync"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_enforcement_check_role_with_access_would_allow() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["governance", "enforcement", "check", "--command", "threadvault export", "--role", "reviewer", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_enforcement_check", payload)["ok"] is True
    assert payload["permission"]["would_allow"] is True
    assert payload["enforcement"]["would_block_if_enforced"] is False
    assert payload["enforcement"]["status"] == "would_allow"


def test_enforcement_check_config_enabled_is_still_dry_run(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "governance",
            "enforcement",
            "check",
            "--config",
            str(config),
            "--command",
            "threadvault client session",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_enforcement_check", payload)["ok"] is True
    assert payload["diagnostics"]["governance_enabled"] is True
    assert payload["command_policy"]["access_level"] == "raw_transcript"
    assert payload["permission"]["enforced"] is True
    assert payload["permission"]["allowed"] is False
    assert payload["enforcement"]["current_enforced"] is False
    assert payload["enforcement"]["dry_run"] is True
    assert payload["diagnostics"]["business_command_executed"] is False


def test_enforcement_check_unknown_command_is_structured() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["governance", "enforcement", "check", "--command", "threadvault imaginary", "--role", "owner", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_enforcement_check", payload)["ok"] is True
    assert payload["command_policy"]["known"] is False
    assert payload["command_policy"]["operation"] is None
    assert payload["permission"]["required_access"] is None
    assert payload["enforcement"]["status"] == "unknown_command"
    assert "unknown_command" in payload["enforcement"]["reasons"]
    assert payload["diagnostics"]["known_command"] is False


def test_enforcement_check_can_write_dry_run_audit_record(tmp_path: Path) -> None:
    runner = CliRunner()
    log = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "governance",
            "enforcement",
            "check",
            "--command",
            "threadvault restore",
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
    assert validate_payload("governance_enforcement_check", payload)["ok"] is True
    assert payload["audit"]["written"] is True
    assert payload["audit"]["record"]["operation"] == "enforcement_dry_run"
    assert payload["audit"]["record"]["status"] == "would_block"
    assert payload["audit"]["record"]["metadata"]["checked_command"] == "threadvault restore"
    assert payload["audit"]["record"]["metadata"]["dry_run_only"] == "true"
    assert log.exists()

    list_result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])
    assert list_result.exit_code == 0, list_result.output
    listed = json.loads(list_result.output)
    assert listed["records"][0]["operation"] == "enforcement_dry_run"


def test_enforcement_check_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance enforcement check" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_enforcement_dry_run"] is True

    guide = robot_guide()
    assert guide["governance"]["enforcement_check_contract_version"] == "governance_enforcement_check.v1"
    assert guide["governance"]["enforcement_check_schema"] == "governance_enforcement_check"
    assert ENFORCEMENT_CHECK_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_enforcement_check" in schemas
    assert get_schema("governance_enforcement_check")["type"] == "object"
    assert Path("docs/schemas/governance_enforcement_check.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-11-governance-enforcement-dry-run/plan.md"),
        Path("docs/v3/phases/phase-11-governance-enforcement-dry-run/design-notes.md"),
        Path("docs/v3/phases/phase-11-governance-enforcement-dry-run/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

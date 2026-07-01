from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import PERMISSION_CHECK_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_permission_check_default_disabled_is_not_enforced() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["governance", "permission", "check", "--operation", "read_raw_transcript", "--role", "reader", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_permission_check", payload)["ok"] is True
    assert payload["contract_version"] == "governance_permission_check.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["decision"]["enforced"] is False
    assert payload["decision"]["would_allow"] is False
    assert payload["decision"]["allowed"] is True
    assert "governance_disabled_not_enforced" in payload["decision"]["reasons"]
    assert payload["diagnostics"]["server_required"] is False


def test_permission_check_enabled_denies_missing_access(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "governance",
            "permission",
            "check",
            "--config",
            str(config),
            "--operation",
            "read_raw_transcript",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_permission_check", payload)["ok"] is True
    assert payload["governance"]["enabled"] is True
    assert payload["decision"]["enforced"] is True
    assert payload["decision"]["would_allow"] is False
    assert payload["decision"]["allowed"] is False
    assert payload["decision"]["status"] == "denied"
    assert "role_missing_access:raw_transcript" in payload["decision"]["reasons"]


def test_permission_check_enabled_allows_role_with_access(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "governance",
            "permission",
            "check",
            "--config",
            str(config),
            "--operation",
            "export_archive",
            "--role",
            "reviewer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_permission_check", payload)["ok"] is True
    assert payload["decision"]["allowed"] is True
    assert payload["decision"]["would_allow"] is True
    assert payload["decision"]["required_access"] == "export"
    assert payload["decision"]["reasons"] == []


def test_permission_check_can_write_audit_record(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    log = tmp_path / "audit.jsonl"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "governance",
            "permission",
            "check",
            "--config",
            str(config),
            "--operation",
            "restore_backup",
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
    assert validate_payload("governance_permission_check", payload)["ok"] is True
    assert payload["decision"]["allowed"] is False
    assert payload["audit"]["written"] is True
    assert payload["audit"]["record"]["operation"] == "permission_check"
    assert payload["audit"]["record"]["status"] == "denied"
    assert payload["audit"]["record"]["metadata"]["checked_operation"] == "restore_backup"
    assert log.exists()

    list_result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])
    assert list_result.exit_code == 0, list_result.output
    listed = json.loads(list_result.output)
    assert listed["records"][0]["operation"] == "permission_check"


def test_permission_check_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance permission check" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_permission_preflight"] is True

    guide = robot_guide()
    assert guide["governance"]["permission_check_contract_version"] == "governance_permission_check.v1"
    assert guide["governance"]["permission_schema"] == "governance_permission_check"
    assert PERMISSION_CHECK_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_permission_check" in schemas
    assert get_schema("governance_permission_check")["type"] == "object"
    assert Path("docs/schemas/governance_permission_check.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-09-permission-preflight-workflow/plan.md"),
        Path("docs/v3/phases/phase-09-permission-preflight-workflow/design-notes.md"),
        Path("docs/v3/phases/phase-09-permission-preflight-workflow/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

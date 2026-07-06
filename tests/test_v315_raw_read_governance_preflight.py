from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import RAW_READ_PREFLIGHT_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_raw_read_preflight_owner_client_session_would_allow_without_side_effects() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "raw-read",
            "--command",
            "threadvault client session",
            "--role",
            "owner",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_raw_read_preflight", payload)["ok"] is True
    assert payload["contract_version"] == "governance_raw_read_preflight.v1"
    assert payload["scope"]["in_scope"] is True
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "read_raw_transcript"
    assert payload["command_policy"]["access_level"] == "raw_transcript"
    assert payload["permission"]["would_allow"] is True
    assert payload["enforcement"]["preflight_status"] == "would_allow"
    assert payload["privacy"]["raw_transcript_access"] is True
    assert payload["privacy"]["local_metadata_access"] is True
    assert payload["privacy"]["local_debug_requires_explicit_opt_in"] is True
    assert payload["audit"]["required_before_execution"] is True
    assert payload["audit"]["automatic_audit_now"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["raw_transcript_returned"] is False
    assert payload["execution"]["event_preview_returned"] is False
    assert payload["execution"]["local_metadata_returned"] is False
    assert payload["execution"]["server_required"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_raw_read_preflight_reader_client_session_would_block_if_enforced() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "raw-read",
            "--command",
            "threadvault client session",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_raw_read_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is True
    assert payload["permission"]["would_allow"] is False
    assert payload["enforcement"]["would_block_if_enforced"] is True
    assert payload["enforcement"]["preflight_status"] == "would_block"
    assert "role_would_be_blocked" in payload["enforcement"]["reasons"]
    assert payload["execution"]["raw_transcript_returned"] is False


def test_raw_read_preflight_config_enabled_reports_governance_but_still_no_content_returned(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "raw-read",
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
    assert validate_payload("governance_raw_read_preflight", payload)["ok"] is True
    assert payload["diagnostics"]["governance_enabled"] is True
    assert payload["permission"]["enforced"] is True
    assert payload["permission"]["allowed"] is False
    assert payload["enforcement"]["current_enforced"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["event_preview_returned"] is False
    assert payload["execution"]["local_metadata_returned"] is False


def test_raw_read_preflight_out_of_scope_command_is_structured() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "raw-read",
            "--command",
            "threadvault retrieval query",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_raw_read_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is False
    assert payload["scope"]["reason"] == "out_of_scope_command"
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "read_summary_search"
    assert payload["enforcement"]["preflight_status"] == "out_of_scope"
    assert payload["enforcement"]["out_of_scope"] is True
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["raw_transcript_returned"] is False


def test_raw_read_preflight_can_write_audit_record_for_preflight_only(tmp_path: Path) -> None:
    runner = CliRunner()
    log = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "raw-read",
            "--command",
            "threadvault client session",
            "--role",
            "reader",
            "--audit-log",
            str(log),
            "--actor",
            "reader@example",
            "--target-type",
            "session",
            "--target-id",
            "sess-current",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_raw_read_preflight", payload)["ok"] is True
    assert payload["audit"]["preflight_record_written"] is True
    assert payload["audit"]["record"]["operation"] == "raw_read_preflight"
    assert payload["audit"]["record"]["status"] == "would_block"
    assert payload["audit"]["record"]["metadata"]["checked_command"] == "threadvault client session"
    assert payload["audit"]["record"]["metadata"]["business_command_executed"] == "false"
    assert payload["audit"]["record"]["metadata"]["raw_transcript_returned"] == "false"
    assert payload["execution"]["event_preview_returned"] is False
    assert log.exists()

    list_result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])
    assert list_result.exit_code == 0, list_result.output
    listed = json.loads(list_result.output)
    assert listed["records"][0]["operation"] == "raw_read_preflight"


def test_raw_read_preflight_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance preflight raw-read" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_raw_read_preflight"] is True

    guide = robot_guide()
    assert guide["governance"]["raw_read_preflight_contract_version"] == "governance_raw_read_preflight.v1"
    assert guide["governance"]["raw_read_preflight_schema"] == "governance_raw_read_preflight"
    assert RAW_READ_PREFLIGHT_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_raw_read_preflight" in schemas
    assert get_schema("governance_raw_read_preflight")["type"] == "object"
    assert Path("docs/schemas/governance_raw_read_preflight.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-15-raw-read-governance-preflight/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-15-raw-read-governance-preflight/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-15-raw-read-governance-preflight/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import EXPORT_PREVIEW_PREFLIGHT_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_export_preview_preflight_reviewer_would_allow_without_side_effects() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "export-preview",
            "--command",
            "threadvault client export-preview",
            "--role",
            "reviewer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_export_preview_preflight", payload)["ok"] is True
    assert payload["contract_version"] == "governance_export_preview_preflight.v1"
    assert payload["scope"]["in_scope"] is True
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "export_archive"
    assert payload["command_policy"]["access_level"] == "export"
    assert payload["permission"]["would_allow"] is True
    assert payload["enforcement"]["preflight_status"] == "would_allow"
    assert payload["privacy"]["export_access"] is True
    assert payload["privacy"]["preview_access"] is True
    assert payload["privacy"]["privacy_scan_expected_before_execution"] is True
    assert payload["privacy"]["privacy_findings_returned"] is False
    assert payload["audit"]["required_before_execution"] is False
    assert payload["audit"]["automatic_audit_now"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["preview_generated"] is False
    assert payload["execution"]["manifest_returned"] is False
    assert payload["execution"]["files_written"] is False
    assert payload["execution"]["local_metadata_returned"] is False
    assert payload["execution"]["server_required"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_export_preview_preflight_reader_would_block_if_enforced() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "export-preview",
            "--command",
            "threadvault client export-preview",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_export_preview_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is True
    assert payload["permission"]["would_allow"] is False
    assert payload["enforcement"]["would_block_if_enforced"] is True
    assert payload["enforcement"]["preflight_status"] == "would_block"
    assert "role_would_be_blocked" in payload["enforcement"]["reasons"]
    assert payload["execution"]["preview_generated"] is False


def test_export_preview_preflight_config_enabled_reports_governance_but_still_no_preview(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "export-preview",
            "--config",
            str(config),
            "--command",
            "threadvault client export-preview",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_export_preview_preflight", payload)["ok"] is True
    assert payload["diagnostics"]["governance_enabled"] is True
    assert payload["permission"]["enforced"] is True
    assert payload["permission"]["allowed"] is False
    assert payload["enforcement"]["current_enforced"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["preview_generated"] is False
    assert payload["execution"]["manifest_returned"] is False
    assert payload["execution"]["files_written"] is False


def test_export_preview_preflight_out_of_scope_command_is_structured() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "export-preview",
            "--command",
            "threadvault export",
            "--role",
            "reviewer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_export_preview_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is False
    assert payload["scope"]["reason"] == "out_of_scope_command"
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "export_archive"
    assert payload["enforcement"]["preflight_status"] == "out_of_scope"
    assert payload["enforcement"]["out_of_scope"] is True
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["preview_generated"] is False


def test_export_preview_preflight_can_write_audit_record_for_preflight_only(tmp_path: Path) -> None:
    runner = CliRunner()
    log = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "export-preview",
            "--command",
            "threadvault client export-preview",
            "--role",
            "reader",
            "--audit-log",
            str(log),
            "--actor",
            "reader@example",
            "--target-type",
            "export-preview",
            "--target-id",
            "preview-1",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_export_preview_preflight", payload)["ok"] is True
    assert payload["audit"]["preflight_record_written"] is True
    assert payload["audit"]["record"]["operation"] == "export_preview_preflight"
    assert payload["audit"]["record"]["status"] == "would_block"
    assert payload["audit"]["record"]["metadata"]["checked_command"] == "threadvault client export-preview"
    assert payload["audit"]["record"]["metadata"]["business_command_executed"] == "false"
    assert payload["audit"]["record"]["metadata"]["preview_generated"] == "false"
    assert payload["audit"]["record"]["metadata"]["files_written"] == "false"
    assert payload["execution"]["manifest_returned"] is False
    assert log.exists()

    list_result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])
    assert list_result.exit_code == 0, list_result.output
    listed = json.loads(list_result.output)
    assert listed["records"][0]["operation"] == "export_preview_preflight"


def test_export_preview_preflight_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance preflight export-preview" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_export_preview_preflight"] is True

    guide = robot_guide()
    assert (
        guide["governance"]["export_preview_preflight_contract_version"]
        == "governance_export_preview_preflight.v1"
    )
    assert guide["governance"]["export_preview_preflight_schema"] == "governance_export_preview_preflight"
    assert EXPORT_PREVIEW_PREFLIGHT_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_export_preview_preflight" in schemas
    assert get_schema("governance_export_preview_preflight")["type"] == "object"
    assert Path("docs/schemas/governance_export_preview_preflight.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-17-export-preview-governance-preflight/plan.md"),
        Path("docs/v3/phases/phase-17-export-preview-governance-preflight/design-notes.md"),
        Path("docs/v3/phases/phase-17-export-preview-governance-preflight/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

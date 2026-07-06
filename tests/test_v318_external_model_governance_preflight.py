from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import EXTERNAL_MODEL_PREFLIGHT_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_external_model_preflight_reviewer_would_allow_without_side_effects() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "external-model",
            "--command",
            "external model adapters",
            "--role",
            "reviewer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_external_model_preflight", payload)["ok"] is True
    assert payload["contract_version"] == "governance_external_model_preflight.v1"
    assert payload["scope"]["in_scope"] is True
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "external_model_call"
    assert payload["command_policy"]["access_level"] == "export"
    assert payload["permission"]["would_allow"] is True
    assert payload["enforcement"]["preflight_status"] == "would_allow"
    assert payload["outbound_policy"]["external_model_calls_enabled_by_default"] is False
    assert payload["outbound_policy"]["explicit_opt_in_required"] is True
    assert payload["outbound_policy"]["outbound_data_policy_required"] is True
    assert payload["outbound_policy"]["privacy_scan_required"] is True
    assert payload["outbound_policy"]["redaction_or_fail_policy_required"] is True
    assert payload["outbound_policy"]["evidence_validation_required"] is True
    assert payload["outbound_policy"]["raw_transcript_allowed_by_default"] is False
    assert payload["audit"]["required_before_execution"] is True
    assert payload["audit"]["automatic_audit_now"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["external_call_executed"] is False
    assert payload["execution"]["payload_sent"] is False
    assert payload["execution"]["model_response_returned"] is False
    assert payload["execution"]["provider_metadata_returned"] is False
    assert payload["execution"]["server_required"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False
    assert payload["diagnostics"]["external_adapter_implemented"] is False


def test_external_model_preflight_reader_would_block_if_enforced() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "external-model",
            "--command",
            "external model adapters",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_external_model_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is True
    assert payload["permission"]["would_allow"] is False
    assert payload["enforcement"]["would_block_if_enforced"] is True
    assert payload["enforcement"]["preflight_status"] == "would_block"
    assert "role_would_be_blocked" in payload["enforcement"]["reasons"]
    assert payload["execution"]["payload_sent"] is False


def test_external_model_preflight_config_enabled_reports_governance_but_still_no_call(
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
            "external-model",
            "--config",
            str(config),
            "--command",
            "external model adapters",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_external_model_preflight", payload)["ok"] is True
    assert payload["diagnostics"]["governance_enabled"] is True
    assert payload["permission"]["enforced"] is True
    assert payload["permission"]["allowed"] is False
    assert payload["enforcement"]["current_enforced"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["external_call_executed"] is False
    assert payload["execution"]["payload_sent"] is False


def test_external_model_preflight_unknown_command_is_structured() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "external-model",
            "--command",
            "threadvault export",
            "--role",
            "reviewer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_external_model_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is False
    assert payload["scope"]["reason"] == "out_of_scope_command"
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "export_archive"
    assert payload["enforcement"]["preflight_status"] == "out_of_scope"
    assert payload["enforcement"]["out_of_scope"] is True
    assert payload["execution"]["external_call_executed"] is False
    assert payload["execution"]["payload_sent"] is False


def test_external_model_preflight_can_write_audit_record_for_preflight_only(tmp_path: Path) -> None:
    runner = CliRunner()
    log = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "external-model",
            "--command",
            "external model adapters",
            "--role",
            "reader",
            "--audit-log",
            str(log),
            "--actor",
            "reader@example",
            "--target-type",
            "external-model",
            "--target-id",
            "adapter-preview",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_external_model_preflight", payload)["ok"] is True
    assert payload["audit"]["preflight_record_written"] is True
    assert payload["audit"]["record"]["operation"] == "external_model_preflight"
    assert payload["audit"]["record"]["status"] == "would_block"
    assert payload["audit"]["record"]["metadata"]["checked_command"] == "external model adapters"
    assert payload["audit"]["record"]["metadata"]["business_command_executed"] == "false"
    assert payload["audit"]["record"]["metadata"]["external_call_executed"] == "false"
    assert payload["audit"]["record"]["metadata"]["payload_sent"] == "false"
    assert payload["execution"]["model_response_returned"] is False
    assert log.exists()

    list_result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])
    assert list_result.exit_code == 0, list_result.output
    listed = json.loads(list_result.output)
    assert listed["records"][0]["operation"] == "external_model_preflight"


def test_external_model_preflight_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance preflight external-model" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_external_model_preflight"] is True

    guide = robot_guide()
    assert (
        guide["governance"]["external_model_preflight_contract_version"]
        == "governance_external_model_preflight.v1"
    )
    assert guide["governance"]["external_model_preflight_schema"] == "governance_external_model_preflight"
    assert EXTERNAL_MODEL_PREFLIGHT_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_external_model_preflight" in schemas
    assert get_schema("governance_external_model_preflight")["type"] == "object"
    assert Path("docs/schemas/governance_external_model_preflight.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-18-external-model-governance-preflight/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-18-external-model-governance-preflight/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-18-external-model-governance-preflight/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

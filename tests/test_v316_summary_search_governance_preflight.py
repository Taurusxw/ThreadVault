from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import SUMMARY_SEARCH_PREFLIGHT_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_summary_search_preflight_reader_retrieval_query_would_allow_without_side_effects() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "summary-search",
            "--command",
            "threadvault retrieval query",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_summary_search_preflight", payload)["ok"] is True
    assert payload["contract_version"] == "governance_summary_search_preflight.v1"
    assert payload["scope"]["in_scope"] is True
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "read_summary_search"
    assert payload["command_policy"]["access_level"] == "summary_search"
    assert payload["permission"]["would_allow"] is True
    assert payload["enforcement"]["preflight_status"] == "would_allow"
    assert payload["privacy"]["summary_search_access"] is True
    assert payload["privacy"]["raw_transcript_access"] is False
    assert payload["privacy"]["local_debug_requires_explicit_opt_in"] is True
    assert payload["audit"]["required_before_execution"] is False
    assert payload["audit"]["automatic_audit_now"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["search_executed"] is False
    assert payload["execution"]["retrieval_results_returned"] is False
    assert payload["execution"]["warning_details_returned"] is False
    assert payload["execution"]["local_metadata_returned"] is False
    assert payload["execution"]["server_required"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_summary_search_preflight_unknown_role_would_block_if_enforced() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "summary-search",
            "--command",
            "threadvault agent retrieve",
            "--role",
            "guest",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_summary_search_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is True
    assert payload["permission"]["would_allow"] is False
    assert payload["enforcement"]["would_block_if_enforced"] is True
    assert payload["enforcement"]["preflight_status"] == "would_block"
    assert "unknown_role" in payload["enforcement"]["reasons"]
    assert payload["execution"]["search_executed"] is False


def test_summary_search_preflight_config_enabled_reports_governance_but_still_no_results_returned(
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
            "summary-search",
            "--config",
            str(config),
            "--command",
            "threadvault client warnings",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_summary_search_preflight", payload)["ok"] is True
    assert payload["diagnostics"]["governance_enabled"] is True
    assert payload["permission"]["enforced"] is True
    assert payload["permission"]["allowed"] is True
    assert payload["enforcement"]["current_enforced"] is False
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["retrieval_results_returned"] is False
    assert payload["execution"]["warning_details_returned"] is False


def test_summary_search_preflight_out_of_scope_command_is_structured() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "summary-search",
            "--command",
            "threadvault client session",
            "--role",
            "owner",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_summary_search_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is False
    assert payload["scope"]["reason"] == "out_of_scope_command"
    assert payload["command_policy"]["known"] is True
    assert payload["command_policy"]["operation"] == "read_raw_transcript"
    assert payload["enforcement"]["preflight_status"] == "out_of_scope"
    assert payload["enforcement"]["out_of_scope"] is True
    assert payload["execution"]["business_command_executed"] is False
    assert payload["execution"]["retrieval_results_returned"] is False


def test_summary_search_preflight_unknown_command_is_structured() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "summary-search",
            "--command",
            "threadvault unknown",
            "--role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_summary_search_preflight", payload)["ok"] is True
    assert payload["scope"]["in_scope"] is False
    assert payload["command_policy"]["known"] is False
    assert payload["command_policy"]["operation"] is None
    assert payload["enforcement"]["preflight_status"] == "unknown_command"
    assert "unknown_command" in payload["enforcement"]["reasons"]
    assert payload["execution"]["search_executed"] is False


def test_summary_search_preflight_can_write_audit_record_for_preflight_only(tmp_path: Path) -> None:
    runner = CliRunner()
    log = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "governance",
            "preflight",
            "summary-search",
            "--command",
            "threadvault retrieval hybrid",
            "--role",
            "reader",
            "--audit-log",
            str(log),
            "--actor",
            "reader@example",
            "--target-type",
            "search",
            "--target-id",
            "query-1",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_summary_search_preflight", payload)["ok"] is True
    assert payload["audit"]["preflight_record_written"] is True
    assert payload["audit"]["record"]["operation"] == "summary_search_preflight"
    assert payload["audit"]["record"]["status"] == "would_allow"
    assert payload["audit"]["record"]["metadata"]["checked_command"] == "threadvault retrieval hybrid"
    assert payload["audit"]["record"]["metadata"]["business_command_executed"] == "false"
    assert payload["audit"]["record"]["metadata"]["search_executed"] == "false"
    assert payload["audit"]["record"]["metadata"]["retrieval_results_returned"] == "false"
    assert payload["execution"]["retrieval_results_returned"] is False
    assert log.exists()

    list_result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])
    assert list_result.exit_code == 0, list_result.output
    listed = json.loads(list_result.output)
    assert listed["records"][0]["operation"] == "summary_search_preflight"


def test_summary_search_preflight_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance preflight summary-search" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_summary_search_preflight"] is True

    guide = robot_guide()
    assert (
        guide["governance"]["summary_search_preflight_contract_version"]
        == "governance_summary_search_preflight.v1"
    )
    assert guide["governance"]["summary_search_preflight_schema"] == "governance_summary_search_preflight"
    assert SUMMARY_SEARCH_PREFLIGHT_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_summary_search_preflight" in schemas
    assert get_schema("governance_summary_search_preflight")["type"] == "object"
    assert Path("docs/schemas/governance_summary_search_preflight.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-16-summary-search-governance-preflight/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-16-summary-search-governance-preflight/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-16-summary-search-governance-preflight/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import ENFORCEMENT_GAPS_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_enforcement_gaps_default_payload_is_planning_only() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "enforcement", "gaps", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_enforcement_gaps", payload)["ok"] is True
    assert payload["contract_version"] == "governance_enforcement_gaps.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["governance"]["enforcement_enabled"] is False
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["cloud_sync"] is False
    assert payload["diagnostics"]["permissions_enforced_now"] is False
    assert payload["diagnostics"]["automatic_audit_now"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False
    assert payload["summary"]["command_count"] == len(payload["commands"])
    assert payload["summary"]["audit_required_count"] > 0
    assert payload["summary"]["instrumented_command_count"] == 16
    assert all(item["current_state"]["enforced"] is False for item in payload["commands"])
    by_command = {item["command"]: item for item in payload["commands"]}
    assert by_command["threadvault client export-preview"]["current_state"]["automatic_preflight"] is True
    assert by_command["threadvault client export-preview"]["current_state"]["automatic_audit"] is True
    assert by_command["threadvault export"]["current_state"]["automatic_preflight"] is True


def test_enforcement_gaps_cover_v3_governance_command_surface() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "enforcement", "gaps", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    by_command = {item["command"]: item for item in payload["commands"]}
    for command in [
        "threadvault client session",
        "threadvault agent retrieve",
        "threadvault retrieval query",
        "threadvault export",
        "threadvault export-target markdown",
        "threadvault export-target obsidian",
        "threadvault export-target skill",
        "threadvault backup",
        "threadvault client export-preview",
        "threadvault restore",
        "threadvault restore-history prune",
        "threadvault backup-history prune",
        "threadvault audit-history prune",
        "external model adapters",
    ]:
        assert command in by_command

    assert by_command["threadvault client session"]["access_level"] == "raw_transcript"
    assert by_command["threadvault export"]["operation"] == "export_archive"
    assert by_command["threadvault restore"]["access_level"] == "restore"
    assert by_command["threadvault backup-history prune"]["operation"] == "delete_or_prune"
    assert by_command["external model adapters"]["operation"] == "external_model_call"
    assert payload["summary"]["by_access_level"]["export"] >= 1
    assert payload["summary"]["by_access_level"]["delete_retention"] >= 1


def test_enforcement_gaps_config_enabled_still_does_not_enable_enforcement(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(app, ["governance", "enforcement", "gaps", "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_enforcement_gaps", payload)["ok"] is True
    assert payload["governance"]["enabled"] is True
    assert payload["governance"]["mode"] == "local_opt_in"
    assert payload["governance"]["enforcement_enabled"] is False


def test_enforcement_gaps_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance enforcement gaps" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_enforcement_gap_audit"] is True

    guide = robot_guide()
    assert guide["governance"]["enforcement_gaps_contract_version"] == "governance_enforcement_gaps.v1"
    assert guide["governance"]["enforcement_gaps_schema"] == "governance_enforcement_gaps"
    assert ENFORCEMENT_GAPS_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_enforcement_gaps" in schemas
    assert get_schema("governance_enforcement_gaps")["type"] == "object"
    assert Path("docs/schemas/governance_enforcement_gaps.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-10-governance-enforcement-gap-audit/plan.md"),
        Path("docs/v3/phases/phase-10-governance-enforcement-gap-audit/design-notes.md"),
        Path("docs/v3/phases/phase-10-governance-enforcement-gap-audit/gap-audit.md"),
        Path("docs/v3/phases/phase-10-governance-enforcement-gap-audit/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

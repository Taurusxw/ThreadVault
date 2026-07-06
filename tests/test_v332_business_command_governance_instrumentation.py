from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import BUSINESS_COMMAND_INSTRUMENTATION_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def write_governance_config(path: Path) -> None:
    path.write_text("[governance]\nenabled = true\n", encoding="utf-8")


def test_business_command_instrumentation_diagnostic_routes_to_export_backup_preflight(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    audit_log = tmp_path / "audit.jsonl"
    write_governance_config(config)

    result = runner.invoke(
        app,
        [
            "governance",
            "instrumentation",
            "business-command",
            "--config",
            str(config),
            "--command",
            "threadvault backup",
            "--role",
            "reader",
            "--actor",
            "reader@example",
            "--audit-log",
            str(audit_log),
            "--target-type",
            "backup",
            "--target-id",
            "threadvault.db",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_business_command_instrumentation", payload)["ok"] is True
    assert payload["contract_version"] == "governance_business_command_instrumentation.v1"
    assert payload["governance"]["enabled"] is True
    assert payload["command_policy"]["category"] == "export_backup"
    assert payload["command_policy"]["operation"] == "export_archive"
    assert payload["instrumentation"]["instrumented"] is True
    assert payload["instrumentation"]["blocked"] is True
    assert payload["instrumentation"]["business_command_should_execute"] is False
    assert payload["preflight"]["contract_version"] == "governance_export_backup_preflight.v1"
    assert payload["audit"]["preflight_record_written"] is True
    assert audit_log.exists()


def test_backup_command_blocks_reader_before_side_effect_when_governance_enabled(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    db = tmp_path / "missing.db"
    out = tmp_path / "blocked-backup.db"
    write_governance_config(config)

    result = runner.invoke(
        app,
        [
            "backup",
            "--db",
            str(db),
            "--out",
            str(out),
            "--governance-config",
            str(config),
            "--governance-role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["error"] == "governance_preflight_blocked"
    instrumentation = payload["governance_instrumentation"]
    assert instrumentation["instrumentation"]["blocked"] is True
    assert instrumentation["execution"]["business_command_executed"] is False
    assert instrumentation["execution"]["blocked_before_execution"] is True
    assert not out.exists()


def test_backup_command_allows_reviewer_and_marks_execution(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    config = tmp_path / "threadvault.toml"
    out = tmp_path / "allowed-backup.db"
    write_governance_config(config)

    result = runner.invoke(
        app,
        [
            "backup",
            "--db",
            str(db),
            "--out",
            str(out),
            "--governance-config",
            str(config),
            "--governance-role",
            "reviewer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("backup", payload)["ok"] is True
    assert payload["ok"] is True
    assert out.exists()
    instrumentation = payload["governance_instrumentation"]
    assert instrumentation["instrumentation"]["blocked"] is False
    assert instrumentation["execution"]["business_command_executed"] is True
    assert instrumentation["preflight"]["execution"]["business_command_executed"] is True


def test_raw_read_command_blocks_reader_before_session_payload(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    config = tmp_path / "threadvault.toml"
    write_governance_config(config)

    result = runner.invoke(
        app,
        [
            "client",
            "session",
            "--db",
            str(db),
            "--session",
            "sess-current",
            "--governance-config",
            str(config),
            "--governance-role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["error"] == "governance_preflight_blocked"
    instrumentation = payload["governance_instrumentation"]
    assert instrumentation["command_policy"]["category"] == "raw_read"
    assert instrumentation["instrumentation"]["blocked"] is True
    assert instrumentation["execution"]["business_command_executed"] is False
    assert "events" not in payload


def test_summary_search_command_allows_reader_without_changing_retrieval_core(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    config = tmp_path / "threadvault.toml"
    write_governance_config(config)

    result = runner.invoke(
        app,
        [
            "retrieval",
            "query",
            "pytest",
            "--db",
            str(db),
            "--governance-config",
            str(config),
            "--governance-role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("retrieval_query", payload)["ok"] is True
    assert payload["contract_version"] == "retrieval.v1"
    assert payload["diagnostics"]["used_mode"] == "fts"
    assert payload["results"]
    instrumentation = payload["governance_instrumentation"]
    assert instrumentation["command_policy"]["category"] == "summary_search"
    assert instrumentation["instrumentation"]["blocked"] is False
    assert instrumentation["execution"]["business_command_executed"] is True
    assert instrumentation["diagnostics"]["v2_retrieval_core_changed"] is False


def test_business_command_instrumentation_discovery_schema_docs_and_gap_audit() -> None:
    caps = capabilities()
    assert "governance instrumentation business-command" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_business_command_instrumentation"] is True

    guide = robot_guide()
    assert BUSINESS_COMMAND_INSTRUMENTATION_COMMAND in guide["recommended_commands"]
    assert (
        guide["governance"]["business_command_instrumentation_contract_version"]
        == "governance_business_command_instrumentation.v1"
    )
    assert guide["governance"]["business_command_instrumentation_schema"] == "governance_business_command_instrumentation"

    schemas = robot_schemas()
    assert "governance_business_command_instrumentation" in schemas
    assert get_schema("governance_business_command_instrumentation")["type"] == "object"
    assert Path("docs/schemas/governance_business_command_instrumentation.schema.json").exists()

    runner = CliRunner()
    result = runner.invoke(app, ["governance", "v3", "gap-audit", "--json"])
    assert result.exit_code == 0, result.output
    gap = json.loads(result.output)
    blocker_codes = {item["code"] for item in gap["blockers"]}
    gaps = {item["code"]: item for item in gap["remaining_gaps"]}
    assert "automatic_governance_instrumentation_incomplete" not in blocker_codes
    assert "v3_acceptance_smoke_missing" not in blocker_codes
    assert gaps["automatic_instrumentation"]["status"] == "accepted_broad_command_instrumentation"
    assert "business_command_governance_instrumentation" in gap["implemented_capabilities"]
    assert gap["completion"]["accepted_phase_count"] == 33
    assert gap["completion"]["current_phase"] == "phase-33-v3-final-acceptance-smoke"
    assert gap["completion"]["blocking_count"] == 0

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-32-business-command-governance-instrumentation/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-32-business-command-governance-instrumentation/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-32-business-command-governance-instrumentation/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

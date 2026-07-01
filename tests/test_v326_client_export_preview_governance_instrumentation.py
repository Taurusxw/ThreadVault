from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import validate_payload
from threadvault.store import ArchiveStore, capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_client_export_preview_default_keeps_governance_instrumentation_disabled(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "preview-out"

    result = runner.invoke(
        app,
        ["client", "export-preview", "--db", str(db), "--session", "sess-current", "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_export_preview", payload)["ok"] is True
    assert payload["governance_instrumentation"]["enabled"] is False
    assert payload["governance_instrumentation"]["reason"] == "not_requested"
    assert payload["diagnostics"]["governance_instrumented"] is False
    assert payload["diagnostics"]["governance_blocked"] is False
    assert payload["diagnostics"]["writes_files"] is False
    assert not out.exists()


def test_client_export_preview_governance_reviewer_generates_preview_without_writing_files(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "instrumented-preview"

    result = runner.invoke(
        app,
        [
            "client",
            "export-preview",
            "--db",
            str(db),
            "--session",
            "sess-current",
            "--out",
            str(out),
            "--governance-role",
            "reviewer",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_export_preview", payload)["ok"] is True
    governance = payload["governance_instrumentation"]
    assert governance["enabled"] is True
    assert governance["blocked"] is False
    assert governance["reason"] == "preflight_allowed"
    assert governance["role"] == "reviewer"
    assert governance["preflight"]["scope"]["in_scope"] is True
    assert governance["preflight"]["permission"]["would_allow"] is True
    assert governance["preflight"]["execution"]["business_command_executed"] is False
    assert governance["preflight"]["execution"]["preview_generated"] is True
    assert governance["preflight"]["execution"]["manifest_returned"] is True
    assert payload["planned_files"]
    assert payload["diagnostics"]["governance_instrumented"] is True
    assert payload["diagnostics"]["governance_blocked"] is False
    assert payload["diagnostics"]["writes_files"] is False
    assert not out.exists()


def test_client_export_preview_governance_can_write_preflight_audit_record(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "audit-preview"
    log = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "client",
            "export-preview",
            "--db",
            str(db),
            "--session",
            "sess-current",
            "--out",
            str(out),
            "--governance-role",
            "reviewer",
            "--governance-audit-log",
            str(log),
            "--governance-actor",
            "reviewer@example",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_export_preview", payload)["ok"] is True
    preflight = payload["governance_instrumentation"]["preflight"]
    assert preflight["audit"]["preflight_record_written"] is True
    assert preflight["audit"]["record"]["operation"] == "export_preview_preflight"
    assert preflight["audit"]["record"]["actor"] == "reviewer@example"
    assert preflight["audit"]["record"]["metadata"]["business_command_executed"] == "false"
    assert preflight["audit"]["record"]["metadata"]["files_written"] == "false"
    assert log.exists()
    assert not out.exists()

    list_result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])
    assert list_result.exit_code == 0, list_result.output
    listed = json.loads(list_result.output)
    assert listed["records"][0]["operation"] == "export_preview_preflight"


def test_client_export_preview_governance_enabled_blocks_reader_before_preview(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "blocked-preview"
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "client",
            "export-preview",
            "--db",
            str(db),
            "--session",
            "sess-current",
            "--out",
            str(out),
            "--governance-config",
            str(config),
            "--governance-role",
            "reader",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_export_preview", payload)["ok"] is True
    governance = payload["governance_instrumentation"]
    assert governance["enabled"] is True
    assert governance["blocked"] is True
    assert governance["reason"] == "preflight_blocked"
    assert governance["preflight"]["permission"]["enforced"] is True
    assert governance["preflight"]["permission"]["allowed"] is False
    assert governance["preflight"]["execution"]["preview_generated"] is False
    assert payload["planned_files"] == []
    assert payload["skipped"][0]["reason"] == "governance_preflight_blocked"
    assert payload["diagnostics"]["preview"] is False
    assert payload["diagnostics"]["governance_blocked"] is True
    assert payload["diagnostics"]["writes_files"] is False
    assert not out.exists()


def test_client_export_preview_governance_instrumentation_discovery_docs_and_gap_audit() -> None:
    caps = capabilities()
    assert caps["feature_flags"]["client_export_preview_governance_instrumentation"] is True

    guide = robot_guide()
    assert "threadvault client export-preview --session SESSION_ID --out OUT --governance-role reviewer --json" in guide[
        "recommended_commands"
    ]
    assert guide["client_interface"]["instrumented_commands"] == ["threadvault client export-preview"]

    schemas = robot_schemas()
    assert schemas["client_export_preview"]["governance_instrumentation"] == "object"

    gap = ArchiveStore(Path("unused.db")).governance_v3_completion_gap_audit()
    blocker_codes = {item["code"] for item in gap["blockers"]}
    gaps = {item["code"]: item for item in gap["remaining_gaps"]}
    assert "automatic_governance_instrumentation_missing" not in blocker_codes
    assert "automatic_governance_instrumentation_incomplete" not in blocker_codes
    assert gaps["automatic_instrumentation"]["status"] == "accepted_broad_command_instrumentation"
    assert "client_export_preview_governance_instrumentation" in gap["implemented_capabilities"]
    assert gap["completion"]["accepted_phase_count"] == 33
    assert gap["completion"]["current_phase"] == "phase-33-v3-final-acceptance-smoke"

    for path in [
        Path("docs/v3/phases/phase-26-client-export-preview-governance-instrumentation/plan.md"),
        Path("docs/v3/phases/phase-26-client-export-preview-governance-instrumentation/design-notes.md"),
        Path("docs/v3/phases/phase-26-client-export-preview-governance-instrumentation/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_client_session_detail_default_payload_is_safe(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["client", "session", "--db", str(db), "--session", "sess-current", "--event-limit", "3", "--max-chars", "50", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_session", payload)["ok"] is True
    assert payload["contract_version"] == "client_session.v1"
    assert payload["session"]["session_id"] == "sess-current"
    assert "raw_path" not in payload["session"]
    assert payload["summary"]["evidence_event_ids"]
    assert len(payload["events"]) == 3
    assert all(len(event["text_preview"]) <= 50 for event in payload["events"])
    assert all("file_path" not in event for event in payload["events"])
    assert payload["privacy"]["raw_paths_included"] is False
    assert payload["privacy"]["event_file_paths_included"] is False
    assert payload["privacy"]["raw_transcript_included"] is False
    assert payload["diagnostics"]["server_required"] is False
    assert payload["actions"]["export_markdown"].startswith("threadvault export-target markdown")


def test_client_session_detail_local_debug_is_explicit(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["client", "session", "--db", str(db), "--session", "sess-current", "--local-debug", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_session", payload)["ok"] is True
    assert payload["privacy"]["raw_paths_included"] is True
    assert payload["privacy"]["event_file_paths_included"] is True
    assert "raw_path" in payload["session"]
    assert any("file_path" in event for event in payload["events"])


def test_client_session_detail_unknown_session_is_controlled_error(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["client", "session", "--db", str(db), "--session", "missing", "--json"])

    assert result.exit_code != 0
    assert "Unknown session: missing" in result.output


def test_client_session_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "client session" in caps["json_outputs"]
    assert caps["feature_flags"]["client_session"] is True

    guide = robot_guide()
    assert guide["client_interface"]["session_contract_version"] == "client_session.v1"
    assert guide["client_interface"]["schemas"] == [
        "client_interface_manifest",
        "client_overview",
        "client_tui_runtime",
        "client_session",
        "client_export_preview",
        "client_warnings",
    ]
    assert "threadvault client session --session SESSION_ID --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "client_session" in schemas
    assert get_schema("client_session")["type"] == "object"
    assert Path("docs/schemas/client_session.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-04-client-session-detail-workflow/plan.md"),
        Path("docs/v3/phases/phase-04-client-session-detail-workflow/design-notes.md"),
        Path("docs/v3/phases/phase-04-client-session-detail-workflow/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

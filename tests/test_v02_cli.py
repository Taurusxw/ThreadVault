from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["failed"] == 0
    return db


def test_json_contracts_stats_doctor_and_warnings(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["list", "--db", str(db), "--json"])
    assert result.exit_code == 0, result.output
    listed = json.loads(result.output)
    assert any(row["session_id"] == "sess-current" for row in listed)

    result = runner.invoke(app, ["stats", "--db", str(db), "--json"])
    assert result.exit_code == 0, result.output
    stats = json.loads(result.output)
    assert stats["sessions"] >= 3
    assert stats["turns"] >= 3

    result = runner.invoke(app, ["doctor", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    doctor = json.loads(result.output)
    assert doctor["ok"] is True
    assert doctor["jsonl_files"] >= 3

    result = runner.invoke(app, ["warnings", "--db", str(db), "--json"])
    assert result.exit_code == 0, result.output
    warnings = json.loads(result.output)
    assert any(item["code"] == "invalid_json" for item in warnings)


def test_search_filters_minimal_json_and_special_query(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["search", "alpha:beta", "--db", str(db), "--json", "--fields", "minimal"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload
    assert set(payload[0]) == {"event_id", "session_id"}

    result = runner.invoke(
        app,
        ["search", "second", "--db", str(db), "--json", "--type", "function_call", "--tool", "shell"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload
    assert all(item["tool_name"] == "shell" for item in payload)


def test_export_filters_last_turns_and_sections(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "out"

    result = runner.invoke(
        app,
        [
            "export",
            "--session",
            "sess-fork",
            "--db",
            str(db),
            "--out",
            str(out),
            "--last-turns",
            "1",
            "--no-tool-output",
            "--no-reasoning",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    exported = Path(payload["path"])
    text = exported.read_text(encoding="utf-8")
    assert "Second branch question" in text
    assert "First branch question" not in text
    assert "second output" not in text
    assert "hidden reasoning" not in text


def test_reimport_replaces_old_events_and_fts(tmp_path: Path) -> None:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    codex_home = tmp_path / "codex_home"
    sessions = codex_home / "sessions"
    sessions.mkdir(parents=True)
    session_file = sessions / "one.jsonl"
    session_file.write_text(
        "\n".join([
            '{"timestamp":"2026-03-01T00:00:00Z","type":"session_meta","payload":{"session_id":"replace-me","cwd":"E:\\\\Repo","source":"cli"}}',
            '{"timestamp":"2026-03-01T00:00:01Z","type":"event_msg","payload":{"type":"user_message","message":"old needle"}}',
        ]),
        encoding="utf-8",
    )
    assert runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(codex_home)]).exit_code == 0

    session_file.write_text(
        "\n".join([
            '{"timestamp":"2026-03-01T00:00:00Z","type":"session_meta","payload":{"session_id":"replace-me","cwd":"E:\\\\Repo","source":"cli"}}',
            '{"timestamp":"2026-03-01T00:00:01Z","type":"event_msg","payload":{"type":"user_message","message":"new needle"}}',
        ]),
        encoding="utf-8",
    )
    assert runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(codex_home)]).exit_code == 0

    conn = sqlite3.connect(db)
    try:
        event_count = conn.execute("SELECT COUNT(*) FROM events WHERE session_id = 'replace-me'").fetchone()[0]
        fts_count = conn.execute(
            "SELECT COUNT(*) FROM events_fts JOIN events e ON e.event_id = events_fts.rowid WHERE e.session_id = 'replace-me'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert event_count == 2
    assert fts_count == 2

    result = runner.invoke(app, ["search", "old", "--db", str(db), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == []

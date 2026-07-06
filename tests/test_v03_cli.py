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
    return db


def test_capabilities_robot_docs_and_reindex(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["capabilities", "--json"])
    assert result.exit_code == 0, result.output
    caps = json.loads(result.output)
    assert "robot-docs" in caps["commands"]
    assert set(caps["export_formats"]) == {"md", "json", "jsonl", "csv"}

    result = runner.invoke(app, ["robot-docs", "guide"])
    assert result.exit_code == 0, result.output
    guide = json.loads(result.output)
    assert "json_contract" in guide

    result = runner.invoke(app, ["robot-docs", "schemas"])
    assert result.exit_code == 0, result.output
    schemas = json.loads(result.output)
    assert "search_minimal" in schemas

    result = runner.invoke(app, ["reindex", "--db", str(db), "--fts-only", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["events"] == payload["events_fts"]


def test_export_formats_and_agent_profile(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "out"

    for fmt, suffix in [("json", ".json"), ("jsonl", ".jsonl"), ("csv", ".csv")]:
        result = runner.invoke(
            app,
            ["export", "--session", "sess-fork", "--db", str(db), "--out", str(out), "--format", fmt, "--json"],
        )
        assert result.exit_code == 0, result.output
        exported = Path(json.loads(result.output)["path"])
        assert exported.suffix == suffix
        assert exported.exists()

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
            "--profile",
            "agent",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    text = Path(json.loads(result.output)["path"]).read_text(encoding="utf-8")
    assert "hidden reasoning summary" not in text
    assert "second output" not in text


def test_state_sqlite_enriches_session_metadata(tmp_path: Path) -> None:
    runner = CliRunner()
    codex_home = tmp_path / "codex_home"
    sessions = codex_home / "sessions"
    sessions.mkdir(parents=True)
    rollout = sessions / "state-linked.jsonl"
    rollout.write_text(
        "\n".join([
            '{"timestamp":"2026-04-01T00:00:00Z","type":"session_meta","payload":{"session_id":"jsonl-id","source":"cli"}}',
            '{"timestamp":"2026-04-01T00:00:01Z","type":"event_msg","payload":{"type":"user_message","message":"state enrichment"}}',
        ]),
        encoding="utf-8",
    )
    conn = sqlite3.connect(codex_home / "state_5.sqlite")
    try:
        conn.execute(
            """
            CREATE TABLE threads (
              id TEXT,
              rollout_path TEXT,
              created_at TEXT,
              updated_at TEXT,
              source TEXT,
              cwd TEXT,
              title TEXT,
              preview TEXT,
              archived INTEGER,
              model TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "state-id",
                str(rollout),
                "2026-04-01T00:00:00Z",
                "2026-04-01T00:00:02Z",
                "desktop",
                "E:\\StateRepo",
                "State title",
                "State preview",
                1,
                "gpt-test",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(codex_home), "--json"])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["list", "--db", str(db), "--json"])
    assert result.exit_code == 0, result.output
    rows = json.loads(result.output)
    assert rows[0]["session_id"] == "state-id"
    assert rows[0]["cwd"] == "E:\\StateRepo"


def test_traceability_documents_exist() -> None:
    required = [
        Path("docs/progress/archive/legacy-v0/phases/phase-03-agent-friendly-archive/plan.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
        Path("docs/progress/archive/legacy-v0/phases/phase-03-agent-friendly-archive/external-review.md"),
    ]
    for path in required:
        assert path.exists(), f"missing {path}"

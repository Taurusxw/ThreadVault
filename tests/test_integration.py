from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import connect, list_sessions

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def test_import_search_export_and_summarize(tmp_path: Path) -> None:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    out = tmp_path / "out"

    result = runner.invoke(app, ["init", "--db", str(db)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES)])
    assert result.exit_code == 0, result.output
    assert "failed=0" in result.output

    result = runner.invoke(app, ["list", "--db", str(db)])
    assert result.exit_code == 0, result.output
    with connect(db) as conn:
        session_ids = {row.session_id for row in list_sessions(conn)}
    assert {"sess-current", "sess-legacy"} <= session_ids

    result = runner.invoke(app, ["search", "pytest", "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert "sess-current" in result.output

    result = runner.invoke(app, ["export", "--session", "sess-current", "--db", str(db), "--out", str(out)])
    assert result.exit_code == 0, result.output
    exported = out / "sess-current.md"
    assert exported.exists()
    assert "Run pytest" in exported.read_text(encoding="utf-8")

    result = runner.invoke(app, ["summarize", "--session", "sess-current", "--db", str(db), "--format", "json"])
    assert result.exit_code == 0, result.output
    assert "evidence_event_ids" in result.output
    assert "pytest" in result.output

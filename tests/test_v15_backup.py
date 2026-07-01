from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import SCHEMA_VERSION

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def session_count(db: Path) -> int:
    with sqlite3.connect(db) as conn:
        return int(conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0])


def test_backup_to_directory_creates_timestamped_db(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "backups"

    result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(out), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    backup = Path(payload["destination"])
    assert payload["ok"] is True
    assert backup.parent == out
    assert backup.name.startswith("threadvault-backup-")
    assert backup.suffix == ".db"
    assert payload["bytes"] > 0
    assert payload["schema_version"] == SCHEMA_VERSION
    assert session_count(backup) == session_count(db)


def test_backup_to_explicit_file_and_schema_validation(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "backup.db"
    payload_path = tmp_path / "backup.json"

    result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(out), "--json"])

    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")
    payload = json.loads(result.output)
    assert Path(payload["destination"]) == out
    assert payload["stats"]["sessions"] >= 1

    result = runner.invoke(app, ["validate-json", "--schema", "backup", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_backup_refuses_existing_without_force(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "backup.db"
    out.write_text("existing", encoding="utf-8")

    result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(out), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["error"] == "backup_exists"
    assert payload["overwritten"] is False
    assert out.read_text(encoding="utf-8") == "existing"


def test_backup_force_overwrites_existing(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "backup.db"
    out.write_text("existing", encoding="utf-8")

    result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(out), "--force", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["overwritten"] is True
    assert session_count(out) == session_count(db)


def test_v15_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-15-database-backup/plan.md"),
        Path("docs/v0/phases/phase-15-database-backup/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

from __future__ import annotations

import json
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


def make_named_backup(db: Path, path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(path), "--json"])
    assert result.exit_code == 0, result.output


def test_backup_history_list_latest_and_verify_latest(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    first = backup_dir / "threadvault-backup-20260630T000000Z.db"
    second = backup_dir / "threadvault-backup-20260630T000100Z.db"
    make_named_backup(db, first)
    make_named_backup(db, second)

    result = runner.invoke(app, ["backup-history", "list", "--dir", str(backup_dir), "--json"])
    assert result.exit_code == 0, result.output
    listing = json.loads(result.output)
    assert [Path(item["path"]).name for item in listing["backups"]] == [first.name, second.name]

    result = runner.invoke(app, ["backup-history", "latest", "--dir", str(backup_dir), "--json"])
    assert result.exit_code == 0, result.output
    latest = json.loads(result.output)
    assert Path(latest["latest"]["path"]).name == second.name

    result = runner.invoke(app, ["backup-history", "verify-latest", "--dir", str(backup_dir), "--json"])
    assert result.exit_code == 0, result.output
    verified = json.loads(result.output)
    assert verified["ok"] is True
    assert Path(verified["latest"]["path"]).name == second.name
    assert verified["verification"]["integrity_check"] == ["ok"]


def test_backup_history_empty_directory_returns_structured_error(tmp_path: Path) -> None:
    runner = CliRunner()
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    result = runner.invoke(app, ["backup-history", "verify-latest", "--dir", str(backup_dir), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["error"] == "no_valid_backups"


def test_backup_history_invalid_backup_is_warning(tmp_path: Path) -> None:
    runner = CliRunner()
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    bad = backup_dir / "threadvault-backup-20260630T000000Z.db"
    bad.write_text("not sqlite", encoding="utf-8")

    result = runner.invoke(app, ["backup-history", "list", "--dir", str(backup_dir), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["backups"] == []
    assert payload["warnings"][0]["code"] == "invalid_backup"


def test_backup_history_schemas_and_docs(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    make_named_backup(db, backup_dir / "threadvault-backup-20260630T000000Z.db")

    payloads = {
        "backup_history_list": tmp_path / "backup-history-list.json",
        "backup_history_latest": tmp_path / "backup-history-latest.json",
        "backup_history_verify_latest": tmp_path / "backup-history-verify-latest.json",
    }
    commands = {
        "backup_history_list": ["backup-history", "list", "--dir", str(backup_dir), "--json"],
        "backup_history_latest": ["backup-history", "latest", "--dir", str(backup_dir), "--json"],
        "backup_history_verify_latest": ["backup-history", "verify-latest", "--dir", str(backup_dir), "--json"],
    }
    for schema, command in commands.items():
        result = runner.invoke(app, command)
        assert result.exit_code == 0, result.output
        payloads[schema].write_text(result.output, encoding="utf-8")
        result = runner.invoke(app, ["validate-json", "--schema", schema, "--input", str(payloads[schema]), "--json"])
        assert result.exit_code == 0, result.output

    for path in [
        Path("docs/progress/archive/legacy-v0/phases/phase-17-backup-history/plan.md"),
        Path("docs/progress/archive/legacy-v0/phases/phase-17-backup-history/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

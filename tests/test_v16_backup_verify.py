from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import SCHEMA_VERSION

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def make_backup(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    backup = tmp_path / "backup.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(backup), "--json"])
    assert result.exit_code == 0, result.output
    return backup


def test_backup_verify_valid_backup_and_schema(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    payload_path = tmp_path / "backup-verify.json"

    result = runner.invoke(app, ["backup-verify", "--backup", str(backup), "--json"])

    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["exists"] is True
    assert payload["integrity_check"] == ["ok"]
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["doctor"]["ok"] is True
    assert payload["stats"]["sessions"] >= 1

    result = runner.invoke(app, ["validate-json", "--schema", "backup_verify", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_backup_verify_missing_file(tmp_path: Path) -> None:
    runner = CliRunner()
    missing = tmp_path / "missing.db"

    result = runner.invoke(app, ["backup-verify", "--backup", str(missing), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["exists"] is False
    assert payload["errors"][0]["code"] == "backup_missing"


def test_backup_verify_non_sqlite_file(tmp_path: Path) -> None:
    runner = CliRunner()
    bad = tmp_path / "bad.db"
    bad.write_text("not sqlite", encoding="utf-8")

    result = runner.invoke(app, ["backup-verify", "--backup", str(bad), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["exists"] is True
    assert payload["errors"][0]["code"] == "invalid_sqlite_database"


def test_v16_docs_exist() -> None:
    for path in [
        Path("docs/progress/archive/legacy-v0/phases/phase-16-backup-verify/plan.md"),
        Path("docs/progress/archive/legacy-v0/phases/phase-16-backup-verify/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

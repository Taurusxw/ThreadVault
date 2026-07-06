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


def make_backups(tmp_path: Path) -> list[Path]:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    paths = [
        backup_dir / "threadvault-backup-20260630T000000Z.db",
        backup_dir / "threadvault-backup-20260630T000100Z.db",
        backup_dir / "threadvault-backup-20260630T000200Z.db",
    ]
    for path in paths:
        result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(path), "--json"])
        assert result.exit_code == 0, result.output
    return paths


def test_backup_history_prune_dry_run_does_not_delete(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = make_backups(tmp_path)

    result = runner.invoke(app, ["backup-history", "prune", "--dir", str(paths[0].parent), "--keep", "2", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["apply"] is False
    assert len(payload["kept"]) == 2
    assert len(payload["deletable"]) == 1
    assert payload["deleted"] == []
    assert all(path.exists() for path in paths)


def test_backup_history_prune_apply_deletes_only_valid_old_backups(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = make_backups(tmp_path)
    bad = paths[0].parent / "threadvault-backup-bad.db"
    bad.write_text("not sqlite", encoding="utf-8")

    result = runner.invoke(app, ["backup-history", "prune", "--dir", str(paths[0].parent), "--keep", "1", "--apply", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["apply"] is True
    assert len(payload["deleted"]) == 2
    assert not paths[0].exists()
    assert not paths[1].exists()
    assert paths[2].exists()
    assert bad.exists()
    assert payload["warnings"][0]["code"] == "invalid_backup"


def test_backup_history_prune_schema_and_docs(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = make_backups(tmp_path)
    payload_path = tmp_path / "backup-prune.json"

    result = runner.invoke(app, ["backup-history", "prune", "--dir", str(paths[0].parent), "--keep", "2", "--json"])
    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")

    result = runner.invoke(app, ["validate-json", "--schema", "backup_history_prune", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True

    for path in [
        Path("docs/progress/archive/legacy-v0/phases/phase-18-backup-retention/plan.md"),
        Path("docs/progress/archive/legacy-v0/phases/phase-18-backup-retention/external-review.md"),
        Path("docs/schemas/backup_history_prune.schema.json"),
    ]:
        assert path.exists(), f"missing {path}"

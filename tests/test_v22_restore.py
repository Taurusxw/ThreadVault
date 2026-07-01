from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from tests.test_v15_backup import import_fixture, session_count
from threadvault.cli import app


def make_backup(tmp_path: Path, with_manifest: bool = True) -> Path:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    backup = tmp_path / "backup.db"
    args = ["backup", "--db", str(db), "--out", str(backup), "--json"]
    if not with_manifest:
        args.insert(-1, "--no-manifest")
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    return backup


def test_restore_dry_run_writes_nothing_and_schema_validates(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    target = tmp_path / "restore.db"
    payload_path = tmp_path / "restore.json"

    result = runner.invoke(app, ["restore", "--backup", str(backup), "--target-db", str(target), "--json"])

    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["mode"] == "dry_run"
    assert payload["apply"] is False
    assert not target.exists()

    result = runner.invoke(app, ["validate-json", "--schema", "restore", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_restore_apply_to_new_target_writes_and_verifies(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    target = tmp_path / "restore.db"

    result = runner.invoke(app, ["restore", "--backup", str(backup), "--target-db", str(target), "--apply", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["mode"] == "applied"
    assert payload["restored_verification"]["ok"] is True
    assert payload["restored_doctor"]["ok"] is True
    assert session_count(target) == session_count(backup)
    assert target.with_name(f"{target.name}.manifest.json").exists()
    result = runner.invoke(app, ["backup-manifest", "--backup", str(target), "--json"])
    assert result.exit_code == 0, result.output


def test_restore_existing_target_requires_overwrite(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    target = tmp_path / "restore.db"
    target.write_text("existing", encoding="utf-8")

    result = runner.invoke(app, ["restore", "--backup", str(backup), "--target-db", str(target), "--apply", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    codes = {error["code"] for error in payload["errors"]}
    assert "target_exists_without_overwrite" in codes
    assert target.read_text(encoding="utf-8") == "existing"


def test_restore_overwrite_requires_pre_restore_backup_dir(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    target = tmp_path / "restore.db"
    original = import_fixture(tmp_path / "existing")
    target.write_bytes(original.read_bytes())

    result = runner.invoke(app, ["restore", "--backup", str(backup), "--target-db", str(target), "--apply", "--overwrite", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    codes = {error["code"] for error in payload["errors"]}
    assert "pre_restore_backup_required" in codes


def test_restore_overwrite_creates_pre_restore_backup(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    target = tmp_path / "restore.db"
    original = import_fixture(tmp_path / "existing")
    target.write_bytes(original.read_bytes())
    pre_restore_dir = tmp_path / "pre-restore"

    result = runner.invoke(
        app,
        [
            "restore",
            "--backup",
            str(backup),
            "--target-db",
            str(target),
            "--apply",
            "--overwrite",
            "--pre-restore-backup-dir",
            str(pre_restore_dir),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["pre_restore_backup"]["ok"] is True
    assert Path(payload["pre_restore_backup"]["destination"]).exists()
    assert session_count(target) == session_count(backup)


def test_restore_missing_manifest_requires_explicit_opt_in(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path, with_manifest=False)
    target = tmp_path / "restore.db"

    result = runner.invoke(app, ["restore", "--backup", str(backup), "--target-db", str(target), "--apply", "--json"])

    assert result.exit_code == 1
    assert not target.exists()
    payload = json.loads(result.output)
    assert {error["code"] for error in payload["errors"]} == {"manifest_required"}

    result = runner.invoke(
        app,
        ["restore", "--backup", str(backup), "--target-db", str(target), "--apply", "--allow-missing-manifest", "--json"],
    )

    assert result.exit_code == 0, result.output
    assert target.exists()
    with sqlite3.connect(target) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] >= 1


def test_v22_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-22-safe-restore/plan.md"),
        Path("docs/v0/phases/phase-22-safe-restore/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

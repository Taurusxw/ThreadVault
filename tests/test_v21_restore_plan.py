from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from tests.test_v15_backup import import_fixture
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


def test_restore_plan_valid_backup_with_manifest(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    target = tmp_path / "restored.db"
    payload_path = tmp_path / "restore-plan.json"

    result = runner.invoke(app, ["restore-plan", "--backup", str(backup), "--target-db", str(target), "--json"])

    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["mode"] == "read_only_plan"
    assert payload["backup_verification"]["ok"] is True
    assert payload["manifest_verification"]["ok"] is True
    assert payload["warnings"] == []
    assert not target.exists()

    result = runner.invoke(app, ["validate-json", "--schema", "restore_plan", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_restore_plan_missing_manifest_is_warning(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path, with_manifest=False)
    target = tmp_path / "restored.db"

    result = runner.invoke(app, ["restore-plan", "--backup", str(backup), "--target-db", str(target), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["manifest_verification"]["ok"] is False
    assert payload["warnings"][0]["code"] == "manifest_missing"


def test_restore_plan_existing_target_is_warning(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    target = tmp_path / "existing.db"
    target.write_text("current db placeholder", encoding="utf-8")

    result = runner.invoke(app, ["restore-plan", "--backup", str(backup), "--target-db", str(target), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    codes = {warning["code"] for warning in payload["warnings"]}
    assert "target_exists" in codes
    assert target.read_text(encoding="utf-8") == "current db placeholder"


def test_restore_plan_target_same_as_backup_is_error(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)

    result = runner.invoke(app, ["restore-plan", "--backup", str(backup), "--target-db", str(backup), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "target_same_as_backup"


def test_v21_docs_exist() -> None:
    for path in [
        Path("docs/progress/archive/legacy-v0/phases/phase-21-restore-plan-preflight/plan.md"),
        Path("docs/progress/archive/legacy-v0/phases/phase-21-restore-plan-preflight/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

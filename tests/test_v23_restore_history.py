from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from tests.test_v22_restore import make_backup
from threadvault.cli import app


def test_restore_apply_appends_custom_history_and_schemas_validate(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    target = tmp_path / "restore.db"
    history = tmp_path / "restore-history.jsonl"
    restore_payload = tmp_path / "restore.json"
    history_payload = tmp_path / "restore-history-list.json"

    result = runner.invoke(
        app,
        ["restore", "--backup", str(backup), "--target-db", str(target), "--apply", "--restore-history", str(history), "--json"],
    )

    assert result.exit_code == 0, result.output
    restore_payload.write_text(result.output, encoding="utf-8")
    payload = json.loads(result.output)
    assert payload["history"]["path"] == str(history)
    assert history.exists()
    record = json.loads(history.read_text(encoding="utf-8").strip())
    assert record["backup"] == str(backup)
    assert record["target_db"] == str(target)
    assert record["backup_sha256"]
    assert record["target_sha256"]

    result = runner.invoke(app, ["validate-json", "--schema", "restore", "--input", str(restore_payload), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True

    result = runner.invoke(app, ["restore-history", "list", "--history", str(history), "--json"])
    assert result.exit_code == 0, result.output
    history_payload.write_text(result.output, encoding="utf-8")
    list_payload = json.loads(result.output)
    assert len(list_payload["records"]) == 1
    assert list_payload["warnings"] == []

    result = runner.invoke(app, ["validate-json", "--schema", "restore_history_list", "--input", str(history_payload), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_restore_history_latest_and_malformed_lines(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    history = tmp_path / "restore-history.jsonl"
    first_target = tmp_path / "restore-a.db"
    second_target = tmp_path / "restore-b.db"
    result = runner.invoke(
        app,
        ["restore", "--backup", str(backup), "--target-db", str(first_target), "--apply", "--restore-history", str(history), "--json"],
    )
    assert result.exit_code == 0, result.output
    with history.open("a", encoding="utf-8") as handle:
        handle.write("not-json\n")
    result = runner.invoke(
        app,
        ["restore", "--backup", str(backup), "--target-db", str(second_target), "--apply", "--restore-history", str(history), "--json"],
    )
    assert result.exit_code == 0, result.output

    latest_payload = tmp_path / "restore-history-latest.json"
    result = runner.invoke(app, ["restore-history", "latest", "--history", str(history), "--json"])

    assert result.exit_code == 0, result.output
    latest_payload.write_text(result.output, encoding="utf-8")
    payload = json.loads(result.output)
    assert payload["latest"]["target_db"] == str(second_target)
    assert payload["warnings"][0]["code"] == "invalid_history_json"

    result = runner.invoke(app, ["validate-json", "--schema", "restore_history_latest", "--input", str(latest_payload), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_restore_dry_run_and_failed_restore_do_not_append_history(tmp_path: Path) -> None:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    history = tmp_path / "restore-history.jsonl"
    dry_target = tmp_path / "dry.db"
    existing_target = tmp_path / "existing.db"
    existing_target.write_text("existing", encoding="utf-8")

    result = runner.invoke(
        app,
        ["restore", "--backup", str(backup), "--target-db", str(dry_target), "--restore-history", str(history), "--json"],
    )
    assert result.exit_code == 0, result.output
    assert not history.exists()

    result = runner.invoke(
        app,
        ["restore", "--backup", str(backup), "--target-db", str(existing_target), "--apply", "--restore-history", str(history), "--json"],
    )

    assert result.exit_code == 1
    assert not history.exists()


def test_restore_history_empty_missing_file(tmp_path: Path) -> None:
    runner = CliRunner()
    history = tmp_path / "missing.jsonl"

    result = runner.invoke(app, ["restore-history", "list", "--history", str(history), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["records"] == []
    assert payload["warnings"] == []


def test_v23_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-23-restore-history/plan.md"),
        Path("docs/v0/phases/phase-23-restore-history/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

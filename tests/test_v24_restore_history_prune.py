from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from tests.test_v22_restore import make_backup
from threadvault.cli import app


def seed_restore_history(tmp_path: Path, count: int = 3) -> Path:
    runner = CliRunner()
    backup = make_backup(tmp_path)
    history = tmp_path / "restore-history.jsonl"
    for index in range(count):
        target = tmp_path / f"restore-{index}.db"
        result = runner.invoke(
            app,
            ["restore", "--backup", str(backup), "--target-db", str(target), "--apply", "--restore-history", str(history), "--json"],
        )
        assert result.exit_code == 0, result.output
    return history


def test_restore_history_prune_dry_run_writes_nothing_and_schema_validates(tmp_path: Path) -> None:
    runner = CliRunner()
    history = seed_restore_history(tmp_path)
    before = history.read_text(encoding="utf-8")
    payload_path = tmp_path / "restore-history-prune.json"

    result = runner.invoke(app, ["restore-history", "prune", "--history", str(history), "--keep", "2", "--json"])

    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")
    payload = json.loads(result.output)
    assert payload["apply"] is False
    assert payload["rewritten"] is False
    assert len(payload["kept"]) == 2
    assert len(payload["deletable"]) == 1
    assert history.read_text(encoding="utf-8") == before

    result = runner.invoke(app, ["validate-json", "--schema", "restore_history_prune", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_restore_history_prune_apply_keeps_latest_valid_records(tmp_path: Path) -> None:
    runner = CliRunner()
    history = seed_restore_history(tmp_path)

    result = runner.invoke(app, ["restore-history", "prune", "--history", str(history), "--keep", "1", "--apply", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["rewritten"] is True
    assert len(payload["kept"]) == 1
    lines = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 1
    assert lines[0]["target_db"] == payload["kept"][0]["target_db"]


def test_restore_history_prune_preserves_malformed_lines(tmp_path: Path) -> None:
    runner = CliRunner()
    history = seed_restore_history(tmp_path, count=2)
    with history.open("a", encoding="utf-8") as handle:
        handle.write("not-json\n")

    result = runner.invoke(app, ["restore-history", "prune", "--history", str(history), "--keep", "1", "--apply", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["warnings"][0]["code"] == "invalid_history_json"
    text = history.read_text(encoding="utf-8")
    assert "not-json" in text
    valid_records = [json.loads(line) for line in text.splitlines() if line.startswith("{")]
    assert len(valid_records) == 1


def test_restore_history_prune_missing_history_is_empty_plan(tmp_path: Path) -> None:
    runner = CliRunner()
    history = tmp_path / "missing.jsonl"

    result = runner.invoke(app, ["restore-history", "prune", "--history", str(history), "--keep", "2", "--apply", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["records"] == []
    assert payload["kept"] == []
    assert payload["deletable"] == []
    assert payload["rewritten"] is False
    assert not history.exists()


def test_v24_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-24-restore-history-retention/plan.md"),
        Path("docs/v0/phases/phase-24-restore-history-retention/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

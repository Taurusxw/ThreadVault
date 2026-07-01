from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from tests.test_v24_restore_history_prune import seed_restore_history
from threadvault.cli import app


def write_restore_config(tmp_path: Path, keep: int) -> Path:
    config = tmp_path / "threadvault.toml"
    config.write_text(f"[restore_history]\nkeep = {keep}\n", encoding="utf-8")
    return config


def test_restore_history_prune_uses_config_keep(tmp_path: Path) -> None:
    runner = CliRunner()
    history = seed_restore_history(tmp_path, count=3)
    config = write_restore_config(tmp_path, keep=2)

    result = runner.invoke(app, ["restore-history", "prune", "--history", str(history), "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["keep"] == 2
    assert payload["keep_source"] == "config"
    assert len(payload["kept"]) == 2
    assert len(payload["deletable"]) == 1


def test_restore_history_prune_cli_keep_overrides_config(tmp_path: Path) -> None:
    runner = CliRunner()
    history = seed_restore_history(tmp_path, count=3)
    config = write_restore_config(tmp_path, keep=3)

    result = runner.invoke(
        app,
        ["restore-history", "prune", "--history", str(history), "--config", str(config), "--keep", "1", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["keep"] == 1
    assert payload["keep_source"] == "cli"
    assert len(payload["kept"]) == 1
    assert len(payload["deletable"]) == 2


def test_restore_history_prune_requires_keep_or_config(tmp_path: Path) -> None:
    runner = CliRunner()
    history = seed_restore_history(tmp_path, count=1)
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 2\n", encoding="utf-8")

    result = runner.invoke(app, ["restore-history", "prune", "--history", str(history), "--config", str(config), "--json"])

    assert result.exit_code != 0
    assert "Provide --keep or configure [restore_history].keep" in result.output


def test_restore_history_prune_reports_invalid_config(tmp_path: Path) -> None:
    runner = CliRunner()
    history = seed_restore_history(tmp_path, count=1)
    config = tmp_path / "threadvault.toml"
    config.write_text("[restore_history]\nkeep = true\n", encoding="utf-8")

    result = runner.invoke(app, ["restore-history", "prune", "--history", str(history), "--config", str(config), "--json"])

    assert result.exit_code != 0
    assert "restore_history.keep must be an integer" in result.output


def test_config_show_includes_restore_history_keep(tmp_path: Path) -> None:
    runner = CliRunner()
    config = write_restore_config(tmp_path, keep=9)

    result = runner.invoke(app, ["config", "show", "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["restore_history"]["keep"] == 9


def test_restore_history_prune_schema_includes_keep_source(tmp_path: Path) -> None:
    runner = CliRunner()
    history = seed_restore_history(tmp_path, count=2)
    config = write_restore_config(tmp_path, keep=1)
    payload_path = tmp_path / "restore-history-prune.json"

    result = runner.invoke(app, ["restore-history", "prune", "--history", str(history), "--config", str(config), "--json"])
    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")

    result = runner.invoke(app, ["validate-json", "--schema", "restore_history_prune", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_v25_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-25-restore-history-retention-config/plan.md"),
        Path("docs/v0/phases/phase-25-restore-history-retention-config/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

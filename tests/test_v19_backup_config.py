from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from tests.test_v18_backup_prune import make_backups
from threadvault.cli import app


def test_backup_history_prune_uses_config_keep(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = make_backups(tmp_path)
    config = tmp_path / "threadvault.toml"
    config.write_text("[backup_history]\nkeep = 2\n", encoding="utf-8")

    result = runner.invoke(app, ["backup-history", "prune", "--dir", str(paths[0].parent), "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["keep"] == 2
    assert payload["keep_source"] == "config"
    assert len(payload["kept"]) == 2
    assert len(payload["deletable"]) == 1
    assert all(path.exists() for path in paths)


def test_backup_history_prune_cli_keep_overrides_config(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = make_backups(tmp_path)
    config = tmp_path / "threadvault.toml"
    config.write_text("[backup_history]\nkeep = 1\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["backup-history", "prune", "--dir", str(paths[0].parent), "--config", str(config), "--keep", "2", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["keep"] == 2
    assert payload["keep_source"] == "cli"
    assert len(payload["kept"]) == 2


def test_backup_history_prune_requires_keep_or_config(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = make_backups(tmp_path)
    missing_config = tmp_path / "missing.toml"

    result = runner.invoke(app, ["backup-history", "prune", "--dir", str(paths[0].parent), "--config", str(missing_config), "--json"])

    assert result.exit_code != 0
    assert "Provide --keep or configure [backup_history].keep" in result.output


def test_backup_history_prune_rejects_invalid_config_keep(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = make_backups(tmp_path)
    config = tmp_path / "threadvault.toml"
    config.write_text("[backup_history]\nkeep = true\n", encoding="utf-8")

    result = runner.invoke(app, ["backup-history", "prune", "--dir", str(paths[0].parent), "--config", str(config), "--json"])

    assert result.exit_code != 0
    assert "backup_history.keep must be an integer" in result.output


def test_backup_history_prune_schema_config_show_and_docs(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = make_backups(tmp_path)
    config = tmp_path / "threadvault.toml"
    config.write_text("[backup_history]\nkeep = 2\n", encoding="utf-8")
    payload_path = tmp_path / "backup-prune.json"

    result = runner.invoke(app, ["backup-history", "prune", "--dir", str(paths[0].parent), "--config", str(config), "--json"])
    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")

    result = runner.invoke(app, ["validate-json", "--schema", "backup_history_prune", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True

    result = runner.invoke(app, ["config", "show", "--config", str(config), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["backup_history"]["keep"] == 2

    for path in [
        Path("docs/v0/phases/phase-19-backup-retention-config/plan.md"),
        Path("docs/v0/phases/phase-19-backup-retention-config/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

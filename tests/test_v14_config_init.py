from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.app_config import default_config_template, diagnose_app_config
from threadvault.cli import app


def test_default_config_template_is_valid_and_uses_literal_windows_regex(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text(default_config_template(), encoding="utf-8")

    payload = diagnose_app_config(config)

    assert payload["ok"] is True
    assert "pattern = '^E:\\\\Codex\\\\'" in default_config_template()


def test_config_init_creates_template_and_validates_schema(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    payload_path = tmp_path / "config-init.json"

    result = runner.invoke(app, ["config", "init", "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["created"] is True
    assert payload["overwritten"] is False
    assert payload["doctor"]["ok"] is True
    assert config.exists()

    result = runner.invoke(app, ["validate-json", "--schema", "config_init", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_config_init_refuses_existing_without_force(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 9\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "init", "--config", str(config), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["error"] == "config_exists"
    assert payload["created"] is False
    assert config.read_text(encoding="utf-8") == "[audit_history]\nkeep = 9\n"


def test_config_init_force_overwrites_existing(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 9\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "init", "--config", str(config), "--force", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["created"] is False
    assert payload["overwritten"] is True
    assert "keep = 20" in config.read_text(encoding="utf-8")


def test_readme_uses_literal_string_for_windows_regex() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    assert "pattern = '^E:\\\\\\\\Codex\\\\\\\\'" in text
    assert 'pattern = "^E:\\\\\\\\Codex\\\\\\\\"' not in text


def test_v14_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-14-config-init-template/plan.md"),
        Path("docs/v0/phases/phase-14-config-init-template/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

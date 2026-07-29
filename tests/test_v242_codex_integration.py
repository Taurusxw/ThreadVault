from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.codex_integration import (
    build_hook_command,
    codex_integration_status,
    install_codex_integration,
)
from threadvault.schemas import validate_payload


def _executable(tmp_path: Path) -> Path:
    executable = tmp_path / "threadvault.exe"
    executable.write_bytes(b"test executable")
    return executable


def test_codex_integration_dry_run_plans_hook_and_mcp_without_writing(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    db = tmp_path / "threadvault.db"
    executable = _executable(tmp_path)

    payload = install_codex_integration(
        codex_home,
        db,
        threadvault_executable=executable,
    )

    assert payload["ok"] is True
    assert payload["applied"] is False
    assert payload["hook"]["action"] == "created"
    assert payload["mcp"]["action"] == "created"
    assert payload["restart_required"] is False
    assert payload["hook_trust_required"] is False
    assert not (codex_home / "hooks.json").exists()
    assert not (codex_home / "config.toml").exists()
    assert validate_payload("codex_integration_install", payload)["ok"] is True


def test_codex_integration_status_detects_exact_pinned_config(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    codex_home.mkdir()
    db = tmp_path / "threadvault.db"
    executable = _executable(tmp_path)
    command = build_hook_command(executable, db)
    (codex_home / "hooks.json").write_text(
        json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": command}]}]}}),
        encoding="utf-8",
    )
    quoted_executable = str(executable).replace("\\", "\\\\")
    quoted_db = str(db).replace("\\", "\\\\")
    (codex_home / "config.toml").write_text(
        f'[mcp_servers.threadvault]\ncommand = "{quoted_executable}"\nargs = ["mcp", "serve", "--db", "{quoted_db}"]\n',
        encoding="utf-8",
    )

    payload = codex_integration_status(codex_home, db, threadvault_executable=executable)

    assert payload["ok"] is True
    assert payload["hook"]["matches"] is True
    assert payload["mcp"]["matches"] is True
    assert payload["healthy"] is False
    assert "review_and_trust_hook_in_slash_hooks" in payload["recommended_actions"]
    assert validate_payload("codex_integration_status", payload)["ok"] is True


def test_codex_install_cli_is_dry_run_by_default(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    db = tmp_path / "threadvault.db"
    executable = _executable(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "codex", "install", "--codex-home", str(codex_home), "--db", str(db),
            "--threadvault-executable", str(executable), "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["applied"] is False
    assert payload["hook"]["action"] == "created"
    assert payload["mcp"]["action"] == "created"

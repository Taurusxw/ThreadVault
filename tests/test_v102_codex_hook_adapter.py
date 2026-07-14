from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.codex_hooks import build_codex_hook_config, handle_codex_hook_payload, infer_codex_home, install_codex_hook
from threadvault.database import connect, init_db
from threadvault.schemas import validate_payload

FIXTURES = Path("tests/fixtures/codex_home")


def hook_payload(transcript_path: Path | None = None) -> dict:
    return {
        "session_id": "hook-session",
        "transcript_path": str(transcript_path or (FIXTURES / "sessions" / "current.jsonl")),
        "cwd": "E:\\Codex\\ThreadVault",
        "hook_event_name": "Stop",
        "model": "gpt-test",
    }


def test_infer_codex_home_from_transcript_path() -> None:
    assert infer_codex_home(FIXTURES / "sessions" / "current.jsonl") == FIXTURES
    assert infer_codex_home(FIXTURES / "archived_sessions" / "legacy.jsonl") == FIXTURES
    assert infer_codex_home("not-under-session/current.jsonl") is None


def test_hook_handler_enqueues_stop_payload_without_importing(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    with connect(db) as conn:
        init_db(conn)
        result = handle_codex_hook_payload(conn, hook_payload())
        sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        queued = conn.execute("SELECT COUNT(*) FROM ingestion_queue").fetchone()[0]

    assert result["ok"] is True
    assert result["hook_event_name"] == "Stop"
    assert result["codex_home"] == str(FIXTURES)
    assert result["enqueue"]["enqueued"] is True
    assert result["enqueue"]["request"]["reason"] == "codex-hook:Stop"
    assert result["hook_response"] == {"continue": True}
    assert queued == 1
    assert sessions == 0


def test_hook_handler_apply_imports_only_named_transcript_and_completes_queue(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    with connect(db) as conn:
        init_db(conn)
        result = handle_codex_hook_payload(conn, hook_payload(), apply=True)
        sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        queued = conn.execute("SELECT status, attempts FROM ingestion_queue").fetchone()

    assert result["ok"] is True
    assert result["process"]["status"] == "completed"
    assert result["process"]["import_stats"]["discovered"] == 1
    assert result["process"]["import_stats"]["imported"] == 1
    assert sessions == 1
    assert dict(queued) == {"status": "completed", "attempts": 1}


def test_codex_hook_cli_default_stdout_is_hook_compatible_json(tmp_path: Path) -> None:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"

    result = runner.invoke(app, ["codex-hook", "ingest", "--db", str(db)], input=json.dumps(hook_payload()))

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"continue": True}

    list_result = runner.invoke(app, ["ingest-queue", "list", "--db", str(db), "--json"])
    assert list_result.exit_code == 0, list_result.output
    queued = json.loads(list_result.output)
    assert queued["count"] == 1
    assert queued["requests"][0]["reason"] == "codex-hook:Stop"


def test_codex_hook_cli_apply_imports_transcript(tmp_path: Path) -> None:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"

    result = runner.invoke(
        app,
        ["codex-hook", "ingest", "--db", str(db), "--apply"],
        input=json.dumps(hook_payload()),
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"continue": True}
    with connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1
        assert conn.execute("SELECT status FROM ingestion_queue").fetchone()[0] == "completed"


def test_codex_hook_cli_diagnostic_json_validates(tmp_path: Path) -> None:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"

    result = runner.invoke(
        app,
        ["codex-hook", "ingest", "--db", str(db), "--diagnostic-json"],
        input=json.dumps(hook_payload()),
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("codex_hook_ingest", payload)["ok"] is True
    assert payload["enqueue"]["enqueued"] is True
    assert payload["hook_response"] == {"continue": True}


def test_codex_hook_cli_invalid_stdin_continues_without_enqueue(tmp_path: Path) -> None:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"

    result = runner.invoke(app, ["codex-hook", "ingest", "--db", str(db)], input="{not json")

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"continue": True}

    list_result = runner.invoke(app, ["ingest-queue", "list", "--db", str(db), "--json"])
    assert list_result.exit_code == 0, list_result.output
    assert json.loads(list_result.output)["count"] == 0


def test_codex_hook_config_shape_and_schema() -> None:
    config = build_codex_hook_config("threadvault codex-hook ingest --apply --db vault.db", timeout=7)

    assert validate_payload("codex_hook_config", config)["ok"] is True
    hook = config["hooks"]["Stop"][0]["hooks"][0]
    assert hook["type"] == "command"
    assert hook["command"] == "threadvault codex-hook ingest --apply --db vault.db"
    assert hook["timeout"] == 7


def test_codex_hook_config_cli_json_validates(tmp_path: Path) -> None:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"

    result = runner.invoke(app, ["codex-hook", "config", "--db", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("codex_hook_config", payload)["ok"] is True
    command = payload["hooks"]["Stop"][0]["hooks"][0]["command"]
    assert "threadvault codex-hook ingest --apply" in command
    assert str(db) in command


def test_codex_hook_install_is_dry_run_by_default_and_idempotent(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    command = '"C:\\ThreadVault\\threadvault.exe" codex-hook ingest --apply --db "C:\\vault.db"'

    planned = install_codex_hook(codex_home, command)
    assert planned["apply"] is False
    assert planned["action"] == "created"
    assert not (codex_home / "hooks.json").exists()

    installed = install_codex_hook(codex_home, command, apply=True)
    assert validate_payload("codex_hook_install", installed)["ok"] is True
    assert installed["action"] == "created"
    assert installed["trust_required"] is True

    repeated = install_codex_hook(codex_home, command, apply=True)
    assert repeated["action"] == "unchanged"
    config = json.loads((codex_home / "hooks.json").read_text(encoding="utf-8"))
    handlers = config["hooks"]["Stop"][0]["hooks"]
    assert len(handlers) == 1
    assert handlers[0]["command"] == command


def test_codex_hook_install_preserves_non_threadvault_handlers(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    codex_home.mkdir()
    existing = {
        "hooks": {
            "Stop": [{"hooks": [{"type": "command", "command": "other-tool stop"}]}],
            "SessionStart": [{"hooks": [{"type": "command", "command": "other-tool start"}]}],
        }
    }
    (codex_home / "hooks.json").write_text(json.dumps(existing), encoding="utf-8")

    installed = install_codex_hook(codex_home, "threadvault codex-hook ingest --apply", apply=True)

    assert installed["action"] == "updated"
    config = installed["config"]
    assert config["hooks"]["SessionStart"] == existing["hooks"]["SessionStart"]
    stop_commands = [handler["command"] for group in config["hooks"]["Stop"] for handler in group["hooks"]]
    assert stop_commands == ["other-tool stop", "threadvault codex-hook ingest --apply"]


def test_capabilities_and_schema_registry_include_codex_hook_adapter() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["capabilities", "--json"])
    assert result.exit_code == 0, result.output
    capabilities = json.loads(result.output)
    assert "codex-hook" in capabilities["commands"]
    assert "codex-hook ingest" in capabilities["json_outputs"]
    assert capabilities["feature_flags"]["codex_hook_adapter"] is True

    result = runner.invoke(app, ["schemas", "list", "--json"])
    assert result.exit_code == 0, result.output
    schemas = json.loads(result.output)["schemas"]
    assert "codex_hook_ingest" in schemas
    assert "codex_hook_config" in schemas
    assert "codex_hook_install" in schemas


def test_v102_docs_exist() -> None:
    for path in [
        Path("docs/progress/archive/legacy-v1/README.md"),
        Path("docs/progress/archive/legacy-v1/phases/phase-02-codex-hook-adapter/plan.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"

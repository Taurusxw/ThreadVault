from __future__ import annotations

import json
import os
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .codex_hooks import install_codex_hook
from .source_sync import inspect_source_freshness

CODEX_INTEGRATION_CONTRACT_VERSION = "codex-integration.v1"
MCP_SERVER_NAME = "threadvault"


def resolve_threadvault_executable(value: Path | None = None) -> Path:
    if value is not None:
        candidate = value.expanduser().resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f"ThreadVault executable not found: {candidate}")
        return candidate
    script_name = "threadvault.exe" if os.name == "nt" else "threadvault"
    sibling = Path(sys.executable).resolve().with_name(script_name)
    if sibling.is_file():
        return sibling
    discovered = shutil.which("threadvault")
    if discovered:
        return Path(discovered).resolve()
    raise FileNotFoundError("ThreadVault executable was not found beside Python or on PATH.")


def build_hook_command(executable: Path, db_path: Path) -> str:
    parts = [str(executable), "codex-hook", "ingest", "--apply", "--db", str(db_path)]
    if os.name == "nt":
        return f'"{executable}" codex-hook ingest --apply --db "{db_path}"'
    return shlex.join(parts)


def codex_integration_status(
    codex_home: Path,
    db_path: Path,
    *,
    threadvault_executable: Path | None = None,
) -> dict[str, Any]:
    codex_home = codex_home.expanduser().resolve()
    db_path = db_path.expanduser().resolve()
    executable = resolve_threadvault_executable(threadvault_executable)
    hook_command = build_hook_command(executable, db_path)
    hook = _hook_status(codex_home / "hooks.json", hook_command)
    mcp = _mcp_status(codex_home / "config.toml", executable, db_path)
    freshness = inspect_source_freshness(db_path, codex_home=codex_home)
    observed = _latest_hook_activity(db_path)
    observed["current"] = _timestamp_at_or_after(observed["processed_at"], freshness["latest_source_mtime"])
    actions: list[str] = []
    if not hook["matches"] or not mcp["matches"]:
        actions.append("run_threadvault_codex_install")
    if hook["configured"] and not observed["current"]:
        actions.append("review_and_trust_hook_in_slash_hooks")
    if not freshness["fresh"]:
        actions.append("run_storage_sync")
    if mcp["matches"]:
        actions.append("restart_codex_after_mcp_change_if_not_already_restarted")
    configured = bool(hook["matches"] and mcp["matches"])
    healthy = bool(configured and freshness["fresh"] and observed["current"])
    return {
        "contract_version": CODEX_INTEGRATION_CONTRACT_VERSION,
        "ok": configured,
        "healthy": healthy,
        "codex_home": str(codex_home),
        "db_path": str(db_path),
        "threadvault_executable": str(executable),
        "hook": hook | {"activity": observed},
        "mcp": mcp,
        "source_freshness": freshness,
        "recommended_actions": actions,
    }


def install_codex_integration(
    codex_home: Path,
    db_path: Path,
    *,
    threadvault_executable: Path | None = None,
    codex_executable: Path | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or install the pinned Stop hook and read-only MCP server together."""

    codex_home = codex_home.expanduser().resolve()
    db_path = db_path.expanduser().resolve()
    executable = resolve_threadvault_executable(threadvault_executable)
    hook_command = build_hook_command(executable, db_path)
    hook = install_codex_hook(codex_home, hook_command, timeout=30, apply=apply)
    mcp = install_codex_mcp(
        codex_home,
        executable,
        db_path,
        codex_executable=codex_executable,
        apply=apply,
    )
    status = codex_integration_status(
        codex_home,
        db_path,
        threadvault_executable=executable,
    )
    return {
        "contract_version": CODEX_INTEGRATION_CONTRACT_VERSION,
        "ok": bool(hook["ok"] and mcp["ok"]),
        "applied": apply,
        "hook": hook,
        "mcp": mcp,
        "status": status,
        "restart_required": bool(apply and mcp["action"] != "unchanged"),
        "hook_trust_required": bool(apply and hook["action"] != "unchanged"),
    }


def install_codex_mcp(
    codex_home: Path,
    threadvault_executable: Path,
    db_path: Path,
    *,
    codex_executable: Path | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    config_path = codex_home / "config.toml"
    before = _mcp_status(config_path, threadvault_executable, db_path)
    action = "unchanged" if before["matches"] else ("updated" if before["configured"] else "created")
    base = {
        "ok": True,
        "apply": apply,
        "action": action,
        "config_path": str(config_path),
        "name": MCP_SERVER_NAME,
        "command": str(threadvault_executable),
        "args": ["mcp", "serve", "--db", str(db_path)],
    }
    if not apply or action == "unchanged":
        return base

    codex = _resolve_codex_executable(codex_executable)
    existed = config_path.is_file()
    original = config_path.read_bytes() if existed else None
    try:
        if before["configured"]:
            _run_codex([str(codex), "mcp", "remove", MCP_SERVER_NAME])
        _run_codex(
            [
                str(codex),
                "mcp",
                "add",
                MCP_SERVER_NAME,
                "--",
                str(threadvault_executable),
                "mcp",
                "serve",
                "--db",
                str(db_path),
            ]
        )
    except Exception:
        _restore_config(config_path, original, existed)
        raise
    after = _mcp_status(config_path, threadvault_executable, db_path)
    return base | {"ok": bool(after["matches"]), "installed": after}


def _hook_status(path: Path, expected_command: str) -> dict[str, Any]:
    configured_commands: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        for group in (payload.get("hooks") or {}).get("Stop") or []:
            if not isinstance(group, dict):
                continue
            for handler in group.get("hooks") or []:
                if not isinstance(handler, dict):
                    continue
                command = handler.get("commandWindows") or handler.get("command_windows") or handler.get("command")
                if isinstance(command, str) and "threadvault" in command.lower() and "codex-hook ingest" in command:
                    configured_commands.append(command)
    except (OSError, TypeError, json.JSONDecodeError):
        pass
    return {
        "path": str(path),
        "configured": bool(configured_commands),
        "matches": expected_command in configured_commands,
        "command": configured_commands[0] if configured_commands else None,
        "expected_command": expected_command,
        "trust_state": "not_programmatically_observable",
    }


def _mcp_status(config_path: Path, executable: Path, db_path: Path) -> dict[str, Any]:
    entry: dict[str, Any] = {}
    try:
        if config_path.is_file():
            with config_path.open("rb") as handle:
                entry = dict((tomllib.load(handle).get("mcp_servers") or {}).get(MCP_SERVER_NAME) or {})
    except (OSError, TypeError, tomllib.TOMLDecodeError):
        entry = {}
    args = [str(item) for item in entry.get("args") or []]
    command = entry.get("command")
    expected_args = ["mcp", "serve", "--db", str(db_path)]
    command_matches = isinstance(command, str) and _path_key(Path(command)) == _path_key(executable)
    return {
        "config_path": str(config_path),
        "configured": bool(entry),
        "enabled": bool(entry) and entry.get("enabled", True) is not False,
        "matches": bool(entry and command_matches and args == expected_args and entry.get("enabled", True) is not False),
        "command": command,
        "args": args,
        "expected_command": str(executable),
        "expected_args": expected_args,
    }


def _latest_hook_activity(db_path: Path) -> dict[str, Any]:
    if not db_path.is_file():
        return {"observed": False, "status": None, "processed_at": None, "request_id": None}
    try:
        conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                """
                SELECT request_id, status, processed_at
                FROM ingestion_queue
                WHERE source = 'codex-hook'
                ORDER BY request_id DESC LIMIT 1
                """
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        row = None
    return {
        "observed": row is not None,
        "status": row["status"] if row is not None else None,
        "processed_at": row["processed_at"] if row is not None else None,
        "request_id": row["request_id"] if row is not None else None,
    }


def _timestamp_at_or_after(value: Any, reference: Any) -> bool:
    if not isinstance(value, str) or not value.strip() or not isinstance(reference, str) or not reference.strip():
        return False
    try:
        candidate = datetime.fromisoformat(value.replace("Z", "+00:00"))
        target = datetime.fromisoformat(reference.replace("Z", "+00:00"))
    except ValueError:
        return False
    if candidate.tzinfo is None:
        candidate = candidate.replace(tzinfo=UTC)
    if target.tzinfo is None:
        target = target.replace(tzinfo=UTC)
    return candidate.astimezone(UTC) >= target.astimezone(UTC)


def _resolve_codex_executable(value: Path | None) -> Path:
    if value is not None:
        candidate = value.expanduser().resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f"Codex executable not found: {candidate}")
        return candidate
    discovered = shutil.which("codex")
    if not discovered:
        raise FileNotFoundError("Codex CLI was not found on PATH.")
    return Path(discovered).resolve()


def _run_codex(command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    if completed.returncode:
        message = completed.stderr.strip() or completed.stdout.strip() or f"Codex command failed with exit code {completed.returncode}."
        raise RuntimeError(message)
    return completed


def _restore_config(path: Path, original: bytes | None, existed: bool) -> None:
    if existed and original is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".toml.threadvault-rollback")
        temporary.write_bytes(original)
        temporary.replace(path)
    elif path.exists():
        path.unlink()


def _path_key(path: Path) -> str:
    return os.path.normcase(str(path.expanduser().resolve()))

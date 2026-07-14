from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .ingestion import IngestionRequest, enqueue_ingestion, process_ingestion_request

DEFAULT_HOOK_COMMAND = "threadvault codex-hook ingest --apply"
DEFAULT_HOOK_STATUS_MESSAGE = "Archiving this Codex turn in ThreadVault"


def handle_codex_hook_payload(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    codex_home: Path | None = None,
    source: str = "codex-hook",
    apply: bool = False,
) -> dict[str, Any]:
    hook_event_name = _clean_event_name(payload.get("hook_event_name"))
    inferred_codex_home = codex_home or infer_codex_home(payload.get("transcript_path"))
    enqueue_payload = enqueue_ingestion(
        conn,
        IngestionRequest(
            source=source,
            codex_home=inferred_codex_home,
            reason=f"codex-hook:{hook_event_name}",
        ),
    )
    process_payload = None
    transcript_path = _transcript_path(payload.get("transcript_path"))
    if apply and transcript_path is not None:
        process_payload = process_ingestion_request(
            conn,
            int(enqueue_payload["request"]["request_id"]),
            codex_home=inferred_codex_home,
            transcript_path=transcript_path,
        )
    return {
        "ok": True,
        "hook_event_name": hook_event_name,
        "session_id": payload.get("session_id"),
        "codex_home": str(inferred_codex_home) if inferred_codex_home is not None else None,
        "enqueue": enqueue_payload,
        "process": process_payload,
        "hook_response": hook_continue_response(),
    }


def invalid_hook_payload_result(error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "hook_event_name": None,
        "session_id": None,
        "codex_home": None,
        "enqueue": None,
        "process": None,
        "error": error,
        "hook_response": hook_continue_response(),
    }


def hook_continue_response() -> dict[str, Any]:
    return {"continue": True}


def build_codex_hook_config(
    command: str = DEFAULT_HOOK_COMMAND,
    *,
    timeout: int = 10,
    status_message: str = DEFAULT_HOOK_STATUS_MESSAGE,
) -> dict[str, Any]:
    timeout = max(1, timeout)
    hook: dict[str, Any] = {
        "type": "command",
        "command": command,
        "timeout": timeout,
    }
    if status_message:
        hook["statusMessage"] = status_message
    return {"hooks": {"Stop": [{"hooks": [hook]}]}}


def install_codex_hook(
    codex_home: Path,
    command: str = DEFAULT_HOOK_COMMAND,
    *,
    timeout: int = 30,
    status_message: str = DEFAULT_HOOK_STATUS_MESSAGE,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or install one idempotent user-level ThreadVault Stop hook."""
    hooks_path = codex_home.expanduser().resolve() / "hooks.json"
    existing: dict[str, Any] = {}
    if hooks_path.exists():
        loaded = json.loads(hooks_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError(f"Codex hooks file must contain a JSON object: {hooks_path}")
        existing = loaded

    desired = dict(existing)
    hooks = dict(desired.get("hooks") or {})
    stop_groups = []
    for group in hooks.get("Stop") or []:
        if not isinstance(group, dict):
            stop_groups.append(group)
            continue
        handlers = [
            handler
            for handler in group.get("hooks") or []
            if not _is_threadvault_ingest_handler(handler)
        ]
        if handlers:
            stop_groups.append(group | {"hooks": handlers})
    stop_groups.extend(build_codex_hook_config(command, timeout=timeout, status_message=status_message)["hooks"]["Stop"])
    hooks["Stop"] = stop_groups
    desired["hooks"] = hooks

    action = "unchanged" if desired == existing else ("created" if not hooks_path.exists() else "updated")
    if apply and action != "unchanged":
        hooks_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = hooks_path.with_suffix(".json.tmp")
        temp_path.write_text(json.dumps(desired, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp_path.replace(hooks_path)
    return {
        "ok": True,
        "apply": apply,
        "path": str(hooks_path),
        "action": action,
        "config": desired,
        "trust_required": True,
    }


def infer_codex_home(transcript_path: Any) -> Path | None:
    path = _transcript_path(transcript_path)
    if path is None:
        return None
    for index, part in enumerate(path.parts):
        if part in {"sessions", "archived_sessions"}:
            if index == 0:
                return None
            return Path(*path.parts[:index])
    return None


def _transcript_path(value: Any) -> Path | None:
    if isinstance(value, Path):
        return value.expanduser()
    if isinstance(value, str) and value.strip():
        return Path(value).expanduser()
    return None


def _clean_event_name(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "unknown"


def _is_threadvault_ingest_handler(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    command = value.get("commandWindows") or value.get("command_windows") or value.get("command")
    return isinstance(command, str) and "codex-hook ingest" in command and "threadvault" in command.lower()

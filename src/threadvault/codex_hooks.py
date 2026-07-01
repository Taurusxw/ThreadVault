from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .ingestion import IngestionRequest, enqueue_ingestion

DEFAULT_HOOK_COMMAND = "threadvault codex-hook ingest"
DEFAULT_HOOK_STATUS_MESSAGE = "Queueing ThreadVault ingestion"


def handle_codex_hook_payload(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    codex_home: Path | None = None,
    source: str = "codex-hook",
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
    return {
        "ok": True,
        "hook_event_name": hook_event_name,
        "session_id": payload.get("session_id"),
        "codex_home": str(inferred_codex_home) if inferred_codex_home is not None else None,
        "enqueue": enqueue_payload,
        "hook_response": hook_continue_response(),
    }


def invalid_hook_payload_result(error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "hook_event_name": None,
        "session_id": None,
        "codex_home": None,
        "enqueue": None,
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


def infer_codex_home(transcript_path: Any) -> Path | None:
    if isinstance(transcript_path, Path):
        path = transcript_path.expanduser()
    elif isinstance(transcript_path, str) and transcript_path.strip():
        path = Path(transcript_path).expanduser()
    else:
        return None
    for index, part in enumerate(path.parts):
        if part in {"sessions", "archived_sessions"}:
            if index == 0:
                return None
            return Path(*path.parts[:index])
    return None


def _clean_event_name(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "unknown"

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from .config import default_codex_home

THREAD_COLUMNS = [
    "id",
    "rollout_path",
    "created_at",
    "updated_at",
    "source",
    "thread_source",
    "model_provider",
    "cwd",
    "title",
    "preview",
    "archived",
    "model",
    "agent_path",
]


def state_candidates(codex_home: Path | None = None) -> list[Path]:
    home = (codex_home or default_codex_home()).expanduser()
    candidates: list[Path] = []
    sqlite_home = os.environ.get("CODEX_SQLITE_HOME")
    if sqlite_home:
        candidates.append(Path(sqlite_home).expanduser() / "state_5.sqlite")
    candidates.append(home / "state_5.sqlite")
    return candidates


def inspect_state(codex_home: Path | None = None) -> dict[str, Any]:
    for candidate in state_candidates(codex_home):
        if not candidate.exists():
            continue
        try:
            with _connect_readonly(candidate) as conn:
                tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                table_columns = {
                    table: [row[1] for row in conn.execute(f'PRAGMA table_info("{_quote_identifier(table)}")')]
                    for table in tables[:50]
                }
            return {"path": str(candidate), "ok": True, "tables": tables, "columns": table_columns}
        except sqlite3.DatabaseError as exc:
            return {"path": str(candidate), "ok": False, "error": str(exc)}
    return {"ok": False, "message": "state_5.sqlite not found"}


def load_state_threads(codex_home: Path | None = None) -> dict[Path, dict[str, Any]]:
    for candidate in state_candidates(codex_home):
        if not candidate.exists():
            continue
        try:
            with _connect_readonly(candidate) as conn:
                tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if "threads" not in tables:
                    return {}
                columns = {row[1] for row in conn.execute('PRAGMA table_info("threads")')}
                if "rollout_path" not in columns:
                    return {}
                selected = [column for column in THREAD_COLUMNS if column in columns]
                quoted = ", ".join(f'"{_quote_identifier(column)}"' for column in selected)
                rows = conn.execute(f"SELECT {quoted} FROM threads WHERE rollout_path IS NOT NULL").fetchall()
                result: dict[Path, dict[str, Any]] = {}
                for row in rows:
                    data = dict(row)
                    rollout_path = data.get("rollout_path")
                    if rollout_path:
                        result[Path(rollout_path).expanduser().resolve()] = data
                return result
        except (OSError, sqlite3.DatabaseError):
            return {}
    return {}


def _connect_readonly(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _quote_identifier(value: str) -> str:
    return value.replace('"', '""')

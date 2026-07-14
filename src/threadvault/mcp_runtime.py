from __future__ import annotations

import platform
import sqlite3
import sys
from pathlib import Path
from typing import Any

from .agent_interface import AgentRetrievalRequest, agent_retrieve
from .app_config import load_app_config
from .client_interface import client_export_preview, client_session_detail
from .config import default_codex_home, discover_session_dirs
from .database import (
    REQUIRED_INDEXES,
    REQUIRED_TABLES,
    REQUIRED_TRIGGERS,
    SCHEMA_VERSION,
    connect_readonly,
    get_events_filtered,
    get_session,
    list_warnings,
    search_index_stats,
    warning_summary,
)
from .database import (
    stats as database_stats,
)
from .export_targets import ExportTargetRequest, preview_export_target
from .state import inspect_state
from .summarizer import build_summary


class McpReadOnlyArchive:
    """The MCP data seam: existing databases only, with persistent writes disabled."""

    def __init__(self, db_path: Path, config_path: Path | None = None):
        self.db_path = db_path.expanduser()
        self.config_path = config_path

    def stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            return database_stats(conn)

    def doctor(self, codex_home: Path | None = None, *, local_debug: bool = False) -> dict[str, Any]:
        home = (codex_home or default_codex_home()).expanduser()
        with self._connect() as conn:
            result = _read_only_doctor(conn)

        session_dirs = discover_session_dirs(home)
        readable_files: list[str] = []
        missing_dirs: list[str] = []
        for session_dir in session_dirs:
            if not session_dir.exists():
                missing_dirs.append(str(session_dir))
                continue
            readable_files.extend(str(path) for path in session_dir.rglob("*.jsonl") if path.is_file())

        result.update(
            {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "db_path": str(self.db_path),
                "codex_home": str(home),
                "session_dirs": [str(path) for path in session_dirs],
                "missing_session_dirs": missing_dirs,
                "jsonl_files": len(readable_files),
                "codex_state": inspect_state(home),
            }
        )
        return result if local_debug else _redact_doctor_paths(result)

    def retrieve(
        self,
        *,
        query: str,
        mode: str,
        limit: int,
        vector_limit: int,
        session_id: str | None,
        cwd: str | None,
        since: str | None,
        until: str | None,
        top_type: str | None,
        tool: str | None,
        local_debug: bool,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            return agent_retrieve(
                conn,
                AgentRetrievalRequest(
                    text=query,
                    mode=mode,
                    limit=limit,
                    vector_limit=vector_limit,
                    session_id=session_id,
                    cwd=cwd,
                    since=since,
                    until=until,
                    top_type=top_type,
                    tool=tool,
                    local_debug=local_debug,
                ),
                load_app_config(self.config_path),
            )

    def session(
        self,
        *,
        session_id: str,
        event_limit: int,
        max_chars: int,
        local_debug: bool,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            session = get_session(conn, session_id)
            if session is None:
                raise KeyError(session_id)
            events = get_events_filtered(conn, session_id)
            warning_count = len(list_warnings(conn, session_id=session_id, limit=100000))
            summary = build_summary(session, events)
            session_payload = dict(session)
            session_payload["event_count"] = len(events)
            session_payload["warning_count"] = warning_count
            return client_session_detail(
                session=session_payload,
                summary=summary,
                events=events,
                event_limit=event_limit,
                max_chars=max_chars,
                local_debug=local_debug,
            )

    def export_preview(self, request: ExportTargetRequest) -> dict[str, Any]:
        with self._connect() as conn:
            preview = preview_export_target(conn, request)
        return client_export_preview(preview, _export_preview_execute_command(request))

    def _connect(self) -> sqlite3.Connection:
        if not self.db_path.is_file():
            raise FileNotFoundError("Archive database is unavailable.")
        conn = connect_readonly(self.db_path)
        conn.execute("PRAGMA query_only = ON")
        return conn


def _read_only_doctor(conn: sqlite3.Connection) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    maintenance_suggestions: list[dict[str, str]] = []
    fts_available = bool(conn.execute("SELECT EXISTS(SELECT 1 FROM pragma_module_list WHERE name = 'fts5')").fetchone()[0])
    checks.append(
        {
            "name": "sqlite_fts5",
            "ok": fts_available,
            "message": "FTS5 is available." if fts_available else "FTS5 is unavailable.",
        }
    )
    ok = fts_available

    schema_row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    schema_version = schema_row["value"] if schema_row else None
    schema_ok = schema_version == str(SCHEMA_VERSION)
    ok = ok and schema_ok
    checks.append(
        {
            "name": "schema_version",
            "ok": schema_ok,
            "message": f"expected {SCHEMA_VERSION}, found {schema_version}",
        }
    )
    if not schema_ok:
        maintenance_suggestions.append(
            {
                "code": "schema_version_mismatch",
                "message": "Back up the database, then run threadvault init with the current version.",
            }
        )

    objects = _sqlite_objects(conn)
    for kind, required in (
        ("table", REQUIRED_TABLES),
        ("index", REQUIRED_INDEXES),
        ("trigger", REQUIRED_TRIGGERS),
    ):
        missing = sorted(required - objects[kind])
        present_ok = not missing
        ok = ok and present_ok
        checks.append(
            {
                "name": f"{kind}s_present",
                "ok": present_ok,
                "message": "all required objects present" if present_ok else f"missing: {', '.join(missing)}",
            }
        )
        if missing:
            maintenance_suggestions.append(
                {
                    "code": f"missing_{kind}s",
                    "message": "Back up the database before reinitializing schema objects.",
                }
            )

    event_count = conn.execute("SELECT COUNT(*) AS count FROM events").fetchone()["count"]
    fts_count = conn.execute("SELECT COUNT(*) AS count FROM events_fts").fetchone()["count"]
    fts_ok = event_count == fts_count
    ok = ok and fts_ok
    checks.append(
        {
            "name": "fts_index_count",
            "ok": fts_ok,
            "message": f"events={event_count}, events_fts={fts_count}",
        }
    )
    if not fts_ok:
        maintenance_suggestions.append(
            {
                "code": "fts_count_mismatch",
                "message": "Run threadvault reindex --fts-only after backing up the database.",
            }
        )

    warning_count = conn.execute("SELECT COUNT(*) AS count FROM parse_warnings").fetchone()["count"]
    parse_health = {
        "events": event_count,
        "warnings": warning_count,
        "warning_codes_top": warning_summary(conn)[:10],
        "warning_ratio": (warning_count / event_count) if event_count else 0,
    }
    index_health = search_index_stats(conn)
    if warning_count > event_count and event_count:
        maintenance_suggestions.append(
            {
                "code": "high_warning_ratio",
                "message": "Run threadvault warnings --summary --json and inspect parser warning codes.",
            }
        )
    return {
        "ok": ok,
        "checks": checks,
        "stats": database_stats(conn),
        "parse_health": parse_health,
        "search_index": index_health,
        "schema_version": SCHEMA_VERSION,
        "schema_objects": {key: sorted(value) for key, value in objects.items()},
        "maintenance_suggestions": maintenance_suggestions,
    }


def _sqlite_objects(conn: sqlite3.Connection) -> dict[str, set[str]]:
    rows = conn.execute("SELECT type, name FROM sqlite_master WHERE type IN ('table', 'index', 'trigger')").fetchall()
    objects: dict[str, set[str]] = {"table": set(), "index": set(), "trigger": set()}
    for row in rows:
        if row["name"].startswith("sqlite_"):
            continue
        objects[row["type"]].add(row["name"])
    return objects


def _redact_doctor_paths(payload: dict[str, Any]) -> dict[str, Any]:
    state = payload.get("codex_state")
    sensitive_values = [
        payload.get("db_path"),
        payload.get("codex_home"),
        *payload.get("session_dirs", []),
        *payload.get("missing_session_dirs", []),
        state.get("path") if isinstance(state, dict) else None,
    ]
    variants = {
        variant
        for value in sensitive_values
        if isinstance(value, str) and value
        for variant in (value, value.replace("\\", "/"), value.replace("/", "\\"))
    }
    _redact_path_strings(payload, sorted(variants, key=len, reverse=True))
    payload["db_path"] = "<redacted:threadvault-db>"
    payload["codex_home"] = "<redacted:codex-home>"
    payload["session_dirs"] = ["<redacted:session-dir>" for _ in payload["session_dirs"]]
    payload["missing_session_dirs"] = ["<redacted:session-dir>" for _ in payload["missing_session_dirs"]]
    state = payload.get("codex_state")
    if isinstance(state, dict) and "path" in state:
        state["path"] = "<redacted:codex-state-db>"
    return payload


def _redact_path_strings(value: Any, sensitive_paths: list[str]) -> Any:
    if isinstance(value, dict):
        for key, item in value.items():
            value[key] = _redact_path_strings(item, sensitive_paths)
        return value
    if isinstance(value, list):
        for index, item in enumerate(value):
            value[index] = _redact_path_strings(item, sensitive_paths)
        return value
    if isinstance(value, str):
        for path in sensitive_paths:
            value = value.replace(path, "<redacted:path>")
    return value


def _export_preview_execute_command(request: ExportTargetRequest) -> str:
    parts = ["threadvault", "export-target", request.profile]
    for session_id in request.session_ids:
        parts.extend(["--session", session_id])
    if request.project:
        parts.extend(["--project", request.project])
    parts.extend(["--out", str(request.out_dir), "--privacy-mode", request.privacy_mode, "--json"])
    if request.skill_name:
        parts.extend(["--skill-name", request.skill_name])
    if request.skill_description:
        parts.extend(["--skill-description", request.skill_description])
    return " ".join(parts)

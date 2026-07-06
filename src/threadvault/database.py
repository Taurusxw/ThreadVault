from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import ParsedSession, SearchResult, SessionRow

SCHEMA_VERSION = 5
REQUIRED_TABLES = {
    "meta",
    "sessions",
    "turns",
    "events",
    "import_logs",
    "parse_warnings",
    "events_fts",
    "ingestion_queue",
    "vector_index_meta",
    "vector_chunks",
}
REQUIRED_INDEXES = {
    "idx_events_session",
    "idx_events_turn",
    "idx_events_timestamp",
    "idx_events_tool",
    "idx_events_type",
    "idx_events_index_policy",
    "idx_events_value_level",
    "idx_sessions_cwd",
    "idx_vector_chunks_session",
    "idx_vector_chunks_adapter",
}
REQUIRED_TRIGGERS = {"events_ai", "events_ad", "events_au"}
LOW_VALUE_EVENT_TYPES = {
    ("event_msg", "token_count"),
    ("event_msg", "patch_apply_end"),
    ("event_msg", "task_started"),
    ("event_msg", "task_complete"),
    ("event_msg", "web_search_end"),
    ("event_msg", "thread_goal_updated"),
    ("event_msg", "item_completed"),
    ("event_msg", "turn_aborted"),
    ("response_item", "reasoning"),
    ("response_item", "web_search_call"),
    ("response_item", "tool_search_output"),
    ("session_meta", None),
}
MAX_FULL_INDEX_CHARS = 5000
TOOL_HEAD_CHARS = 1200
TOOL_TAIL_CHARS = 800


def connect(db_path: Path) -> sqlite3.Connection:
    db_path = db_path.expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    db_path = db_path.expanduser().resolve()
    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def classify_index_text(event_or_row: Any) -> dict[str, str | None]:
    top_type = _event_value(event_or_row, "top_type")
    sub_type = _event_value(event_or_row, "sub_type")
    tool_name = _event_value(event_or_row, "tool_name")
    file_path = _event_value(event_or_row, "file_path")
    text = _event_value(event_or_row, "text_content") or ""

    if not text.strip():
        return {"indexed_text": None, "index_policy": "skip_empty", "value_level": "noise"}
    if (top_type, sub_type) in LOW_VALUE_EVENT_TYPES:
        return {"indexed_text": None, "index_policy": "skip_low_value", "value_level": "noise"}
    if _contains_inline_binary(text):
        return {
            "indexed_text": _binary_placeholder(top_type, sub_type, tool_name, file_path),
            "index_policy": "metadata_only",
            "value_level": "evidence",
        }
    if sub_type in {"function_call_output", "custom_tool_call_output"}:
        if len(text) > TOOL_HEAD_CHARS + TOOL_TAIL_CHARS:
            return {
                "indexed_text": _head_tail_text(text, TOOL_HEAD_CHARS, TOOL_TAIL_CHARS),
                "index_policy": "truncated",
                "value_level": "evidence",
            }
        return {"indexed_text": text, "index_policy": "full", "value_level": "evidence"}
    if len(text) > MAX_FULL_INDEX_CHARS:
        return {
            "indexed_text": _head_tail_text(text, 2500, 1500),
            "index_policy": "truncated",
            "value_level": "core",
        }
    return {"indexed_text": text, "index_policy": "full", "value_level": "core"}


def _event_value(event_or_row: Any, name: str) -> Any:
    if isinstance(event_or_row, sqlite3.Row):
        return event_or_row[name]
    if isinstance(event_or_row, dict):
        return event_or_row.get(name)
    return getattr(event_or_row, name, None)


def _contains_inline_binary(text: str) -> bool:
    return "data:image/" in text or ";base64," in text


def _binary_placeholder(top_type: str | None, sub_type: str | None, tool_name: str | None, file_path: str | None) -> str:
    parts = ["[binary or image evidence omitted from search index]"]
    if top_type or sub_type:
        parts.append(f"type={top_type or ''}/{sub_type or ''}")
    if tool_name:
        parts.append(f"tool={tool_name}")
    if file_path:
        parts.append(f"file={file_path}")
    return " ".join(parts)


def _head_tail_text(text: str, head_chars: int, tail_chars: int) -> str:
    omitted = max(0, len(text) - head_chars - tail_chars)
    return f"{text[:head_chars]}\n[... {omitted} chars omitted from search index ...]\n{text[-tail_chars:]}"


def backup_database(db_path: Path, out: Path, force: bool = False) -> dict[str, Any]:
    db_path = db_path.expanduser()
    out = out.expanduser()
    if out.suffix.lower() == ".db":
        destination = out
    else:
        timestamp = datetime.now(UTC).replace(microsecond=0).strftime("%Y%m%dT%H%M%SZ")
        destination = out / f"threadvault-backup-{timestamp}.db"
    existed = destination.exists()
    if existed and not force:
        return {
            "ok": False,
            "error": "backup_exists",
            "source_db": str(db_path),
            "destination": str(destination),
            "existed": True,
            "overwritten": False,
            "force": force,
            "bytes": destination.stat().st_size if destination.exists() else 0,
            "schema_version": None,
            "stats": None,
        }
    if existed:
        destination.unlink()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as source, sqlite3.connect(destination) as target:
        init_db(source)
        source.backup(target)
    with connect(destination) as backup_conn:
        schema_row = backup_conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
        backup_stats = stats(backup_conn)
    return {
        "ok": True,
        "error": None,
        "source_db": str(db_path),
        "destination": str(destination),
        "existed": existed,
        "overwritten": existed,
        "force": force,
        "bytes": destination.stat().st_size,
        "schema_version": int(schema_row["value"]) if schema_row else None,
        "stats": backup_stats,
    }


def verify_database_backup(path: Path) -> dict[str, Any]:
    backup_path = path.expanduser()
    base: dict[str, Any] = {
        "backup": str(backup_path),
        "exists": backup_path.exists(),
        "ok": False,
        "errors": [],
        "integrity_check": None,
        "schema_version": None,
        "doctor": None,
        "stats": None,
        "bytes": backup_path.stat().st_size if backup_path.exists() else 0,
    }
    if not backup_path.exists():
        base["errors"].append({"code": "backup_missing", "message": "Backup file does not exist."})
        return base
    try:
        with connect_readonly(backup_path) as conn:
            integrity = [row[0] for row in conn.execute("PRAGMA integrity_check").fetchall()]
            schema_row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
            doctor_result = doctor(conn)
            backup_stats = stats(conn)
    except sqlite3.DatabaseError as exc:
        base["errors"].append({"code": "invalid_sqlite_database", "message": str(exc)})
        return base
    except sqlite3.Error as exc:
        base["errors"].append({"code": "sqlite_error", "message": str(exc)})
        return base
    base["integrity_check"] = integrity
    base["schema_version"] = int(schema_row["value"]) if schema_row else None
    base["doctor"] = doctor_result
    base["stats"] = backup_stats
    if integrity != ["ok"]:
        base["errors"].append({"code": "integrity_check_failed", "message": "; ".join(integrity)})
    if not doctor_result["ok"]:
        base["errors"].append({"code": "schema_doctor_failed", "message": "ThreadVault schema checks failed."})
    base["ok"] = not base["errors"]
    return base


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
          session_id TEXT PRIMARY KEY,
          parent_session_id TEXT NULL,
          source_kind TEXT NOT NULL,
          cwd TEXT NULL,
          model_provider TEXT NULL,
          first_seen_at TEXT NULL,
          updated_at TEXT NULL,
          archived INTEGER NOT NULL DEFAULT 0,
          raw_path TEXT NOT NULL,
          raw_sha256 TEXT NOT NULL,
          parse_version INTEGER NOT NULL,
          flags_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS turns (
          turn_id TEXT PRIMARY KEY,
          session_id TEXT NOT NULL,
          turn_index INTEGER NOT NULL,
          timestamp TEXT NULL,
          model TEXT NULL,
          effort TEXT NULL,
          approval_policy TEXT NULL,
          collaboration_mode_json TEXT NULL,
          user_message_text TEXT NULL,
          assistant_message_text TEXT NULL,
          summary_text TEXT NULL,
          token_usage_json TEXT NULL,
          FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS events (
          event_id INTEGER PRIMARY KEY AUTOINCREMENT,
          session_id TEXT NOT NULL,
          turn_id TEXT NULL,
          timestamp TEXT NULL,
          top_type TEXT NOT NULL,
          sub_type TEXT NULL,
          role TEXT NULL,
          call_id TEXT NULL,
          tool_name TEXT NULL,
          file_path TEXT NULL,
          text_content TEXT NULL,
          indexed_text TEXT NULL,
          index_policy TEXT NOT NULL DEFAULT 'full',
          value_level TEXT NOT NULL DEFAULT 'core',
          payload_json TEXT NOT NULL,
          line_no INTEGER NULL,
          FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS import_logs (
          import_id INTEGER PRIMARY KEY AUTOINCREMENT,
          raw_path TEXT NOT NULL,
          raw_sha256 TEXT NOT NULL,
          session_id TEXT NULL,
          status TEXT NOT NULL,
          imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          message TEXT NULL,
          UNIQUE(raw_path, raw_sha256)
        );

        CREATE TABLE IF NOT EXISTS parse_warnings (
          warning_id INTEGER PRIMARY KEY AUTOINCREMENT,
          session_id TEXT NULL,
          raw_path TEXT NOT NULL,
          line_no INTEGER NULL,
          code TEXT NOT NULL,
          message TEXT NOT NULL,
          raw_excerpt TEXT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(
          session_id UNINDEXED,
          tool_name,
          file_path,
          indexed_text,
          content='events',
          content_rowid='event_id',
          tokenize='unicode61'
        );

        CREATE TRIGGER IF NOT EXISTS events_ai AFTER INSERT ON events BEGIN
          INSERT INTO events_fts(rowid, session_id, tool_name, file_path, indexed_text)
          VALUES (new.event_id, new.session_id, new.tool_name, new.file_path, new.indexed_text);
        END;

        CREATE TRIGGER IF NOT EXISTS events_ad AFTER DELETE ON events BEGIN
          INSERT INTO events_fts(events_fts, rowid, session_id, tool_name, file_path, indexed_text)
          VALUES ('delete', old.event_id, old.session_id, old.tool_name, old.file_path, old.indexed_text);
        END;

        CREATE TRIGGER IF NOT EXISTS events_au AFTER UPDATE ON events BEGIN
          INSERT INTO events_fts(events_fts, rowid, session_id, tool_name, file_path, indexed_text)
          VALUES ('delete', old.event_id, old.session_id, old.tool_name, old.file_path, old.indexed_text);
          INSERT INTO events_fts(rowid, session_id, tool_name, file_path, indexed_text)
          VALUES (new.event_id, new.session_id, new.tool_name, new.file_path, new.indexed_text);
        END;

        CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
        CREATE INDEX IF NOT EXISTS idx_events_turn ON events(turn_id);
        CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_events_tool ON events(tool_name);
        CREATE INDEX IF NOT EXISTS idx_events_type ON events(top_type, sub_type);
        CREATE INDEX IF NOT EXISTS idx_sessions_cwd ON sessions(cwd);
        """
    )
    _migrate_v2(conn)
    _migrate_v3(conn)
    _migrate_v4(conn)
    _migrate_v5(conn)
    conn.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()


def _migrate_v2(conn: sqlite3.Connection) -> None:
    event_cols = {row["name"] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
    if "turn_index" not in event_cols:
        conn.execute("ALTER TABLE events ADD COLUMN turn_index INTEGER NULL")

    turn_cols = {row["name"] for row in conn.execute("PRAGMA table_info(turns)").fetchall()}
    if "event_count" not in turn_cols:
        conn.execute("ALTER TABLE turns ADD COLUMN event_count INTEGER NOT NULL DEFAULT 0")


def _migrate_v3(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ingestion_queue (
          request_id INTEGER PRIMARY KEY AUTOINCREMENT,
          source TEXT NOT NULL,
          codex_home TEXT NULL,
          reason TEXT NOT NULL,
          status TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          processed_at TEXT NULL,
          attempts INTEGER NOT NULL DEFAULT 0,
          message TEXT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_ingestion_queue_status ON ingestion_queue(status, created_at);
        CREATE INDEX IF NOT EXISTS idx_ingestion_queue_active
          ON ingestion_queue(source, codex_home, reason, status);
        """
    )


def _migrate_v4(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS vector_index_meta (
          key TEXT PRIMARY KEY,
          adapter TEXT NOT NULL,
          dimensions INTEGER NOT NULL,
          chunk_count INTEGER NOT NULL,
          built_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS vector_chunks (
          chunk_id TEXT PRIMARY KEY,
          adapter TEXT NOT NULL,
          dimensions INTEGER NOT NULL,
          chunk_type TEXT NOT NULL,
          session_id TEXT NOT NULL,
          turn_index INTEGER NULL,
          text TEXT NOT NULL,
          text_hash TEXT NOT NULL,
          vector_json TEXT NOT NULL,
          evidence_event_ids_json TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          indexed_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_vector_chunks_session ON vector_chunks(session_id);
        CREATE INDEX IF NOT EXISTS idx_vector_chunks_adapter ON vector_chunks(adapter, dimensions);
        """
    )


def _migrate_v5(conn: sqlite3.Connection) -> None:
    event_cols = {row["name"] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
    added_columns = False
    if "indexed_text" not in event_cols:
        conn.execute("ALTER TABLE events ADD COLUMN indexed_text TEXT NULL")
        added_columns = True
    if "index_policy" not in event_cols:
        conn.execute("ALTER TABLE events ADD COLUMN index_policy TEXT NOT NULL DEFAULT 'full'")
        added_columns = True
    if "value_level" not in event_cols:
        conn.execute("ALTER TABLE events ADD COLUMN value_level TEXT NOT NULL DEFAULT 'core'")
        added_columns = True

    rows = conn.execute(
        """
        SELECT event_id, top_type, sub_type, tool_name, file_path, text_content
        FROM events
        WHERE
          index_policy IS NULL
          OR value_level IS NULL
          OR (indexed_text IS NULL AND index_policy = 'full' AND value_level = 'core')
        """
    ).fetchall()
    if rows:
        conn.executemany(
            "UPDATE events SET indexed_text = ?, index_policy = ?, value_level = ? WHERE event_id = ?",
            [
                (
                    classification["indexed_text"],
                    classification["index_policy"],
                    classification["value_level"],
                    row["event_id"],
                )
                for row in rows
                for classification in [classify_index_text(row)]
            ],
        )

    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_events_index_policy ON events(index_policy);
        CREATE INDEX IF NOT EXISTS idx_events_value_level ON events(value_level);
        """
    )
    if added_columns or _fts_uses_legacy_text_content(conn):
        recreate_clean_fts(conn)


def _fts_uses_legacy_text_content(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'events_fts'").fetchone()
    return bool(row and "text_content" in (row["sql"] or ""))


def recreate_clean_fts(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TRIGGER IF EXISTS events_ai;
        DROP TRIGGER IF EXISTS events_ad;
        DROP TRIGGER IF EXISTS events_au;
        DROP TABLE IF EXISTS events_fts;

        CREATE VIRTUAL TABLE events_fts USING fts5(
          session_id UNINDEXED,
          tool_name,
          file_path,
          indexed_text,
          content='events',
          content_rowid='event_id',
          tokenize='unicode61'
        );

        CREATE TRIGGER events_ai AFTER INSERT ON events BEGIN
          INSERT INTO events_fts(rowid, session_id, tool_name, file_path, indexed_text)
          VALUES (new.event_id, new.session_id, new.tool_name, new.file_path, new.indexed_text);
        END;

        CREATE TRIGGER events_ad AFTER DELETE ON events BEGIN
          INSERT INTO events_fts(events_fts, rowid, session_id, tool_name, file_path, indexed_text)
          VALUES ('delete', old.event_id, old.session_id, old.tool_name, old.file_path, old.indexed_text);
        END;

        CREATE TRIGGER events_au AFTER UPDATE ON events BEGIN
          INSERT INTO events_fts(events_fts, rowid, session_id, tool_name, file_path, indexed_text)
          VALUES ('delete', old.event_id, old.session_id, old.tool_name, old.file_path, old.indexed_text);
          INSERT INTO events_fts(rowid, session_id, tool_name, file_path, indexed_text)
          VALUES (new.event_id, new.session_id, new.tool_name, new.file_path, new.indexed_text);
        END;

        INSERT INTO events_fts(rowid, session_id, tool_name, file_path, indexed_text)
        SELECT event_id, session_id, tool_name, file_path, indexed_text
        FROM events;
        """
    )


def has_imported(conn: sqlite3.Connection, raw_path: Path, raw_sha256: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM import_logs WHERE raw_path = ? AND raw_sha256 = ? AND status = 'imported'",
        (str(raw_path), raw_sha256),
    ).fetchone()
    return row is not None


def insert_session(conn: sqlite3.Connection, parsed: ParsedSession) -> int:
    with conn:
        writer = SessionWriter(conn, parsed)
        for event in parsed.events:
            writer.add_event(event)
        return writer.finish()


def delete_session_data(conn: sqlite3.Connection, session_id: str) -> None:
    row = conn.execute("SELECT raw_path FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
    raw_path = row["raw_path"] if row else None
    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM parse_warnings WHERE session_id = ?", (session_id,))
    if raw_path:
        conn.execute("DELETE FROM import_logs WHERE raw_path = ?", (raw_path,))


def insert_session_streaming(conn: sqlite3.Connection, parsed: ParsedSession, batch_size: int = 500) -> int:
    return insert_session(conn, parsed)


class SessionWriter:
    def __init__(self, conn: sqlite3.Connection, parsed: ParsedSession, batch_size: int = 500):
        self.conn = conn
        self.parsed = parsed
        self.batch_size = batch_size
        self.event_batch = []
        self.event_count = 0
        self.warning_count = 0
        self.current_turn: dict[str, Any] | None = None
        self.turn_count = 0
        delete_session_data(conn, parsed.session_id)
        self._insert_session_row()
        for warning in parsed.warnings:
            self.add_warning(warning)

    def add_event(self, event) -> None:
        self._assign_turn(event)
        self.event_batch.append(event)
        self.event_count += 1
        if len(self.event_batch) >= self.batch_size:
            self._flush_events()

    def add_warning(self, warning) -> None:
        self.warning_count += 1
        self.conn.execute(
            """
            INSERT INTO parse_warnings (
              session_id, raw_path, line_no, code, message, raw_excerpt
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self.parsed.session_id,
                str(warning.path),
                warning.line_no,
                warning.code,
                warning.message,
                warning.raw_excerpt,
            ),
        )

    def finish(self) -> int:
        self._flush_events()
        self._flush_turn()
        self.conn.execute(
            """
            INSERT OR REPLACE INTO import_logs(raw_path, raw_sha256, session_id, status, message)
            VALUES (?, ?, ?, 'imported', ?)
            """,
            (
                str(self.parsed.source_path),
                self.parsed.raw_sha256,
                self.parsed.session_id,
                f"{self.event_count} events, {self.warning_count} warnings",
            ),
        )
        return self.event_count

    def _insert_session_row(self) -> None:
        self.conn.execute(
            """
            INSERT INTO sessions (
              session_id, parent_session_id, source_kind, cwd, model_provider,
              first_seen_at, updated_at, archived, raw_path, raw_sha256,
              parse_version, flags_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.parsed.session_id,
                self.parsed.parent_session_id,
                self.parsed.source_kind,
                self.parsed.cwd,
                self.parsed.model_provider,
                self.parsed.first_seen_at,
                self.parsed.updated_at,
                1 if self.parsed.archived else 0,
                str(self.parsed.source_path),
                self.parsed.raw_sha256,
                SCHEMA_VERSION,
                json.dumps(self.parsed.flags, ensure_ascii=False, sort_keys=True),
            ),
        )

    def _assign_turn(self, event) -> None:
        is_user_message = event.top_type == "event_msg" and event.sub_type == "user_message"
        if self.current_turn is None:
            self.current_turn = self._new_turn(event)
        elif is_user_message and self.current_turn.get("user_message_text"):
            self._flush_turn()
            self.current_turn = self._new_turn(event)
        assert self.current_turn is not None
        event.turn_id = self.current_turn["turn_id"]
        event.turn_index = self.current_turn["turn_index"]
        self.current_turn["event_count"] += 1

        if event.top_type == "turn_context":
            self.current_turn["model"] = event.payload.get("model") or self.current_turn["model"]
            self.current_turn["effort"] = event.payload.get("effort") or self.current_turn["effort"]
            self.current_turn["approval_policy"] = event.payload.get("approval_policy") or self.current_turn["approval_policy"]
            if event.payload.get("collaboration_mode") is not None:
                self.current_turn["collaboration_mode_json"] = json.dumps(event.payload["collaboration_mode"], ensure_ascii=False)
        elif is_user_message:
            self.current_turn["user_message_text"] = _append_text(self.current_turn["user_message_text"], event.text_content)
        elif event.top_type == "response_item":
            if event.sub_type == "message":
                self.current_turn["assistant_message_text"] = _append_text(self.current_turn["assistant_message_text"], event.text_content)
            elif event.sub_type == "reasoning":
                self.current_turn["summary_text"] = _append_text(self.current_turn["summary_text"], event.text_content)
        elif event.top_type == "event_msg" and event.sub_type == "token_count":
            self.current_turn["token_usage_json"] = json.dumps(event.payload, ensure_ascii=False, sort_keys=True)

    def _new_turn(self, event) -> dict[str, Any]:
        turn = {
            "turn_id": f"{self.parsed.session_id}:{self.turn_count}",
            "turn_index": self.turn_count,
            "timestamp": event.timestamp,
            "model": None,
            "effort": None,
            "approval_policy": None,
            "collaboration_mode_json": None,
            "user_message_text": None,
            "assistant_message_text": None,
            "summary_text": None,
            "token_usage_json": None,
            "event_count": 0,
        }
        self.turn_count += 1
        return turn

    def _flush_turn(self) -> None:
        if not self.current_turn:
            return
        turn = self.current_turn
        self.conn.execute(
            """
            INSERT INTO turns (
              turn_id, session_id, turn_index, timestamp, model, effort,
              approval_policy, collaboration_mode_json, user_message_text,
              assistant_message_text, summary_text, token_usage_json, event_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                turn["turn_id"],
                self.parsed.session_id,
                turn["turn_index"],
                turn["timestamp"],
                turn["model"],
                turn["effort"],
                turn["approval_policy"],
                turn["collaboration_mode_json"],
                turn["user_message_text"],
                turn["assistant_message_text"],
                turn["summary_text"],
                turn["token_usage_json"],
                turn["event_count"],
            ),
        )
        self.current_turn = None

    def _flush_events(self) -> None:
        if not self.event_batch:
            return
        self.conn.executemany(
            """
            INSERT INTO events (
              session_id, timestamp, top_type, sub_type, role, call_id,
              tool_name, file_path, text_content, indexed_text, index_policy,
              value_level, payload_json, line_no,
              turn_id, turn_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    self.parsed.session_id,
                    event.timestamp,
                    event.top_type,
                    event.sub_type,
                    event.role,
                    event.call_id,
                    event.tool_name,
                    event.file_path,
                    event.text_content,
                    classification["indexed_text"],
                    classification["index_policy"],
                    classification["value_level"],
                    json.dumps(event.payload, ensure_ascii=False, sort_keys=True),
                    event.line_no,
                    event.turn_id,
                    event.turn_index,
                )
                for event in self.event_batch
                for classification in [classify_index_text(event)]
            ],
        )
        self.event_batch = []


def _append_text(existing: str | None, text: str | None) -> str | None:
    if not text:
        return existing
    if not existing:
        return text
    return f"{existing}\n{text}"


def log_skipped(conn: sqlite3.Connection, raw_path: Path, raw_sha256: str, message: str) -> None:
    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO import_logs(raw_path, raw_sha256, status, message)
            VALUES (?, ?, 'skipped', ?)
            """,
            (str(raw_path), raw_sha256, message),
        )


def log_failed(conn: sqlite3.Connection, raw_path: Path, raw_sha256: str | None, message: str) -> None:
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO import_logs(raw_path, raw_sha256, status, message)
            VALUES (?, ?, 'failed', ?)
            """,
            (str(raw_path), raw_sha256 or "", message),
        )


def list_sessions(conn: sqlite3.Connection, limit: int = 50, cwd: str | None = None) -> list[SessionRow]:
    params: list[Any] = []
    where = ""
    if cwd:
        where = "WHERE s.cwd = ?"
        params.append(cwd)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT
          s.session_id, s.cwd, s.source_kind, s.first_seen_at, s.updated_at,
          s.raw_path,
          COUNT(DISTINCT e.event_id) AS event_count,
          COUNT(DISTINCT w.warning_id) AS warning_count
        FROM sessions s
        LEFT JOIN events e ON e.session_id = s.session_id
        LEFT JOIN parse_warnings w ON w.session_id = s.session_id
        {where}
        GROUP BY s.session_id
        ORDER BY COALESCE(s.updated_at, s.first_seen_at, '') DESC, s.session_id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [SessionRow(**dict(row)) for row in rows]


def list_warnings(
    conn: sqlite3.Connection,
    limit: int = 50,
    session_id: str | None = None,
    code: str | None = None,
    raw_path: str | None = None,
) -> list[sqlite3.Row]:
    params: list[Any] = []
    filters: list[str] = []
    if session_id:
        filters.append("session_id = ?")
        params.append(session_id)
    if code:
        filters.append("code = ?")
        params.append(code)
    if raw_path:
        filters.append("raw_path = ?")
        params.append(raw_path)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.append(limit)
    return conn.execute(
        f"""
        SELECT warning_id, session_id, raw_path, line_no, code, message, raw_excerpt, created_at
        FROM parse_warnings
        {where}
        ORDER BY warning_id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()


def warning_summary(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT code, COUNT(*) AS count
        FROM parse_warnings
        GROUP BY code
        ORDER BY count DESC, code
        """
    ).fetchall()
    return [dict(row) for row in rows]


def search_events(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 20,
    session_id: str | None = None,
    cwd: str | None = None,
    since: str | None = None,
    until: str | None = None,
    top_type: str | None = None,
    tool: str | None = None,
    fields: str = "standard",
) -> list[SearchResult]:
    params: list[Any] = []
    filters: list[str] = []
    fts_query = build_fts_query(query)
    use_like = False
    if fts_query:
        filters.append("events_fts MATCH ?")
        params.append(fts_query)
    else:
        use_like = True
        filters.append("COALESCE(e.indexed_text, '') LIKE ?")
        params.append(f"%{query}%")
    if session_id:
        filters.append("e.session_id = ?")
        params.append(session_id)
    if cwd:
        filters.append("s.cwd = ?")
        params.append(cwd)
    if since:
        filters.append("e.timestamp >= ?")
        params.append(since)
    if until:
        filters.append("e.timestamp <= ?")
        params.append(until)
    if top_type:
        filters.append("(e.top_type = ? OR e.sub_type = ?)")
        params.extend([top_type, top_type])
    if tool:
        filters.append("e.tool_name = ?")
        params.append(tool)
    params.append(limit)
    snippet_expr = "e.indexed_text AS snippet" if use_like else "snippet(events_fts, 3, '[', ']', '...', 12) AS snippet"
    rank_expr = "0.0 AS rank" if use_like else "bm25(events_fts) AS rank"
    if fields == "minimal":
        snippet_expr = "NULL AS snippet"
    rows = conn.execute(
        f"""
        SELECT
          e.event_id, e.session_id, e.timestamp, e.top_type, e.sub_type, e.role,
          e.tool_name, e.file_path,
          {snippet_expr},
          {rank_expr}
        FROM events_fts
        JOIN events e ON e.event_id = events_fts.rowid
        JOIN sessions s ON s.session_id = e.session_id
        WHERE {" AND ".join(filters)}
        ORDER BY rank
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [SearchResult(**dict(row)) for row in rows]


def build_fts_query(query: str) -> str | None:
    query = query.strip()
    if not query:
        return None
    if any(char in query for char in ['"', "'", ":", "(", ")", "*", "^", "{", "}", "[", "]"]):
        escaped = query.replace('"', '""')
        return f'"{escaped}"'
    return query


def get_session(conn: sqlite3.Connection, session_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()


def get_sessions_by_ids(conn: sqlite3.Connection, session_ids: list[str]) -> list[sqlite3.Row]:
    if not session_ids:
        return []
    placeholders = ", ".join("?" for _ in session_ids)
    rows = conn.execute(
        f"SELECT * FROM sessions WHERE session_id IN ({placeholders})",
        session_ids,
    ).fetchall()
    by_id = {row["session_id"]: row for row in rows}
    return [by_id[session_id] for session_id in session_ids if session_id in by_id]


def get_events(conn: sqlite3.Connection, session_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM events WHERE session_id = ? ORDER BY event_id",
        (session_id,),
    ).fetchall()


def get_events_filtered(
    conn: sqlite3.Connection,
    session_id: str,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    last_turns: int | None = None,
    no_tool_output: bool = False,
    no_reasoning: bool = False,
) -> list[sqlite3.Row]:
    params: list[Any] = [session_id]
    filters = ["session_id = ?"]
    if include:
        placeholders = ",".join("?" for _ in include)
        filters.append(f"(top_type IN ({placeholders}) OR sub_type IN ({placeholders}))")
        params.extend(include)
        params.extend(include)
    if exclude:
        placeholders = ",".join("?" for _ in exclude)
        filters.append(f"COALESCE(sub_type, top_type) NOT IN ({placeholders}) AND top_type NOT IN ({placeholders})")
        params.extend(exclude)
        params.extend(exclude)
    if no_tool_output:
        filters.append("COALESCE(sub_type, '') != 'function_call_output'")
    if no_reasoning:
        filters.append("COALESCE(sub_type, '') != 'reasoning'")
    if last_turns:
        max_turn = conn.execute(
            "SELECT MAX(turn_index) AS max_turn FROM events WHERE session_id = ?",
            (session_id,),
        ).fetchone()["max_turn"]
        if max_turn is not None:
            min_turn = max(0, int(max_turn) - last_turns + 1)
            filters.append("turn_index >= ?")
            params.append(min_turn)
    return conn.execute(
        f"SELECT * FROM events WHERE {' AND '.join(filters)} ORDER BY event_id",
        params,
    ).fetchall()


def get_project_sessions(conn: sqlite3.Connection, cwd: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM sessions WHERE cwd = ? ORDER BY COALESCE(updated_at, first_seen_at, '') DESC",
        (cwd,),
    ).fetchall()


def get_events_for_sessions(conn: sqlite3.Connection, session_ids: Iterable[str]) -> list[sqlite3.Row]:
    ids = list(session_ids)
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    return conn.execute(
        f"SELECT * FROM events WHERE session_id IN ({placeholders}) ORDER BY session_id, event_id",
        ids,
    ).fetchall()


def stats(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT
          (SELECT COUNT(*) FROM sessions) AS sessions,
          (SELECT COUNT(*) FROM events) AS events,
          (SELECT COUNT(*) FROM turns) AS turns,
          (SELECT COUNT(*) FROM parse_warnings) AS warnings,
          (SELECT COUNT(DISTINCT cwd) FROM sessions WHERE cwd IS NOT NULL) AS projects,
          (SELECT COUNT(*) FROM events WHERE sub_type = 'function_call') AS tool_calls,
          (SELECT COUNT(DISTINCT file_path) FROM events WHERE file_path IS NOT NULL) AS files,
          (SELECT MIN(first_seen_at) FROM sessions) AS first_seen_at,
          (SELECT MAX(updated_at) FROM sessions) AS updated_at
        """
    ).fetchone()
    payload = dict(row)
    payload["search_index"] = search_index_stats(conn)
    return payload


def search_index_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT
          COUNT(*) AS total_events,
          SUM(CASE WHEN COALESCE(indexed_text, '') != '' THEN 1 ELSE 0 END) AS searchable_events,
          SUM(CASE WHEN index_policy LIKE 'skip_%' THEN 1 ELSE 0 END) AS skipped_events,
          SUM(CASE WHEN index_policy = 'truncated' THEN 1 ELSE 0 END) AS truncated_events,
          SUM(CASE WHEN index_policy = 'metadata_only' THEN 1 ELSE 0 END) AS metadata_only_events,
          SUM(LENGTH(COALESCE(text_content, ''))) AS raw_chars,
          SUM(LENGTH(COALESCE(indexed_text, ''))) AS indexed_chars
        FROM events
        """
    ).fetchone()
    by_policy = conn.execute(
        """
        SELECT index_policy, COUNT(*) AS count
        FROM events
        GROUP BY index_policy
        ORDER BY count DESC, index_policy
        """
    ).fetchall()
    by_value = conn.execute(
        """
        SELECT value_level, COUNT(*) AS count
        FROM events
        GROUP BY value_level
        ORDER BY count DESC, value_level
        """
    ).fetchall()
    raw_chars = row["raw_chars"] or 0
    indexed_chars = row["indexed_chars"] or 0
    return {
        "total_events": row["total_events"] or 0,
        "searchable_events": row["searchable_events"] or 0,
        "skipped_events": row["skipped_events"] or 0,
        "truncated_events": row["truncated_events"] or 0,
        "metadata_only_events": row["metadata_only_events"] or 0,
        "raw_chars": raw_chars,
        "indexed_chars": indexed_chars,
        "indexed_char_ratio": (indexed_chars / raw_chars) if raw_chars else 0,
        "by_policy": [dict(item) for item in by_policy],
        "by_value_level": [dict(item) for item in by_value],
    }


def doctor(conn: sqlite3.Connection) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    maintenance_suggestions: list[dict[str, str]] = []
    ok = True
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS temp.tv_fts_check USING fts5(x)")
        checks.append({"name": "sqlite_fts5", "ok": True, "message": "FTS5 is available."})
    except sqlite3.DatabaseError as exc:
        ok = False
        checks.append({"name": "sqlite_fts5", "ok": False, "message": str(exc)})

    schema_row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    schema_version = schema_row["value"] if schema_row else None
    schema_ok = schema_version == str(SCHEMA_VERSION)
    ok = ok and schema_ok
    checks.append({
        "name": "schema_version",
        "ok": schema_ok,
        "message": f"expected {SCHEMA_VERSION}, found {schema_version}",
    })
    if not schema_ok:
        maintenance_suggestions.append({
            "code": "schema_version_mismatch",
            "message": "Back up the database, then run threadvault init with the current version.",
        })

    objects = _sqlite_objects(conn)
    for kind, required in [
        ("table", REQUIRED_TABLES),
        ("index", REQUIRED_INDEXES),
        ("trigger", REQUIRED_TRIGGERS),
    ]:
        missing = sorted(required - objects[kind])
        present_ok = not missing
        ok = ok and present_ok
        checks.append({
            "name": f"{kind}s_present",
            "ok": present_ok,
            "message": "all required objects present" if present_ok else f"missing: {', '.join(missing)}",
        })
        if missing:
            maintenance_suggestions.append({
                "code": f"missing_{kind}s",
                "message": "Back up the database before reinitializing schema objects.",
            })

    event_count = conn.execute("SELECT COUNT(*) AS count FROM events").fetchone()["count"]
    fts_count = conn.execute("SELECT COUNT(*) AS count FROM events_fts").fetchone()["count"]
    fts_ok = event_count == fts_count
    ok = ok and fts_ok
    checks.append({
        "name": "fts_index_count",
        "ok": fts_ok,
        "message": f"events={event_count}, events_fts={fts_count}",
    })
    if not fts_ok:
        maintenance_suggestions.append({
            "code": "fts_count_mismatch",
            "message": "Run threadvault reindex --fts-only after backing up the database.",
        })
    top_warnings = warning_summary(conn)[:10]
    event_count = conn.execute("SELECT COUNT(*) AS count FROM events").fetchone()["count"]
    warning_count = conn.execute("SELECT COUNT(*) AS count FROM parse_warnings").fetchone()["count"]
    parse_health = {
        "events": event_count,
        "warnings": warning_count,
        "warning_codes_top": top_warnings,
        "warning_ratio": (warning_count / event_count) if event_count else 0,
    }
    index_health = search_index_stats(conn)
    if warning_count > event_count and event_count:
        maintenance_suggestions.append({
            "code": "high_warning_ratio",
            "message": "Run threadvault warnings --summary --json and inspect parser warning codes.",
        })
    return {
        "ok": ok,
        "checks": checks,
        "stats": stats(conn),
        "parse_health": parse_health,
        "search_index": index_health,
        "schema_version": SCHEMA_VERSION,
        "schema_objects": {key: sorted(value) for key, value in objects.items()},
        "maintenance_suggestions": maintenance_suggestions,
    }


def _sqlite_objects(conn: sqlite3.Connection) -> dict[str, set[str]]:
    rows = conn.execute(
        """
        SELECT type, name
        FROM sqlite_master
        WHERE type IN ('table', 'index', 'trigger')
        """
    ).fetchall()
    objects = {"table": set(), "index": set(), "trigger": set()}
    for row in rows:
        if row["name"].startswith("sqlite_"):
            continue
        objects[row["type"]].add(row["name"])
    return objects


def reindex_fts(conn: sqlite3.Connection) -> dict[str, Any]:
    with conn:
        rows = conn.execute(
            "SELECT event_id, top_type, sub_type, tool_name, file_path, text_content FROM events"
        ).fetchall()
        conn.executemany(
            "UPDATE events SET indexed_text = ?, index_policy = ?, value_level = ? WHERE event_id = ?",
            [
                (
                    classification["indexed_text"],
                    classification["index_policy"],
                    classification["value_level"],
                    row["event_id"],
                )
                for row in rows
                for classification in [classify_index_text(row)]
            ],
        )
        conn.execute("INSERT INTO events_fts(events_fts) VALUES ('rebuild')")
    return {
        "events": conn.execute("SELECT COUNT(*) AS count FROM events").fetchone()["count"],
        "events_fts": conn.execute("SELECT COUNT(*) AS count FROM events_fts").fetchone()["count"],
        "search_index": search_index_stats(conn),
    }


def vacuum(conn: sqlite3.Connection) -> None:
    conn.execute("VACUUM")

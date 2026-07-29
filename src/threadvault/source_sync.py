from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .config import default_codex_home
from .database import SCHEMA_VERSION, connect, connect_readonly, init_db
from .importer import ImportStats, discover_jsonl_files, import_codex_files

SOURCE_SYNC_CONTRACT_VERSION = "source-sync.v1"
SOURCE_MTIME_TOLERANCE = timedelta(seconds=1)


def inspect_source_freshness(
    db_path: Path,
    *,
    codex_home: Path | None = None,
    include_paths: bool = False,
) -> dict[str, Any]:
    """Compare discovered Codex transcripts with successful archive imports without writing."""

    source_home = (codex_home or default_codex_home()).expanduser().resolve()
    files = discover_jsonl_files(source_home)
    db_path = db_path.expanduser().resolve()
    if not db_path.is_file():
        pending = [(path, archived, "archive_missing") for path, archived in files]
        return _freshness_payload(db_path, source_home, files, pending, latest_import=None, include_paths=include_paths)
    with closing(connect_readonly(db_path)) as conn:
        return _inspect_with_connection(
            conn,
            db_path,
            source_home,
            files,
            include_paths=include_paths,
        )


def sync_codex_sources(
    db_path: Path,
    *,
    codex_home: Path | None = None,
    apply: bool = False,
    include_paths: bool = False,
) -> dict[str, Any]:
    """Plan or apply a targeted catch-up of Codex transcripts missing from the archive."""

    source_home = (codex_home or default_codex_home()).expanduser().resolve()
    db_path = db_path.expanduser().resolve()
    files = discover_jsonl_files(source_home)
    if not apply:
        return inspect_source_freshness(db_path, codex_home=source_home, include_paths=include_paths) | {
            "applied": False,
            "import_stats": None,
        }

    with closing(connect(db_path)) as conn:
        init_db(conn)
        before = _inspect_with_connection(
            conn,
            db_path,
            source_home,
            files,
            include_paths=include_paths,
        )
        pending_keys = {_path_key(Path(item["path"])) for item in before.get("pending", [])} if include_paths else set()
        if include_paths:
            pending_files = [(path, archived) for path, archived in files if _path_key(path) in pending_keys]
        else:
            pending_files = _pending_files(conn, files)
        stats = import_codex_files(conn, pending_files, codex_home=source_home) if pending_files else ImportStats()
        after = _inspect_with_connection(
            conn,
            db_path,
            source_home,
            discover_jsonl_files(source_home),
            include_paths=include_paths,
        )
    ok = stats.failed == 0 and after["pending_files"] == 0
    return {
        **after,
        "ok": ok,
        "applied": True,
        "before": {
            "fresh": before["fresh"],
            "pending_files": before["pending_files"],
            "pending_bytes": before["pending_bytes"],
        },
        "import_stats": stats.__dict__,
    }


def _inspect_with_connection(
    conn: sqlite3.Connection,
    db_path: Path,
    codex_home: Path,
    files: list[tuple[Path, bool]],
    *,
    include_paths: bool,
) -> dict[str, Any]:
    pending = _pending_with_reasons(conn, files)
    latest_row = conn.execute("SELECT MAX(imported_at) AS latest FROM import_logs WHERE status = 'imported'").fetchone()
    latest_import = latest_row["latest"] if latest_row is not None else None
    return _freshness_payload(db_path, codex_home, files, pending, latest_import=latest_import, include_paths=include_paths)


def _pending_files(conn: sqlite3.Connection, files: list[tuple[Path, bool]]) -> list[tuple[Path, bool]]:
    pending_keys = {_path_key(path) for path, _archived, _reason in _pending_with_reasons(conn, files)}
    return [(path, archived) for path, archived in files if _path_key(path) in pending_keys]


def _pending_with_reasons(
    conn: sqlite3.Connection,
    files: list[tuple[Path, bool]],
) -> list[tuple[Path, bool, str]]:
    imported: dict[str, tuple[datetime | None, int | None]] = {}
    rows = conn.execute(
        """
        SELECT l.raw_path, MAX(l.imported_at) AS imported_at, MAX(s.parse_version) AS parse_version
        FROM import_logs AS l
        LEFT JOIN sessions AS s ON s.session_id = l.session_id
        WHERE l.status = 'imported'
        GROUP BY l.raw_path
        """
    ).fetchall()
    for row in rows:
        imported[_path_key(Path(row["raw_path"]))] = (_parse_sqlite_timestamp(row["imported_at"]), row["parse_version"])

    pending: list[tuple[Path, bool, str]] = []
    for path, archived in files:
        record = imported.get(_path_key(path))
        if record is None:
            pending.append((path, archived, "not_imported"))
            continue
        imported_at, parse_version = record
        if parse_version != SCHEMA_VERSION:
            pending.append((path, archived, "parser_version_changed"))
            continue
        try:
            modified_at = datetime.fromtimestamp(path.stat().st_mtime, UTC)
        except OSError:
            pending.append((path, archived, "source_unreadable"))
            continue
        if imported_at is None or modified_at > imported_at + SOURCE_MTIME_TOLERANCE:
            pending.append((path, archived, "modified_after_import"))
    return pending


def _freshness_payload(
    db_path: Path,
    codex_home: Path,
    files: list[tuple[Path, bool]],
    pending: list[tuple[Path, bool, str]],
    *,
    latest_import: str | None,
    include_paths: bool,
) -> dict[str, Any]:
    pending_bytes = 0
    newest: datetime | None = None
    reasons: dict[str, int] = {}
    items: list[dict[str, Any]] = []
    pending_map = {_path_key(path): reason for path, _archived, reason in pending}
    for path, archived in files:
        try:
            stat = path.stat()
        except OSError:
            stat = None
        if stat is not None:
            modified = datetime.fromtimestamp(stat.st_mtime, UTC)
            newest = modified if newest is None or modified > newest else newest
        reason = pending_map.get(_path_key(path))
        if reason is None:
            continue
        size = stat.st_size if stat is not None else 0
        pending_bytes += size
        reasons[reason] = reasons.get(reason, 0) + 1
        if include_paths:
            items.append({"path": str(path), "archived": archived, "reason": reason, "bytes": size})
    payload: dict[str, Any] = {
        "contract_version": SOURCE_SYNC_CONTRACT_VERSION,
        "ok": not pending,
        "fresh": not pending,
        "db_path": str(db_path),
        "codex_home": str(codex_home),
        "source_files": len(files),
        "active_files": sum(1 for _path, archived in files if not archived),
        "archived_files": sum(1 for _path, archived in files if archived),
        "pending_files": len(pending),
        "pending_bytes": pending_bytes,
        "pending_reasons": reasons,
        "latest_source_mtime": _iso(newest),
        "latest_import_at": latest_import,
    }
    if include_paths:
        payload["pending"] = items
    return payload


def _path_key(path: Path) -> str:
    return os.path.normcase(str(path.expanduser().resolve()))


def _parse_sqlite_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat().replace("+00:00", "Z")

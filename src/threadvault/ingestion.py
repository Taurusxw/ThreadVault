from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .importer import import_codex_file, import_codex_home

ACTIVE_STATUSES = {"pending", "processing"}
VALID_STATUSES = {"pending", "processing", "completed", "failed", "skipped"}


@dataclass(frozen=True)
class IngestionRequest:
    source: str = "manual"
    codex_home: Path | None = None
    reason: str = "scan"


def enqueue_ingestion(conn: sqlite3.Connection, request: IngestionRequest) -> dict[str, Any]:
    source = _clean_value(request.source, default="manual")
    reason = _clean_value(request.reason, default="scan")
    codex_home = _normalize_codex_home(request.codex_home)
    existing = _active_request(conn, source=source, codex_home=codex_home, reason=reason)
    if existing is not None:
        return {
            "ok": True,
            "enqueued": False,
            "status": "skipped",
            "message": "Matching active ingestion request already exists.",
            "request": _row_to_request(existing),
        }

    with conn:
        cursor = conn.execute(
            """
            INSERT INTO ingestion_queue(source, codex_home, reason, status, message)
            VALUES (?, ?, ?, 'pending', ?)
            """,
            (source, codex_home, reason, "Queued ingestion request."),
        )
        row = conn.execute("SELECT * FROM ingestion_queue WHERE request_id = ?", (cursor.lastrowid,)).fetchone()
    return {
        "ok": True,
        "enqueued": True,
        "status": "pending",
        "message": "Queued ingestion request.",
        "request": _row_to_request(row),
    }


def list_ingestion_queue(conn: sqlite3.Connection, status: str | None = None, limit: int = 50) -> dict[str, Any]:
    if status is not None and status not in VALID_STATUSES:
        raise ValueError(f"Unknown ingestion queue status: {status}")
    limit = max(1, min(limit, 500))
    if status is None:
        rows = conn.execute(
            "SELECT * FROM ingestion_queue ORDER BY request_id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM ingestion_queue WHERE status = ? ORDER BY request_id DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    requests = [_row_to_request(row) for row in rows]
    return {"requests": requests, "count": len(requests)}


def process_ingestion_queue(
    conn: sqlite3.Connection,
    codex_home: Path | None = None,
    limit: int = 10,
    apply: bool = False,
) -> dict[str, Any]:
    limit = max(1, min(limit, 100))
    pending = _pending_requests(conn, limit=limit)
    if not apply:
        requests = [_row_to_request(row) | {"would_process": True} for row in pending]
        return {"ok": True, "apply": False, "processed": 0, "requests": requests}

    processed: list[dict[str, Any]] = []
    ok = True
    for row in pending:
        result = process_ingestion_request(
            conn,
            int(row["request_id"]),
            codex_home=codex_home,
        )
        ok = ok and result["status"] == "completed"
        processed.append(result)
    return {"ok": ok, "apply": True, "processed": len(processed), "requests": processed}


def process_ingestion_request(
    conn: sqlite3.Connection,
    request_id: int,
    *,
    codex_home: Path | None = None,
    transcript_path: Path | None = None,
) -> dict[str, Any]:
    """Process one queue item, optionally importing only the hook transcript."""
    row = _get_request(conn, request_id)
    request_codex_home = codex_home or (Path(row["codex_home"]) if row["codex_home"] else None)
    if row["status"] != "pending":
        return _row_to_request(row) | {"error": f"Request is not pending: {row['status']}"}
    _mark_processing(conn, request_id)
    try:
        if transcript_path is not None:
            stats = import_codex_file(
                conn,
                transcript_path,
                codex_home=request_codex_home,
            )
        else:
            stats = import_codex_home(conn, request_codex_home)
        status = "failed" if stats.failed else "completed"
        message = json.dumps(stats.__dict__, ensure_ascii=False, sort_keys=True)
        _mark_finished(conn, request_id, status=status, message=message)
        finished = _get_request(conn, request_id)
        result = _row_to_request(finished) | {"import_stats": stats.__dict__}
        if status == "failed":
            result["error"] = "One or more transcript imports failed."
        return result
    except Exception as exc:  # noqa: BLE001 - hooks must record failures and let Codex continue.
        _mark_finished(conn, request_id, status="failed", message=str(exc))
        finished = _get_request(conn, request_id)
        return _row_to_request(finished) | {"error": str(exc)}


def _clean_value(value: str | None, default: str) -> str:
    cleaned = (value or "").strip()
    return cleaned or default


def _normalize_codex_home(path: Path | None) -> str | None:
    return str(path.expanduser()) if path is not None else None


def _active_request(conn: sqlite3.Connection, source: str, codex_home: str | None, reason: str) -> sqlite3.Row | None:
    if codex_home is None:
        return conn.execute(
            """
            SELECT * FROM ingestion_queue
            WHERE source = ? AND codex_home IS NULL AND reason = ? AND status IN ('pending', 'processing')
            ORDER BY request_id ASC LIMIT 1
            """,
            (source, reason),
        ).fetchone()
    return conn.execute(
        """
        SELECT * FROM ingestion_queue
        WHERE source = ? AND codex_home = ? AND reason = ? AND status IN ('pending', 'processing')
        ORDER BY request_id ASC LIMIT 1
        """,
        (source, codex_home, reason),
    ).fetchone()


def _pending_requests(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM ingestion_queue WHERE status = 'pending' ORDER BY request_id ASC LIMIT ?",
        (limit,),
    ).fetchall()


def _get_request(conn: sqlite3.Connection, request_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM ingestion_queue WHERE request_id = ?", (request_id,)).fetchone()
    if row is None:
        raise KeyError(request_id)
    return row


def _mark_processing(conn: sqlite3.Connection, request_id: int) -> None:
    with conn:
        conn.execute(
            """
            UPDATE ingestion_queue
            SET status = 'processing',
                attempts = attempts + 1,
                updated_at = CURRENT_TIMESTAMP,
                message = 'Processing ingestion request.'
            WHERE request_id = ? AND status = 'pending'
            """,
            (request_id,),
        )


def _mark_finished(conn: sqlite3.Connection, request_id: int, status: str, message: str) -> None:
    if status not in {"completed", "failed"}:
        raise ValueError(f"Invalid finished ingestion status: {status}")
    with conn:
        conn.execute(
            """
            UPDATE ingestion_queue
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP,
                processed_at = CURRENT_TIMESTAMP,
                message = ?
            WHERE request_id = ?
            """,
            (status, message, request_id),
        )


def _row_to_request(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "request_id": row["request_id"],
        "source": row["source"],
        "codex_home": row["codex_home"],
        "reason": row["reason"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "processed_at": row["processed_at"],
        "attempts": row["attempts"],
        "message": row["message"],
    }

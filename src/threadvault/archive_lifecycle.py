from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import sqlite3
import string
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .backup_manifest import sha256_file, write_backup_manifest
from .codex_adapter import extract_current_text
from .cold_store import ColdBlobRecord, ColdBlobStore, default_cold_root
from .database import (
    SCHEMA_VERSION,
    backup_database,
    classify_index_text,
    connect,
    connect_readonly,
    deduplicate_agent_messages,
    doctor,
    init_db,
    recreate_clean_fts,
    stats,
    verify_database_backup,
)
from .importer import discover_jsonl_files
from .storage_policy import prepare_event_content

STORAGE_BACKUP_VERSION = "storage-backup.v1"
STORAGE_PROFILES = ("core", "evidence", "forensic")
COPY_TABLES = (
    "sessions",
    "turns",
    "import_logs",
    "parse_warnings",
    "ingestion_queue",
    "vector_index_meta",
    "vector_chunks",
)


def hydrate_event_rows(
    conn: sqlite3.Connection,
    db_path: Path,
    events: list[Any],
    *,
    cold_root: Path | None = None,
) -> list[dict[str, Any]]:
    root = (cold_root or default_cold_root(db_path)).expanduser().resolve()
    store = ColdBlobStore(root)
    metadata: dict[str, sqlite3.Row | None] = {}
    hydrated: list[dict[str, Any]] = []
    for source in events:
        event = dict(source)
        ref = event.get("payload_ref")
        if ref:
            if ref not in metadata:
                metadata[ref] = conn.execute(
                    "SELECT relative_path, codec FROM cold_blobs WHERE blob_id = ?",
                    (ref,),
                ).fetchone()
            row = metadata[ref]
            if row is not None:
                payload_json = store.read(row["relative_path"], row["codec"]).decode("utf-8")
                payload = json.loads(payload_json)
                event["payload_json"] = payload_json
                extracted = extract_current_text(event["top_type"], payload if isinstance(payload, dict) else {})
                if extracted:
                    event["text_content"] = extracted
        hydrated.append(event)
    return hydrated


def read_cold_event(db_path: Path, event_id: int, cold_root: Path | None = None) -> dict[str, Any]:
    db_path = db_path.expanduser().resolve()
    with closing(connect_readonly(db_path)) as conn:
        row = conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
        if row is None:
            raise KeyError(event_id)
        event = hydrate_event_rows(conn, db_path, [row], cold_root=cold_root)[0]
    return {
        "event_id": event_id,
        "storage_class": event.get("storage_class"),
        "payload_ref": event.get("payload_ref"),
        "payload": json.loads(event["payload_json"]),
        "text_content": event.get("text_content"),
    }


def storage_audit(db_path: Path, cold_root: Path | None = None) -> dict[str, Any]:
    db_path = db_path.expanduser().resolve()
    root = (cold_root or default_cold_root(db_path)).expanduser().resolve()
    with closing(connect_readonly(db_path)) as conn:
        event_totals = dict(conn.execute(
            """
            SELECT COUNT(*) AS events,
                   SUM(LENGTH(payload_json)) AS payload_chars,
                   SUM(LENGTH(text_content)) AS text_chars,
                   SUM(LENGTH(indexed_text)) AS indexed_chars
            FROM events
            """
        ).fetchone())
        by_type = [dict(row) for row in conn.execute(
            """
            SELECT top_type, COALESCE(sub_type, '<null>') AS sub_type,
                   COUNT(*) AS events,
                   SUM(LENGTH(payload_json)) AS payload_chars,
                   SUM(LENGTH(text_content)) AS text_chars
            FROM events
            GROUP BY top_type, sub_type
            ORDER BY payload_chars DESC
            LIMIT 40
            """
        )]
        by_storage = _storage_class_rows(conn)
        cold = _cold_metadata_stats(conn)
        pragmas = {
            "page_size": conn.execute("PRAGMA page_size").fetchone()[0],
            "page_count": conn.execute("PRAGMA page_count").fetchone()[0],
            "freelist_count": conn.execute("PRAGMA freelist_count").fetchone()[0],
        }
    return {
        "ok": True,
        "db_path": str(db_path),
        "db_bytes": db_path.stat().st_size,
        "schema_version": SCHEMA_VERSION,
        "cold_root": str(root),
        "cold_root_exists": root.is_dir(),
        "event_totals": event_totals,
        "by_type": by_type,
        "by_storage_class": by_storage,
        "cold": cold,
        "sqlite": pragmas,
        "policy": {
            "core": "human conversation and compact searchable evidence remain in SQLite",
            "evidence": "large tool output, metadata payloads, patches, and assets move to immutable cold blobs",
            "noise": "token/status/reasoning telemetry keeps only a hash stub",
            "quarantine": "unknown event payloads remain losslessly available in cold storage",
        },
    }


def rebuild_archive(
    source_db: Path,
    target_db: Path,
    *,
    cold_root: Path | None = None,
    apply: bool = False,
    batch_size: int = 1000,
) -> dict[str, Any]:
    source_db = source_db.expanduser().resolve()
    target_db = target_db.expanduser().resolve()
    root = (cold_root or default_cold_root(target_db)).expanduser().resolve()
    base = {
        "ok": False,
        "applied": apply,
        "source_db": str(source_db),
        "target_db": str(target_db),
        "cold_root": str(root),
        "source_bytes": source_db.stat().st_size if source_db.exists() else 0,
        "target_bytes": target_db.stat().st_size if target_db.exists() else 0,
        "error": None,
    }
    if not source_db.is_file():
        return {**base, "error": "source_missing"}
    if source_db == target_db:
        return {**base, "error": "target_must_differ_from_source"}
    if target_db.exists():
        return {**base, "error": "target_exists"}
    if not apply:
        return {**base, "ok": True, "plan": storage_audit(source_db)}

    target_db.parent.mkdir(parents=True, exist_ok=True)
    blob_store = ColdBlobStore(root)
    with closing(connect_readonly(source_db)) as source, closing(connect(target_db)) as target:
        init_db(target)
        target.execute("PRAGMA synchronous = NORMAL")
        target.execute("PRAGMA foreign_keys = OFF")
        target.executescript(
            """
            DROP TRIGGER IF EXISTS events_ai;
            DROP TRIGGER IF EXISTS events_ad;
            DROP TRIGGER IF EXISTS events_au;
            DELETE FROM events_fts;
            """
        )
        _copy_meta(source, target)
        for table in COPY_TABLES:
            _copy_table(source, target, table, batch_size=batch_size)
        target.execute("UPDATE sessions SET parse_version = ?", (SCHEMA_VERSION,))
        event_result = _copy_events(source, target, blob_store, source_db, batch_size=batch_size)
        event_result["duplicate_agent_messages_removed"] = deduplicate_agent_messages(target)
        recreate_clean_fts(target)
        target.execute("PRAGMA foreign_keys = ON")
        target.commit()
        target_doctor = doctor(target)
        target_stats = stats(target)
        target_digest = conversation_digest(target)
        source_digest = conversation_digest(source)
        source_counts = _archive_counts(source)
        target_counts = _archive_counts(target)

    cold_verify = verify_cold_storage(target_db, root, deep=False)
    validations = {
        "counts_equal": source_counts == target_counts,
        "conversation_digest_equal": source_digest == target_digest,
        "doctor_ok": target_doctor["ok"],
        "cold_ok": cold_verify["ok"],
    }
    return {
        **base,
        "ok": all(validations.values()),
        "target_bytes": target_db.stat().st_size,
        "events": event_result,
        "source_counts": source_counts,
        "target_counts": target_counts,
        "source_conversation_digest": source_digest,
        "target_conversation_digest": target_digest,
        "validations": validations,
        "target_doctor": target_doctor,
        "target_stats": target_stats,
        "cold": cold_verify,
    }


def verify_cold_storage(db_path: Path, cold_root: Path | None = None, *, deep: bool = False) -> dict[str, Any]:
    db_path = db_path.expanduser().resolve()
    root = (cold_root or default_cold_root(db_path)).expanduser().resolve()
    store = ColdBlobStore(root)
    missing = 0
    invalid = 0
    checked = 0
    original_bytes = 0
    stored_bytes = 0
    errors: list[dict[str, Any]] = []
    with closing(connect_readonly(db_path)) as conn:
        if not _table_exists(conn, "cold_blobs"):
            return {
                "ok": True,
                "cold_root": str(root),
                "blobs": 0,
                "message": "Database has no cold blob metadata.",
            }
        for row in conn.execute(
            "SELECT blob_id, relative_path, codec, kind, original_bytes, stored_bytes, sha256 FROM cold_blobs"
        ):
            record = ColdBlobRecord(**dict(row))
            checked += 1
            original_bytes += record.original_bytes
            stored_bytes += record.stored_bytes
            path = root / record.relative_path
            if not path.is_file():
                missing += 1
                if len(errors) < 20:
                    errors.append({"blob_id": record.blob_id, "error": "missing"})
                continue
            if path.stat().st_size != record.stored_bytes:
                invalid += 1
                if len(errors) < 20:
                    errors.append({"blob_id": record.blob_id, "error": "stored_size_mismatch"})
                continue
            if deep:
                result = store.verify(record)
                if not result["ok"]:
                    invalid += 1
                    if len(errors) < 20:
                        errors.append({"blob_id": record.blob_id, "error": result["error"]})
    return {
        "ok": missing == 0 and invalid == 0,
        "cold_root": str(root),
        "blobs": checked,
        "missing": missing,
        "invalid": invalid,
        "original_bytes": original_bytes,
        "stored_bytes": stored_bytes,
        "deep": deep,
        "errors": errors,
    }


def prune_cold_storage(
    db_path: Path,
    cold_root: Path | None = None,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Remove cold blobs that are no longer referenced by any event."""
    db_path = db_path.expanduser().resolve()
    root = (cold_root or default_cold_root(db_path)).expanduser().resolve()
    with connect(db_path) as conn:
        init_db(conn)
        references: set[str] = {
            row[0]
            for row in conn.execute("SELECT DISTINCT payload_ref FROM events WHERE payload_ref IS NOT NULL")
        }
        for row in conn.execute(
            "SELECT payload_json FROM events WHERE payload_json LIKE '%_ref%'"):
            try:
                _collect_blob_refs(json.loads(row[0]), references)
            except (TypeError, json.JSONDecodeError):
                continue
        metadata = {
            row["blob_id"]: dict(row)
            for row in conn.execute("SELECT * FROM cold_blobs")
        }
        unreferenced = sorted(set(metadata) - references)
        known_paths = {item["relative_path"] for item in metadata.values()}
        orphan_files = [
            path
            for path in root.rglob("*")
            if path.is_file() and path.relative_to(root).as_posix() not in known_paths
        ] if root.is_dir() else []
        reclaimable = sum(
            (root / metadata[blob_id]["relative_path"]).stat().st_size
            for blob_id in unreferenced
            if (root / metadata[blob_id]["relative_path"]).is_file()
        ) + sum(path.stat().st_size for path in orphan_files)
        deleted_files = 0
        if apply:
            for blob_id in unreferenced:
                path = root / metadata[blob_id]["relative_path"]
                if path.is_file():
                    path.unlink()
                    deleted_files += 1
            for path in orphan_files:
                path.unlink()
                deleted_files += 1
            conn.executemany("DELETE FROM cold_blobs WHERE blob_id = ?", [(value,) for value in unreferenced])
            conn.commit()
            _remove_empty_directories(root)
    return {
        "ok": True,
        "applied": apply,
        "db_path": str(db_path),
        "cold_root": str(root),
        "referenced_blobs": len(references),
        "unreferenced_metadata": len(unreferenced),
        "orphan_files": len(orphan_files),
        "reclaimable_bytes": reclaimable,
        "deleted_files": deleted_files,
        "deleted_metadata": len(unreferenced) if apply else 0,
    }


def backup_storage_profile(
    db_path: Path,
    out_dir: Path,
    *,
    profile: str = "core",
    cold_root: Path | None = None,
    codex_home: Path | None = None,
    force: bool = False,
) -> dict[str, Any]:
    if profile not in STORAGE_PROFILES:
        raise ValueError(f"Unsupported storage backup profile: {profile}")
    db_path = db_path.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = out_dir / f"threadvault-{profile}-{timestamp}.db"
    backup = backup_database(db_path, backup_path, force=force)
    if not backup["ok"]:
        return {"ok": False, "profile": profile, "database": backup}
    backup["manifest"] = write_backup_manifest(backup)
    cold_summary = {"included": False, "copied": 0, "skipped": 0, "bytes": 0}
    forensic: list[dict[str, Any]] = []
    if profile in {"evidence", "forensic"}:
        source_cold = (cold_root or default_cold_root(db_path)).expanduser().resolve()
        cold_summary = _sync_cold_files(source_cold, out_dir / "cold")
    if profile == "forensic":
        forensic = _sync_forensic_files(codex_home, out_dir / "forensic")
    manifest = {
        "contract_version": STORAGE_BACKUP_VERSION,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "profile": profile,
        "database": {
            "path": str(backup_path),
            "sha256": sha256_file(backup_path),
            "bytes": backup_path.stat().st_size,
        },
        "cold": cold_summary,
        "forensic": forensic,
        "archive_state": archive_storage_state(
            db_path,
            cold_root=cold_root,
            codex_home=codex_home,
            include_source=profile == "forensic",
        ),
    }
    manifest_path = out_dir / f"threadvault-{profile}-{timestamp}.storage-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "profile": profile,
        "database": backup,
        "cold": cold_summary,
        "forensic_files": len(forensic),
        "manifest": str(manifest_path),
    }


def archive_storage_state(
    db_path: Path,
    *,
    cold_root: Path | None = None,
    codex_home: Path | None = None,
    include_source: bool = False,
) -> dict[str, Any]:
    """Return a cheap logical fingerprint for smart backup decisions."""
    db_path = db_path.expanduser().resolve()
    root = (cold_root or default_cold_root(db_path)).expanduser().resolve()
    with closing(connect_readonly(db_path)) as conn:
        database = dict(conn.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM sessions) AS sessions,
              (SELECT COUNT(*) FROM events) AS events,
              (SELECT COUNT(*) FROM parse_warnings) AS warnings,
              (SELECT MAX(updated_at) FROM sessions) AS updated_at
            """
        ).fetchone())
        cold = _cold_metadata_stats(conn)
    source = None
    if include_source:
        files = discover_jsonl_files(codex_home)
        source = {
            "files": len(files),
            "bytes": sum(path.stat().st_size for path, _ in files),
            "latest_mtime_ns": max((path.stat().st_mtime_ns for path, _ in files), default=0),
        }
    return {
        "database": {**database, "bytes": db_path.stat().st_size},
        "cold": {**cold, "root": str(root)},
        "source": source,
    }


def verify_storage_backup(manifest_path: Path, *, deep: bool = False) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        return {"ok": False, "error": "manifest_missing", "manifest": str(manifest_path)}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    backup_db = Path(manifest["database"]["path"])
    db_verify = verify_database_backup(backup_db)
    sha_ok = backup_db.is_file() and sha256_file(backup_db) == manifest["database"]["sha256"]
    cold_verify = None
    if manifest.get("profile") in {"evidence", "forensic"}:
        cold_verify = verify_cold_storage(backup_db, manifest_path.parent / "cold", deep=deep)
    forensic_errors: list[dict[str, str]] = []
    if manifest.get("profile") == "forensic" and deep:
        for item in manifest.get("forensic", []):
            path = manifest_path.parent / item["relative_path"]
            if not path.is_file():
                forensic_errors.append({"path": str(path), "error": "missing"})
                continue
            digest = hashlib.sha256()
            with gzip.open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != item["sha256"]:
                forensic_errors.append({"path": str(path), "error": "sha256_mismatch"})
    ok = db_verify["ok"] and sha_ok and (cold_verify is None or cold_verify["ok"]) and not forensic_errors
    return {
        "ok": ok,
        "manifest": str(manifest_path),
        "profile": manifest.get("profile"),
        "database": db_verify,
        "database_sha256_ok": sha_ok,
        "cold": cold_verify,
        "forensic_errors": forensic_errors,
    }


def conversation_digest(conn: sqlite3.Connection) -> str:
    digest = hashlib.sha256()
    rows = conn.execute(
        """
        SELECT event_id, top_type, sub_type, COALESCE(role, '') AS role, COALESCE(text_content, '') AS text_content
        FROM events
        WHERE
          (top_type = 'event_msg' AND sub_type = 'user_message')
          OR (top_type = 'response_item' AND sub_type = 'message' AND role IN ('assistant', 'developer'))
          OR top_type = 'compacted'
        ORDER BY event_id
        """
    )
    for row in rows:
        digest.update(json.dumps(list(row), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _copy_events(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    blob_store: ColdBlobStore,
    source_db: Path,
    *,
    batch_size: int,
) -> dict[str, int]:
    source_columns = {row["name"] for row in source.execute("PRAGMA table_info(events)")}
    selected = [
        "event_id", "session_id", "turn_id", "timestamp", "top_type", "sub_type", "role", "call_id",
        "tool_name", "file_path", "text_content", "payload_json", "line_no", "turn_index",
    ]
    if "payload_ref" in source_columns:
        selected.append("payload_ref")
    cursor = source.execute(f"SELECT {', '.join(selected)} FROM events ORDER BY event_id")
    inserted = 0
    blobs = 0
    original_payload_bytes = 0
    hot_payload_bytes = 0
    source_cold = ColdBlobStore(default_cold_root(source_db))
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        prepared_rows = []
        metadata_rows: dict[str, tuple[Any, ...]] = {}
        for row in rows:
            event = dict(row)
            payload_json = _hydrate_source_payload(source, source_cold, event)
            payload = json.loads(payload_json)
            event["payload"] = payload if isinstance(payload, dict) else {"value": payload}
            if event.get("payload_ref") and event.get("text_content"):
                extracted = extract_current_text(event["top_type"], event["payload"])
                if extracted:
                    event["text_content"] = extracted
            prepared = prepare_event_content(event, blob_store)
            classification = classify_index_text({**event, "text_content": prepared.text_content})
            original_payload_bytes += prepared.payload_original_bytes
            hot_payload_bytes += len(prepared.payload_json.encode("utf-8"))
            prepared_rows.append((
                event["event_id"], event["session_id"], event.get("turn_id"), event.get("timestamp"),
                event["top_type"], event.get("sub_type"), event.get("role"), event.get("call_id"),
                event.get("tool_name"), event.get("file_path"), prepared.text_content,
                classification["indexed_text"], classification["index_policy"], classification["value_level"],
                prepared.payload_json, event.get("line_no"), event.get("turn_index"), prepared.payload_ref,
                prepared.payload_original_bytes, prepared.text_original_chars, prepared.storage_class,
                prepared.content_flags_json,
            ))
            for record in prepared.blob_records:
                metadata_rows[record.blob_id] = (
                    record.blob_id, record.relative_path, record.codec, record.kind,
                    record.original_bytes, record.stored_bytes, record.sha256,
                )
        target.executemany(
            """
            INSERT INTO events (
              event_id, session_id, turn_id, timestamp, top_type, sub_type, role, call_id,
              tool_name, file_path, text_content, indexed_text, index_policy, value_level,
              payload_json, line_no, turn_index, payload_ref, payload_original_bytes,
              text_original_chars, storage_class, content_flags_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            prepared_rows,
        )
        target.executemany(
            """
            INSERT OR IGNORE INTO cold_blobs (
              blob_id, relative_path, codec, kind, original_bytes, stored_bytes, sha256
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            metadata_rows.values(),
        )
        inserted += len(prepared_rows)
        blobs += len(metadata_rows)
        target.commit()
    return {
        "inserted": inserted,
        "blob_references_written": blobs,
        "original_payload_bytes": original_payload_bytes,
        "hot_payload_bytes": hot_payload_bytes,
        "payload_bytes_removed_from_hot": max(0, original_payload_bytes - hot_payload_bytes),
    }


def _hydrate_source_payload(source: sqlite3.Connection, cold: ColdBlobStore, event: dict[str, Any]) -> str:
    ref = event.get("payload_ref")
    if not ref:
        return event["payload_json"]
    row = source.execute(
        "SELECT relative_path, codec FROM cold_blobs WHERE blob_id = ?",
        (ref,),
    ).fetchone()
    if row is None:
        return event["payload_json"]
    return cold.read(row["relative_path"], row["codec"]).decode("utf-8")


def _copy_meta(source: sqlite3.Connection, target: sqlite3.Connection) -> None:
    if not _table_exists(source, "meta"):
        return
    rows = source.execute("SELECT key, value FROM meta WHERE key <> 'schema_version'").fetchall()
    target.executemany("INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)", rows)
    target.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))


def _copy_table(source: sqlite3.Connection, target: sqlite3.Connection, table: str, *, batch_size: int) -> None:
    if not _table_exists(source, table) or not _table_exists(target, table):
        return
    source_cols = [row["name"] for row in source.execute(f"PRAGMA table_info({table})")]
    target_cols = {row["name"] for row in target.execute(f"PRAGMA table_info({table})")}
    columns = [column for column in source_cols if column in target_cols]
    cursor = source.execute(f"SELECT {', '.join(columns)} FROM {table}")
    placeholders = ", ".join("?" for _ in columns)
    statement = f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        values = []
        for row in rows:
            item = list(row)
            if table == "turns":
                for field in ("user_message_text", "assistant_message_text", "summary_text", "token_usage_json"):
                    if field in columns:
                        item[columns.index(field)] = None
            values.append(item)
        target.executemany(statement, values)
        target.commit()


def _archive_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "sessions": conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
        "events": conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
        "warnings": conn.execute("SELECT COUNT(*) FROM parse_warnings").fetchone()[0],
    }


def _cold_metadata_stats(conn: sqlite3.Connection) -> dict[str, int]:
    if not _table_exists(conn, "cold_blobs"):
        return {"blobs": 0, "original_bytes": 0, "stored_bytes": 0}
    row = conn.execute(
        "SELECT COUNT(*) AS blobs, SUM(original_bytes) AS original_bytes, SUM(stored_bytes) AS stored_bytes FROM cold_blobs"
    ).fetchone()
    return {key: int(row[key] or 0) for key in ("blobs", "original_bytes", "stored_bytes")}


def _storage_class_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(events)")}
    if "storage_class" not in columns:
        return [{"storage_class": "legacy", "events": conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]}]
    return [dict(row) for row in conn.execute(
        """
        SELECT storage_class, COUNT(*) AS events,
               SUM(LENGTH(payload_json)) AS hot_payload_chars,
               SUM(payload_original_bytes) AS original_payload_bytes
        FROM events GROUP BY storage_class ORDER BY events DESC
        """
    )]


def _sync_cold_files(source: Path, destination: Path) -> dict[str, Any]:
    summary = {"included": True, "source": str(source), "destination": str(destination), "copied": 0, "skipped": 0, "bytes": 0}
    if not source.is_dir():
        return summary
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size == path.stat().st_size:
            summary["skipped"] += 1
        else:
            shutil.copy2(path, target)
            summary["copied"] += 1
        summary["bytes"] += path.stat().st_size
    return summary


def _sync_forensic_files(codex_home: Path | None, destination: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path, archived in discover_jsonl_files(codex_home):
        digest = sha256_file(path)
        relative = Path("forensic") / "blobs" / digest[:2] / f"{digest}.jsonl.gz"
        target = destination.parent / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with path.open("rb") as source, gzip.open(target, "wb", compresslevel=6) as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
        entries.append({
            "sha256": digest,
            "relative_path": relative.as_posix(),
            "source_name": path.name,
            "archived": archived,
            "original_bytes": path.stat().st_size,
            "stored_bytes": target.stat().st_size,
        })
    return entries


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _collect_blob_refs(value: Any, references: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith("_ref") and isinstance(child, str) and _looks_like_sha256(child):
                references.add(child)
            else:
                _collect_blob_refs(child, references)
    elif isinstance(value, list):
        for child in value:
            _collect_blob_refs(child, references)


def _looks_like_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in string.hexdigits for char in value)


def _remove_empty_directories(root: Path) -> None:
    if not root.is_dir():
        return
    for path in sorted((item for item in root.rglob("*") if item.is_dir()), reverse=True):
        try:
            path.rmdir()
        except OSError:
            continue

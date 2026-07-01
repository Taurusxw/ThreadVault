from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .app_config import AppConfig
from .summary_pipeline import SummaryChunkRequest, build_summary_chunks

VECTOR_CONTRACT_VERSION = "vector.v1"
LOCAL_VECTOR_ADAPTER = "local-hash"
DEFAULT_VECTOR_DIMENSIONS = 64
TOKEN_PATTERN = re.compile(r"[\w.\-:/\\]+", re.UNICODE)


@dataclass(frozen=True)
class VectorIndexRequest:
    session_ids: list[str] = field(default_factory=list)
    project: str | None = None
    max_chunks_per_session: int = 12
    max_chars: int = 1200


def build_vector_index(conn: sqlite3.Connection, request: VectorIndexRequest, config: AppConfig) -> dict[str, Any]:
    _require_enabled(config)
    _validate_adapter(config)
    chunk_payload = build_summary_chunks(
        conn,
        SummaryChunkRequest(
            session_ids=request.session_ids,
            project=request.project,
            max_chunks_per_session=request.max_chunks_per_session,
            max_chars=request.max_chars,
        ),
    )
    adapter = config.vector_adapter
    dimensions = config.vector_dimensions
    indexed_at = _utc_now()
    selected_session_ids = chunk_payload["selection"]["selected_session_ids"]
    if selected_session_ids:
        placeholders = ",".join("?" for _ in selected_session_ids)
        conn.execute(
            f"DELETE FROM vector_chunks WHERE adapter = ? AND dimensions = ? AND session_id IN ({placeholders})",
            [adapter, dimensions, *selected_session_ids],
        )

    for chunk in chunk_payload["chunks"]:
        vector = embed_text(chunk["text"], dimensions)
        conn.execute(
            """
            INSERT OR REPLACE INTO vector_chunks(
              chunk_id, adapter, dimensions, chunk_type, session_id, turn_index,
              text, text_hash, vector_json, evidence_event_ids_json, metadata_json, indexed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chunk["chunk_id"],
                adapter,
                dimensions,
                chunk["chunk_type"],
                chunk["session_id"],
                chunk["turn_index"],
                chunk["text"],
                _text_hash(chunk["text"]),
                json.dumps(vector, separators=(",", ":")),
                json.dumps(chunk["evidence_event_ids"], separators=(",", ":")),
                json.dumps(chunk["metadata"], ensure_ascii=False, separators=(",", ":")),
                indexed_at,
            ),
        )

    total_count = _indexed_chunk_count(conn, adapter, dimensions)
    conn.execute(
        """
        INSERT OR REPLACE INTO vector_index_meta(key, adapter, dimensions, chunk_count, built_at)
        VALUES ('default', ?, ?, ?, ?)
        """,
        (adapter, dimensions, total_count, indexed_at),
    )
    conn.commit()
    return {
        "contract_version": VECTOR_CONTRACT_VERSION,
        "ok": True,
        "adapter": adapter,
        "dimensions": dimensions,
        "source": {
            "schema": "summary_chunks",
            "selection": chunk_payload["selection"],
            "skipped": chunk_payload["skipped"],
        },
        "indexed": {
            "chunks": len(chunk_payload["chunks"]),
            "total_chunks": total_count,
            "built_at": indexed_at,
        },
        "diagnostics": {
            "config_enabled": config.vector_enabled,
            "embedding_generated": True,
            "embedding_kind": "local_deterministic_hash",
            "external_provider": False,
            "raw_events_indexed": False,
        },
    }


def query_vector_index(conn: sqlite3.Connection, query: str, config: AppConfig, limit: int = 10) -> dict[str, Any]:
    _require_enabled(config)
    _validate_adapter(config)
    adapter = config.vector_adapter
    dimensions = config.vector_dimensions
    query_vector = embed_text(query, dimensions)
    rows = conn.execute(
        """
        SELECT chunk_id, chunk_type, session_id, turn_index, text, vector_json,
               evidence_event_ids_json, metadata_json, indexed_at
        FROM vector_chunks
        WHERE adapter = ? AND dimensions = ?
        """,
        (adapter, dimensions),
    ).fetchall()
    scored = []
    for row in rows:
        score = _dot(query_vector, json.loads(row["vector_json"]))
        if score <= 0:
            continue
        scored.append({
            "chunk_id": row["chunk_id"],
            "chunk_type": row["chunk_type"],
            "session_id": row["session_id"],
            "turn_index": row["turn_index"],
            "score": score,
            "text": row["text"],
            "evidence_event_ids": json.loads(row["evidence_event_ids_json"]),
            "metadata": json.loads(row["metadata_json"]),
            "indexed_at": row["indexed_at"],
        })
    scored.sort(key=lambda item: (-item["score"], item["chunk_id"]))
    results = scored[:limit]
    return {
        "contract_version": VECTOR_CONTRACT_VERSION,
        "query": {
            "text": query,
            "limit": limit,
            "adapter": adapter,
            "dimensions": dimensions,
        },
        "results": results,
        "diagnostics": {
            "config_enabled": config.vector_enabled,
            "adapter": adapter,
            "dimensions": dimensions,
            "indexed_chunks": len(rows),
            "result_count": len(results),
            "embedding_kind": "local_deterministic_hash",
            "external_provider": False,
        },
    }


def vector_index_status(conn: sqlite3.Connection, config: AppConfig | None = None) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM vector_index_meta WHERE key = 'default'").fetchone()
    adapter = config.vector_adapter if config else (row["adapter"] if row else LOCAL_VECTOR_ADAPTER)
    dimensions = config.vector_dimensions if config else (row["dimensions"] if row else DEFAULT_VECTOR_DIMENSIONS)
    indexed_chunks = _indexed_chunk_count(conn, adapter, dimensions)
    return {
        "contract_version": VECTOR_CONTRACT_VERSION,
        "ok": True,
        "config": {
            "enabled": config.vector_enabled if config else False,
            "adapter": adapter,
            "dimensions": dimensions,
        },
        "index": {
            "exists": row is not None,
            "adapter": row["adapter"] if row else None,
            "dimensions": row["dimensions"] if row else None,
            "chunk_count": row["chunk_count"] if row else 0,
            "built_at": row["built_at"] if row else None,
            "matching_chunks": indexed_chunks,
        },
        "diagnostics": {
            "source_schema": "summary_chunks",
            "embedding_kind": "local_deterministic_hash",
            "external_provider": False,
            "raw_events_indexed": False,
        },
    }


def embed_text(text: str, dimensions: int) -> list[float]:
    if dimensions < 1:
        raise ValueError("dimensions must be at least 1.")
    vector = [0.0] * dimensions
    tokens = TOKEN_PATTERN.findall(text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _require_enabled(config: AppConfig) -> None:
    if not config.vector_enabled:
        raise PermissionError("local vector adapter is disabled; set retrieval.vector.enabled = true in threadvault.toml")


def _validate_adapter(config: AppConfig) -> None:
    if config.vector_adapter != LOCAL_VECTOR_ADAPTER:
        raise ValueError("Only local-hash vector adapter is supported in this phase.")
    if config.vector_dimensions < 1:
        raise ValueError("retrieval.vector.dimensions must be at least 1.")


def _indexed_chunk_count(conn: sqlite3.Connection, adapter: str, dimensions: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM vector_chunks WHERE adapter = ? AND dimensions = ?",
        (adapter, dimensions),
    ).fetchone()
    return int(row["count"])


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

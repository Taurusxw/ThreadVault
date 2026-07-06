from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from .database import build_fts_query, search_events
from .models import SearchResult

RETRIEVAL_CONTRACT_VERSION = "retrieval.v1"
RETRIEVAL_MODES = ["fts"]
SEARCH_FIELDS = {"minimal", "standard", "full"}


@dataclass(frozen=True)
class RetrievalQuery:
    text: str
    limit: int = 20
    session_id: str | None = None
    cwd: str | None = None
    since: str | None = None
    until: str | None = None
    top_type: str | None = None
    tool: str | None = None
    fields: str = "standard"
    mode: str = "fts"


@dataclass(frozen=True)
class RetrievalDiagnostics:
    requested_mode: str
    used_mode: str
    engine: str
    fields: str
    limit: int
    filters: dict[str, Any]
    fallback: dict[str, Any]
    rank_strategy: str
    result_count: int
    index_status: dict[str, Any]
    warnings: list[str]

    def to_payload(self) -> dict[str, Any]:
        return {
            "requested_mode": self.requested_mode,
            "used_mode": self.used_mode,
            "engine": self.engine,
            "fields": self.fields,
            "limit": self.limit,
            "filters": self.filters,
            "fallback": self.fallback,
            "rank_strategy": self.rank_strategy,
            "result_count": self.result_count,
            "index_status": self.index_status,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class RetrievalResponse:
    contract_version: str
    query: dict[str, Any]
    diagnostics: RetrievalDiagnostics
    results: list[SearchResult]

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "query": self.query,
            "diagnostics": self.diagnostics.to_payload(),
            "results": [result.model_dump() for result in self.results],
        }


def retrieve(conn: sqlite3.Connection, query: RetrievalQuery) -> list[SearchResult]:
    return retrieve_response(conn, query).results


def retrieve_response(conn: sqlite3.Connection, query: RetrievalQuery) -> RetrievalResponse:
    if query.mode not in RETRIEVAL_MODES:
        raise ValueError("Only fts retrieval mode is supported.")
    if query.fields not in SEARCH_FIELDS:
        raise ValueError("fields must be minimal, standard, or full.")
    fallback_used = False
    effective_text = query.text
    try:
        results = _search_fts(conn, query)
    except sqlite3.OperationalError:
        quoted = f'"{query.text.replace(chr(34), chr(34) + chr(34))}"'
        fallback_used = True
        effective_text = quoted
        results = _search_fts(conn, RetrievalQuery(**{**query.__dict__, "text": quoted}))
    diagnostics = build_retrieval_diagnostics(
        conn,
        query,
        result_count=len(results),
        fallback_used=fallback_used,
        effective_text=effective_text,
    )
    return RetrievalResponse(
        contract_version=RETRIEVAL_CONTRACT_VERSION,
        query={
            "text": query.text,
            "limit": query.limit,
            "fields": query.fields,
            "mode": query.mode,
        },
        diagnostics=diagnostics,
        results=results,
    )


def build_retrieval_diagnostics(
    conn: sqlite3.Connection,
    query: RetrievalQuery | None = None,
    result_count: int = 0,
    fallback_used: bool = False,
    effective_text: str | None = None,
) -> RetrievalDiagnostics:
    engine = "sqlite_fts5"
    rank_strategy = "bm25(events_fts)"
    if query and build_fts_query(effective_text or query.text) is None:
        engine = "sqlite_like_fallback"
        rank_strategy = "constant_like_rank"
    return RetrievalDiagnostics(
        requested_mode=query.mode if query else "fts",
        used_mode="fts",
        engine=engine,
        fields=query.fields if query else "standard",
        limit=query.limit if query else 0,
        filters=_filter_summary(query),
        fallback={
            "used": fallback_used,
            "reason": "sqlite_operational_error" if fallback_used else None,
        },
        rank_strategy=rank_strategy,
        result_count=result_count,
        index_status=fts_index_status(conn),
        warnings=[],
    )


def fts_index_status(conn: sqlite3.Connection) -> dict[str, Any]:
    try:
        event_count = conn.execute("SELECT COUNT(*) AS count FROM events").fetchone()["count"]
        fts_count = conn.execute("SELECT COUNT(*) AS count FROM events_fts").fetchone()["count"]
    except sqlite3.Error as exc:
        return {
            "ok": False,
            "event_count": None,
            "fts_count": None,
            "message": str(exc),
        }
    return {
        "ok": event_count == fts_count,
        "event_count": event_count,
        "fts_count": fts_count,
        "content_column": "indexed_text",
        "index_policy": "cleaned_knowledge_index",
        "message": f"events={event_count}, events_fts={fts_count}, content=indexed_text",
    }


def _filter_summary(query: RetrievalQuery | None) -> dict[str, Any]:
    if query is None:
        return {
            "session_id": False,
            "cwd": False,
            "since": None,
            "until": None,
            "top_type": None,
            "tool": None,
        }
    return {
        "session_id": query.session_id is not None,
        "cwd": query.cwd is not None,
        "since": query.since,
        "until": query.until,
        "top_type": query.top_type,
        "tool": query.tool,
    }


def _search_fts(conn: sqlite3.Connection, query: RetrievalQuery) -> list[SearchResult]:
    return search_events(
        conn,
        query=query.text,
        limit=query.limit,
        session_id=query.session_id,
        cwd=query.cwd,
        since=query.since,
        until=query.until,
        top_type=query.top_type,
        tool=query.tool,
        fields=query.fields,
    )

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from .app_config import AppConfig
from .retrieval import RetrievalQuery, retrieve_response
from .vector_adapter import query_vector_index, vector_index_status

HYBRID_RETRIEVAL_CONTRACT_VERSION = "hybrid_retrieval.v1"
HYBRID_RANKING_WEIGHTS = {
    "fts": 0.65,
    "vector": 0.35,
    "same_project": 0.05,
    "exact_hint": 0.05,
}


@dataclass(frozen=True)
class HybridRetrievalRequest:
    text: str
    limit: int = 20
    vector_limit: int = 10
    session_id: str | None = None
    cwd: str | None = None
    since: str | None = None
    until: str | None = None
    top_type: str | None = None
    tool: str | None = None


def hybrid_retrieve(conn: sqlite3.Connection, request: HybridRetrievalRequest, config: AppConfig) -> dict[str, Any]:
    fts_response = retrieve_response(
        conn,
        RetrievalQuery(
            text=request.text,
            limit=request.limit,
            session_id=request.session_id,
            cwd=request.cwd,
            since=request.since,
            until=request.until,
            top_type=request.top_type,
            tool=request.tool,
            fields="full",
            mode="fts",
        ),
    )
    fts_results = fts_response.results
    vector_payload, vector_status = _optional_vector_query(conn, request, config)
    candidates = _fts_candidates(fts_results, request) + _vector_candidates(vector_payload, request)
    candidates.sort(key=lambda item: (-item["score"], item["source"], item["hybrid_id"]))
    results = candidates[: request.limit]
    vector_used = bool(vector_payload and vector_payload["results"])
    return {
        "contract_version": HYBRID_RETRIEVAL_CONTRACT_VERSION,
        "query": {
            "text": request.text,
            "limit": request.limit,
            "vector_limit": request.vector_limit,
            "filters": _filter_summary(request),
        },
        "results": results,
        "diagnostics": {
            "capabilities_used": ["fts", "vector", "hybrid"] if vector_used else ["fts", "hybrid"],
            "fts": {
                "used": True,
                "result_count": len(fts_results),
                "engine": fts_response.diagnostics.engine,
                "rank_strategy": fts_response.diagnostics.rank_strategy,
            },
            "vector": vector_status,
            "ranking": {
                "strategy": "weighted_sum",
                "weights": HYBRID_RANKING_WEIGHTS,
                "result_count": len(results),
            },
        },
    }


def _optional_vector_query(
    conn: sqlite3.Connection,
    request: HybridRetrievalRequest,
    config: AppConfig,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    status_payload = vector_index_status(conn, config)
    if not config.vector_enabled:
        return None, {
            "used": False,
            "status": "disabled_by_config",
            "index": status_payload["index"],
        }
    if not status_payload["index"]["exists"] or status_payload["index"]["matching_chunks"] == 0:
        return None, {
            "used": False,
            "status": "empty_index",
            "index": status_payload["index"],
        }
    try:
        payload = query_vector_index(conn, request.text, config=config, limit=request.vector_limit)
    except (PermissionError, ValueError) as exc:
        return None, {
            "used": False,
            "status": "unavailable",
            "error": str(exc),
            "index": status_payload["index"],
        }
    return payload, {
        "used": bool(payload["results"]),
        "status": "used" if payload["results"] else "no_matches",
        "result_count": len(payload["results"]),
        "index": status_payload["index"],
    }


def _fts_candidates(results, request: HybridRetrievalRequest) -> list[dict[str, Any]]:
    if not results:
        return []
    raw_scores = [_fts_score(result.rank) for result in results]
    max_score = max(raw_scores) or 1.0
    candidates = []
    for result, raw_score in zip(results, raw_scores, strict=True):
        normalized = raw_score / max_score
        boosts = _boosts(
            request,
            session_id=result.session_id,
            text=result.snippet or "",
            file_path=result.file_path,
            project=None,
        )
        scores = {
            "fts": round(normalized, 6),
            "vector": 0.0,
            "same_project": boosts["same_project"],
            "exact_hint": boosts["exact_hint"],
        }
        final = _final_score(scores)
        candidates.append({
            "hybrid_id": f"fts:event:{result.event_id}",
            "source": "fts",
            "score": final,
            "scores": scores,
            "session_id": result.session_id,
            "event_id": result.event_id,
            "chunk_id": None,
            "chunk_type": None,
            "text": result.snippet or "",
            "evidence_event_ids": [result.event_id],
            "metadata": {
                "timestamp": result.timestamp,
                "top_type": result.top_type,
                "sub_type": result.sub_type,
                "role": result.role,
                "tool_name": result.tool_name,
                "file_path": result.file_path,
            },
            "explanation": _explanation("fts", scores, ["fts", *boosts["matched_by"]]),
        })
    return candidates


def _vector_candidates(payload: dict[str, Any] | None, request: HybridRetrievalRequest) -> list[dict[str, Any]]:
    if not payload:
        return []
    candidates = []
    for result in payload["results"]:
        boosts = _boosts(
            request,
            session_id=result["session_id"],
            text=result["text"],
            file_path=None,
            project=result["metadata"].get("project"),
        )
        scores = {
            "fts": 0.0,
            "vector": round(float(result["score"]), 6),
            "same_project": boosts["same_project"],
            "exact_hint": boosts["exact_hint"],
        }
        final = _final_score(scores)
        candidates.append({
            "hybrid_id": f"vector:chunk:{result['chunk_id']}",
            "source": "vector",
            "score": final,
            "scores": scores,
            "session_id": result["session_id"],
            "event_id": None,
            "chunk_id": result["chunk_id"],
            "chunk_type": result["chunk_type"],
            "text": result["text"],
            "evidence_event_ids": result["evidence_event_ids"],
            "metadata": result["metadata"],
            "explanation": _explanation("vector", scores, ["vector", *boosts["matched_by"]]),
        })
    return candidates


def _fts_score(rank: float | None) -> float:
    if rank is None:
        return 1.0
    return 1.0 / (1.0 + abs(float(rank)))


def _boosts(
    request: HybridRetrievalRequest,
    session_id: str,
    text: str,
    file_path: str | None,
    project: str | None,
) -> dict[str, Any]:
    matched_by: list[str] = []
    same_project = 0.0
    exact_hint = 0.0
    if request.session_id and request.session_id == session_id:
        matched_by.append("session_filter")
    if request.cwd and (project == request.cwd):
        same_project = 1.0
        matched_by.append("same_project")
    hint = request.text.lower()
    haystack = " ".join(part for part in [text, file_path or ""] if part).lower()
    if _looks_like_exact_hint(hint) and hint in haystack:
        exact_hint = 1.0
        matched_by.append("exact_hint")
    return {"same_project": same_project, "exact_hint": exact_hint, "matched_by": matched_by}


def _looks_like_exact_hint(text: str) -> bool:
    return any(token in text for token in [".", "/", "\\", ":"])


def _final_score(scores: dict[str, float]) -> float:
    score = (
        scores["fts"] * HYBRID_RANKING_WEIGHTS["fts"]
        + scores["vector"] * HYBRID_RANKING_WEIGHTS["vector"]
        + scores["same_project"] * HYBRID_RANKING_WEIGHTS["same_project"]
        + scores["exact_hint"] * HYBRID_RANKING_WEIGHTS["exact_hint"]
    )
    return round(min(score, 1.0), 6)


def _explanation(source: str, scores: dict[str, float], matched_by: list[str]) -> dict[str, Any]:
    return {
        "source": source,
        "matched_by": matched_by,
        "rank_factors": [
            {"name": name, "value": value, "weight": HYBRID_RANKING_WEIGHTS.get(name, 0.0)}
            for name, value in scores.items()
        ],
    }


def _filter_summary(request: HybridRetrievalRequest) -> dict[str, Any]:
    return {
        "session_id": request.session_id is not None,
        "cwd": request.cwd is not None,
        "since": request.since,
        "until": request.until,
        "top_type": request.top_type,
        "tool": request.tool,
    }

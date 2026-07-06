from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from .app_config import AppConfig
from .hybrid_retrieval import HybridRetrievalRequest, hybrid_retrieve
from .retrieval import RETRIEVAL_CONTRACT_VERSION, RetrievalQuery, retrieve_response
from .vector_adapter import LOCAL_VECTOR_ADAPTER, VECTOR_CONTRACT_VERSION, vector_index_status

AGENT_INTERFACE_CONTRACT_VERSION = "agent_interface.v1"
AGENT_RETRIEVAL_CONTRACT_VERSION = "agent_retrieval.v1"
AGENT_RETRIEVAL_MODES = ["hybrid", "fts"]


@dataclass(frozen=True)
class AgentRetrievalRequest:
    text: str
    mode: str = "hybrid"
    limit: int = 20
    vector_limit: int = 10
    session_id: str | None = None
    cwd: str | None = None
    since: str | None = None
    until: str | None = None
    top_type: str | None = None
    tool: str | None = None
    local_debug: bool = False


def agent_manifest(config: AppConfig) -> dict[str, Any]:
    return {
        "contract_version": AGENT_INTERFACE_CONTRACT_VERSION,
        "interface": {
            "name": "threadvault-agent-retrieval",
            "version": "v1",
            "module": "threadvault.agent_interface",
            "default_mode": "hybrid",
            "modes": AGENT_RETRIEVAL_MODES,
        },
        "capabilities": {
            "retrieval": True,
            "hybrid_retrieval": True,
            "fts_fallback": True,
            "vector_optional": True,
            "local_vector_enabled": config.vector_enabled,
            "local_debug_available": True,
            "mcp_runtime_included": True,
        },
        "schemas": {
            "manifest": "agent_interface_manifest",
            "retrieval": "agent_retrieval",
            "underlying": ["retrieval_query", "hybrid_retrieval", "retrieval_diagnostics", "vector_status"],
        },
        "recommended_commands": [
            "threadvault agent manifest --json",
            "threadvault agent retrieve QUERY --json",
            "threadvault agent retrieve QUERY --mode fts --json",
            "threadvault agent retrieve QUERY --mode hybrid --json",
            "threadvault mcp manifest --json",
            "threadvault mcp serve",
            "threadvault validate-json --schema agent_retrieval --input payload.json --json",
        ],
        "privacy": {
            "local_first": True,
            "raw_paths_in_default_output": False,
            "raw_transcript_paths_exposed": False,
            "local_debug_opt_in": True,
            "external_model_calls": False,
        },
        "defaults": {
            "mode": "hybrid",
            "limit": 20,
            "vector_limit": 10,
            "vector_adapter": LOCAL_VECTOR_ADAPTER,
            "vector_contract_version": VECTOR_CONTRACT_VERSION,
        },
    }


def agent_retrieve(conn: sqlite3.Connection, request: AgentRetrievalRequest, config: AppConfig) -> dict[str, Any]:
    if request.mode not in AGENT_RETRIEVAL_MODES:
        raise ValueError("mode must be hybrid or fts.")
    if request.mode == "fts":
        payload = _agent_fts_retrieve(conn, request, config)
    else:
        payload = _agent_hybrid_retrieve(conn, request, config)
    payload["privacy"] = {
        "raw_paths_included": request.local_debug,
        "local_debug": request.local_debug,
        "external_model_calls": False,
    }
    return payload


def _agent_fts_retrieve(conn: sqlite3.Connection, request: AgentRetrievalRequest, config: AppConfig) -> dict[str, Any]:
    response = retrieve_response(
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
            fields="full" if request.local_debug else "standard",
            mode="fts",
        ),
    )
    results = []
    for index, result in enumerate(response.results):
        score = _rank_position_score(index)
        item = {
            "result_id": f"fts:event:{result.event_id}",
            "source": "fts",
            "score": score,
            "session_id": result.session_id,
            "event_id": result.event_id,
            "chunk_id": None,
            "text": result.snippet or "",
            "evidence_event_ids": [result.event_id],
            "explanation": {
                "matched_by": ["fts"],
                "rank_factors": [{"name": "fts_rank_position", "value": score, "weight": 1.0}],
            },
        }
        if request.local_debug:
            item["metadata"] = {
                "timestamp": result.timestamp,
                "top_type": result.top_type,
                "sub_type": result.sub_type,
                "role": result.role,
                "tool_name": result.tool_name,
                "file_path": result.file_path,
                "rank": result.rank,
            }
        results.append(item)
    return {
        "contract_version": AGENT_RETRIEVAL_CONTRACT_VERSION,
        "request": _request_payload(request, used_mode="fts"),
        "results": results,
        "diagnostics": {
            "used_mode": "fts",
            "underlying_contract": RETRIEVAL_CONTRACT_VERSION,
            "capabilities_used": ["fts"],
            "result_count": len(results),
            "retrieval": response.diagnostics.to_payload(),
            "vector": vector_index_status(conn, config=config),
        },
    }


def _agent_hybrid_retrieve(conn: sqlite3.Connection, request: AgentRetrievalRequest, config: AppConfig) -> dict[str, Any]:
    payload = hybrid_retrieve(
        conn,
        HybridRetrievalRequest(
            text=request.text,
            limit=request.limit,
            vector_limit=request.vector_limit,
            session_id=request.session_id,
            cwd=request.cwd,
            since=request.since,
            until=request.until,
            top_type=request.top_type,
            tool=request.tool,
        ),
        config,
    )
    results = [_agent_hybrid_result(result, local_debug=request.local_debug) for result in payload["results"]]
    return {
        "contract_version": AGENT_RETRIEVAL_CONTRACT_VERSION,
        "request": _request_payload(request, used_mode="hybrid"),
        "results": results,
        "diagnostics": {
            "used_mode": "hybrid",
            "underlying_contract": payload["contract_version"],
            "capabilities_used": payload["diagnostics"]["capabilities_used"],
            "result_count": len(results),
            "hybrid": payload["diagnostics"],
        },
    }


def _agent_hybrid_result(result: dict[str, Any], local_debug: bool) -> dict[str, Any]:
    item = {
        "result_id": result["hybrid_id"],
        "source": result["source"],
        "score": result["score"],
        "session_id": result["session_id"],
        "event_id": result["event_id"],
        "chunk_id": result["chunk_id"],
        "text": result["text"],
        "evidence_event_ids": result["evidence_event_ids"],
        "explanation": result["explanation"],
    }
    if local_debug:
        item["metadata"] = result["metadata"]
        item["scores"] = result["scores"]
    return item


def _request_payload(request: AgentRetrievalRequest, used_mode: str) -> dict[str, Any]:
    return {
        "text": request.text,
        "requested_mode": request.mode,
        "used_mode": used_mode,
        "limit": request.limit,
        "vector_limit": request.vector_limit,
        "filters": {
            "session_id": request.session_id is not None,
            "cwd": request.cwd is not None,
            "since": request.since,
            "until": request.until,
            "top_type": request.top_type,
            "tool": request.tool,
        },
    }


def _rank_position_score(index: int) -> float:
    return round(1.0 / (index + 1), 6)

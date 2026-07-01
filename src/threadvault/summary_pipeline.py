from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from .database import get_events_filtered, get_project_sessions, get_sessions_by_ids
from .summarizer import build_summary

SUMMARY_CHUNKS_CONTRACT_VERSION = "summary_chunks.v1"
SUMMARY_CHUNK_TYPES = ["session_summary", "turn_summary", "evidence"]
DEFAULT_MAX_CHUNKS_PER_SESSION = 12
DEFAULT_MAX_CHARS = 1200


@dataclass(frozen=True)
class SummaryChunkRequest:
    session_ids: list[str] = field(default_factory=list)
    project: str | None = None
    max_chunks_per_session: int = DEFAULT_MAX_CHUNKS_PER_SESSION
    max_chars: int = DEFAULT_MAX_CHARS


def build_summary_chunks(conn: sqlite3.Connection, request: SummaryChunkRequest) -> dict[str, Any]:
    if not request.session_ids and not request.project:
        raise ValueError("Provide at least one session id or project cwd.")
    if request.max_chunks_per_session < 1:
        raise ValueError("max_chunks_per_session must be at least 1.")
    if request.max_chars < 100:
        raise ValueError("max_chars must be at least 100.")

    selection = _select_sessions(conn, request)
    chunks: list[dict[str, Any]] = []
    truncated_count = 0

    for session in selection["selected"]:
        session_chunks, session_truncated = _chunks_for_session(conn, session, request)
        chunks.extend(session_chunks)
        truncated_count += session_truncated

    chunk_type_counts = Counter(chunk["chunk_type"] for chunk in chunks)
    return {
        "contract_version": SUMMARY_CHUNKS_CONTRACT_VERSION,
        "selection": {
            "sessions": _dedupe(request.session_ids),
            "project": request.project,
            "selected_session_ids": [row["session_id"] for row in selection["selected"]],
        },
        "chunks": chunks,
        "skipped": selection["skipped"],
        "diagnostics": {
            "selected_sessions_count": len(selection["selected"]),
            "chunks_count": len(chunks),
            "chunk_type_counts": dict(chunk_type_counts),
            "max_chunks_per_session": request.max_chunks_per_session,
            "max_chars": request.max_chars,
            "truncated_chunks": truncated_count,
            "embedding_ready": True,
            "embedding_generated": False,
        },
    }


def _select_sessions(conn: sqlite3.Connection, request: SummaryChunkRequest) -> dict[str, Any]:
    explicit_session_ids = _dedupe(request.session_ids)
    explicit_sessions = get_sessions_by_ids(conn, explicit_session_ids)
    explicit_found = {row["session_id"] for row in explicit_sessions}
    skipped = [
        {"kind": "session", "session_id": session_id, "reason": "session_not_found"}
        for session_id in explicit_session_ids
        if session_id not in explicit_found
    ]

    selected: list[sqlite3.Row] = list(explicit_sessions)
    if request.project:
        project_sessions = get_project_sessions(conn, request.project)
        if project_sessions:
            selected.extend(project_sessions)
        else:
            skipped.append({"kind": "project", "project": request.project, "reason": "project_has_no_sessions"})

    return {"selected": _dedupe_session_rows(selected), "skipped": skipped}


def _chunks_for_session(conn: sqlite3.Connection, session: sqlite3.Row, request: SummaryChunkRequest) -> tuple[list[dict[str, Any]], int]:
    events = get_events_filtered(conn, session["session_id"])
    summary = build_summary(session, events)
    summary_evidence_ids = [
        event_id
        for event_id in summary.evidence_event_ids
        if any(event["event_id"] == event_id and _is_chunk_text_event(event) for event in events)
    ]
    chunks: list[dict[str, Any]] = []
    truncated_count = 0

    if summary_evidence_ids:
        chunk, was_truncated = _chunk(
            chunk_id=f"{session['session_id']}:session-summary",
            chunk_type="session_summary",
            session_id=session["session_id"],
            turn_index=None,
            text=_session_summary_text(session, summary),
            evidence_event_ids=summary_evidence_ids,
            max_chars=request.max_chars,
            metadata={
                "topic": summary.topic,
                "project": session["cwd"],
                "source": "summary",
            },
        )
        chunks.append(chunk)
        truncated_count += int(was_truncated)

    for turn_index, turn_events in _turn_groups(events).items():
        if len(chunks) >= request.max_chunks_per_session:
            break
        if not _has_text(turn_events):
            continue
        evidence_ids = [event["event_id"] for event in turn_events if _is_chunk_text_event(event)]
        if not evidence_ids:
            continue
        chunk, was_truncated = _chunk(
            chunk_id=f"{session['session_id']}:turn-{turn_index}",
            chunk_type="turn_summary",
            session_id=session["session_id"],
            turn_index=turn_index,
            text=_turn_summary_text(turn_events),
            evidence_event_ids=evidence_ids,
            max_chars=request.max_chars,
            metadata={
                "source": "turn",
                "event_count": len(turn_events),
            },
        )
        chunks.append(chunk)
        truncated_count += int(was_truncated)

    seen_evidence_ids = {event_id for chunk in chunks for event_id in chunk["evidence_event_ids"]}
    for event in _high_value_events(events, summary_evidence_ids):
        if len(chunks) >= request.max_chunks_per_session:
            break
        if event["event_id"] in seen_evidence_ids and event["sub_type"] != "function_call_output":
            continue
        if not _is_chunk_text_event(event):
            continue
        chunk, was_truncated = _chunk(
            chunk_id=f"{session['session_id']}:evidence-{event['event_id']}",
            chunk_type="evidence",
            session_id=session["session_id"],
            turn_index=event["turn_index"],
            text=_evidence_text(event),
            evidence_event_ids=[event["event_id"]],
            max_chars=request.max_chars,
            metadata={
                "source": "event",
                "top_type": event["top_type"],
                "sub_type": event["sub_type"],
                "role": event["role"],
                "tool_name": event["tool_name"],
            },
        )
        chunks.append(chunk)
        seen_evidence_ids.add(event["event_id"])
        truncated_count += int(was_truncated)

    return chunks, truncated_count


def _chunk(
    chunk_id: str,
    chunk_type: str,
    session_id: str,
    turn_index: int | None,
    text: str,
    evidence_event_ids: list[int],
    max_chars: int,
    metadata: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    trimmed, was_truncated = _trim_text(text, max_chars)
    return {
        "chunk_id": chunk_id,
        "chunk_type": chunk_type,
        "session_id": session_id,
        "turn_index": turn_index,
        "text": trimmed,
        "text_chars": len(trimmed),
        "evidence_event_ids": sorted(set(evidence_event_ids)),
        "metadata": metadata,
    }, was_truncated


def _session_summary_text(session: sqlite3.Row, summary) -> str:
    lines = [
        f"Session: {summary.session_id}",
        f"Project: {session['cwd'] or ''}",
        f"Topic: {summary.topic}",
    ]
    if summary.user_goal:
        lines.append(f"User goal: {summary.user_goal}")
    lines.append("Key steps:")
    lines.extend(_item_lines(summary.key_steps, "text"))
    lines.append("Key commands:")
    lines.extend(_item_lines(summary.key_commands, "command"))
    lines.append("Files:")
    lines.extend(_item_lines(summary.files, "path"))
    lines.append("Problems:")
    lines.extend(_item_lines(summary.problems, "text"))
    lines.append("Next steps:")
    lines.extend(f"- {item}" for item in summary.next_steps)
    return "\n".join(lines)


def _turn_summary_text(events: list[sqlite3.Row]) -> str:
    lines = [f"Turn: {events[0]['turn_index']}"]
    for event in events:
        text = event["text_content"]
        if not _is_chunk_text_event(event):
            continue
        label = event["sub_type"] or event["top_type"]
        if event["role"]:
            label = f"{label}/{event['role']}"
        if event["tool_name"]:
            label = f"{label}/{event['tool_name']}"
        lines.append(f"- Event {event['event_id']} [{label}]: {_compact(text)}")
    return "\n".join(lines)


def _evidence_text(event: sqlite3.Row) -> str:
    label = event["sub_type"] or event["top_type"]
    if event["tool_name"]:
        label = f"{label}/{event['tool_name']}"
    return "\n".join([
        f"Event: {event['event_id']}",
        f"Type: {label}",
        f"Timestamp: {event['timestamp'] or ''}",
        "",
        event["text_content"] or "",
    ])


def _turn_groups(events: list[sqlite3.Row]) -> dict[int, list[sqlite3.Row]]:
    groups: dict[int, list[sqlite3.Row]] = defaultdict(list)
    for event in events:
        if event["turn_index"] is None:
            continue
        groups[int(event["turn_index"])].append(event)
    return dict(sorted(groups.items()))


def _high_value_events(events: list[sqlite3.Row], summary_evidence_ids: list[int]) -> list[sqlite3.Row]:
    evidence_set = set(summary_evidence_ids)
    selected = []
    for event in events:
        if not _is_chunk_text_event(event):
            continue
        if event["event_id"] in evidence_set:
            selected.append(event)
            continue
        if event["sub_type"] in {"user_message", "function_call", "message"}:
            selected.append(event)
            continue
        if event["sub_type"] == "function_call_output" and _contains_problem(event["text_content"]):
            selected.append(event)
    return selected


def _item_lines(items: list[dict[str, Any]], key: str) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item.get(key)} (evidence: {item.get('evidence_event_id')})" for item in items]


def _has_text(events: list[sqlite3.Row]) -> bool:
    return any(_is_chunk_text_event(event) for event in events)


def _is_chunk_text_event(event: sqlite3.Row) -> bool:
    if not event["text_content"]:
        return False
    return event["top_type"] not in {"session_meta", "turn_context"} and event["sub_type"] not in {"session_meta", "turn_context"}


def _trim_text(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit] + "\n...[truncated]", True


def _compact(text: str, limit: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _contains_problem(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(token in lowered for token in ["error", "failed", "failure", "exception", "traceback", "失败", "错误"])


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _dedupe_session_rows(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    seen = set()
    deduped = []
    for row in rows:
        session_id = row["session_id"]
        if session_id in seen:
            continue
        seen.add(session_id)
        deduped.append(row)
    return deduped

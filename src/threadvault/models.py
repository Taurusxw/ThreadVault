from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ParseWarning(BaseModel):
    path: Path
    line_no: int | None = None
    code: str
    message: str
    raw_excerpt: str | None = None


class NormalizedEvent(BaseModel):
    session_id: str | None = None
    turn_id: str | None = None
    turn_index: int | None = None
    timestamp: str | None = None
    top_type: str
    sub_type: str | None = None
    role: str | None = None
    call_id: str | None = None
    tool_name: str | None = None
    file_path: str | None = None
    text_content: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    line_no: int | None = None


class ParsedSession(BaseModel):
    source_path: Path
    session_id: str
    parent_session_id: str | None = None
    source_kind: str = "unknown"
    cwd: str | None = None
    model_provider: str | None = None
    first_seen_at: str | None = None
    updated_at: str | None = None
    archived: bool = False
    raw_sha256: str
    flags: dict[str, Any] = Field(default_factory=dict)
    events: list[NormalizedEvent] = Field(default_factory=list)
    warnings: list[ParseWarning] = Field(default_factory=list)


class SessionRow(BaseModel):
    session_id: str
    cwd: str | None = None
    source_kind: str = "unknown"
    first_seen_at: str | None = None
    updated_at: str | None = None
    event_count: int = 0
    warning_count: int = 0
    raw_path: str


class SearchResult(BaseModel):
    event_id: int
    session_id: str
    timestamp: str | None = None
    top_type: str
    sub_type: str | None = None
    role: str | None = None
    tool_name: str | None = None
    file_path: str | None = None
    snippet: str | None = None
    rank: float | None = None


class Summary(BaseModel):
    session_id: str
    topic: str
    user_goal: str | None = None
    key_steps: list[dict[str, Any]] = Field(default_factory=list)
    key_commands: list[dict[str, Any]] = Field(default_factory=list)
    files: list[dict[str, Any]] = Field(default_factory=list)
    problems: list[dict[str, Any]] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    evidence_event_ids: list[int] = Field(default_factory=list)
    evidence_coverage: dict[str, Any] = Field(default_factory=dict)
    missing_evidence_warnings: list[str] = Field(default_factory=list)

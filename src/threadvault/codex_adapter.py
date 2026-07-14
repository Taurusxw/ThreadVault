from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import NormalizedEvent, ParsedSession, ParseWarning

CURRENT_TYPES = {
    "session_meta",
    "turn_context",
    "response_item",
    "event_msg",
    "compacted",
    "world_state",
    "inter_agent_communication_metadata",
}


@dataclass
class AdapterStats:
    total_records: int = 0
    events: int = 0
    warnings: int = 0
    classifications: Counter[str] = field(default_factory=Counter)
    warning_codes: Counter[str] = field(default_factory=Counter)


class CodexJsonlAdapter:
    def sha256_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def iter_jsonl_records(self, path: Path) -> Iterator[tuple[int, dict[str, Any] | None, ParseWarning | None]]:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    value = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    yield line_no, None, ParseWarning(
                        path=path,
                        line_no=line_no,
                        code="invalid_json",
                        message=str(exc),
                        raw_excerpt=stripped[:1000],
                    )
                    continue
                if not isinstance(value, dict):
                    yield line_no, None, ParseWarning(
                        path=path,
                        line_no=line_no,
                        code="non_object_record",
                        message="JSONL record is not an object.",
                        raw_excerpt=stripped[:1000],
                    )
                    continue
                yield line_no, value, None

    def classify_record(self, record: dict[str, Any]) -> str:
        if isinstance(record.get("payload"), dict) and isinstance(record.get("type"), str):
            return "current" if record["type"] in CURRENT_TYPES else "unknown"
        if record.get("record_type") == "state":
            return "legacy"
        if "id" in record and "timestamp" in record and "type" not in record:
            return "state_header"
        if isinstance(record.get("type"), str):
            return "legacy"
        return "unknown"

    def parse_session_file(self, path: Path, archived: bool = False) -> ParsedSession:
        parsed = self.scan_session_file(path, archived=archived)
        events: list[NormalizedEvent] = []
        warnings = list(parsed.warnings)
        for event, warning in self.iter_normalized_events(path, fallback_session_id=parsed.session_id):
            if warning:
                warnings.append(warning)
            elif event:
                events.append(event)
        parsed.events = events
        parsed.warnings = warnings
        return parsed

    def scan_session_file(self, path: Path, archived: bool = False) -> ParsedSession:
        warnings: list[ParseWarning] = []
        session_id: str | None = None
        parent_session_id: str | None = None
        cwd: str | None = None
        source_kind = "unknown"
        model_provider: str | None = None
        first_seen_at: str | None = None
        updated_at: str | None = None
        flags: dict[str, Any] = {
            "legacy": False,
            "unknown_records": 0,
            "invalid_json": 0,
            "streamed": True,
            "classifications": {},
        }
        classifications: Counter[str] = Counter()

        for line_no, record, warning in self.iter_jsonl_records(path):
            if warning:
                flags["invalid_json"] += 1
                classifications["invalid_json"] += 1
                continue
            assert record is not None
            classification = self.classify_record(record)
            classifications[classification] += 1
            event, event_warnings = self.normalize_record(record, path, line_no, session_id)
            flags["unknown_records"] += sum(1 for item in event_warnings if item.code.startswith("unknown"))
            if event.top_type == "legacy":
                flags["legacy"] = True
            if event.session_id and not session_id:
                session_id = event.session_id
            if event.top_type == "session_meta":
                payload = event.payload
                if not cwd:
                    cwd = _string_or_none(payload.get("cwd"))
                if not parent_session_id:
                    parent_session_id = _string_or_none(payload.get("forked_from_id") or payload.get("parent_session_id"))
                if not model_provider:
                    model_provider = _string_or_none(payload.get("model_provider"))
                if source_kind == "unknown":
                    source_kind = _string_or_none(payload.get("source") or payload.get("originator")) or "unknown"
            if event.timestamp:
                first_seen_at = first_seen_at or event.timestamp
                updated_at = event.timestamp

        if not session_id:
            session_id = path.stem
            flags["missing_session_meta"] = True
            warnings.append(ParseWarning(
                path=path,
                line_no=None,
                code="missing_session_id",
                message="No session id was found; using file stem.",
            ))
        flags["classifications"] = dict(classifications)

        return ParsedSession(
            source_path=path,
            session_id=session_id,
            parent_session_id=parent_session_id,
            source_kind=source_kind,
            cwd=cwd,
            model_provider=model_provider,
            first_seen_at=first_seen_at,
            updated_at=updated_at,
            archived=archived,
            raw_sha256=self.sha256_file(path),
            flags=flags,
            events=[],
            warnings=warnings,
        )

    def iter_normalized_events(
        self,
        path: Path,
        fallback_session_id: str | None = None,
    ) -> Iterator[tuple[NormalizedEvent | None, ParseWarning | None]]:
        session_id = fallback_session_id
        calls: dict[str, int] = {}
        outputs: dict[str, int] = {}
        for line_no, record, warning in self.iter_jsonl_records(path):
            if warning:
                yield None, warning
                continue
            assert record is not None
            event, event_warnings = self.normalize_record(record, path, line_no, session_id)
            if event.session_id and not session_id:
                session_id = event.session_id
            if not event.session_id and session_id:
                event.session_id = session_id
            if event.sub_type == "function_call" and event.call_id:
                calls[event.call_id] = line_no
            if event.sub_type == "function_call_output" and event.call_id:
                outputs[event.call_id] = outputs.get(event.call_id, 0) + 1
                if event.call_id not in calls:
                    event_warnings.append(ParseWarning(
                        path=path,
                        line_no=line_no,
                        code="orphan_function_call_output",
                        message=f"function_call_output without previous function_call: {event.call_id}",
                    ))
                elif outputs[event.call_id] > 1:
                    event_warnings.append(ParseWarning(
                        path=path,
                        line_no=line_no,
                        code="duplicate_function_call_output",
                        message=f"Multiple function_call_output records for call_id: {event.call_id}",
                    ))
            for item in event_warnings:
                yield None, item
            yield event, None
        for call_id, line_no in calls.items():
            if call_id not in outputs:
                yield None, ParseWarning(
                    path=path,
                    line_no=line_no,
                    code="missing_function_call_output",
                    message=f"function_call has no matching function_call_output: {call_id}",
                )

    def normalize_record(
        self,
        record: dict[str, Any],
        path: Path,
        line_no: int,
        fallback_session_id: str | None = None,
    ) -> tuple[NormalizedEvent, list[ParseWarning]]:
        warnings: list[ParseWarning] = []
        timestamp = _string_or_none(record.get("timestamp"))

        if isinstance(record.get("payload"), dict) and isinstance(record.get("type"), str):
            top_type = record["type"]
            payload = record["payload"]
            sub_type = _string_or_none(payload.get("type"))
            event = NormalizedEvent(
                session_id=fallback_session_id,
                timestamp=timestamp or _string_or_none(payload.get("timestamp")),
                top_type=top_type,
                sub_type=sub_type,
                role=_string_or_none(payload.get("role")) or ("assistant" if top_type == "compacted" else None),
                call_id=_string_or_none(payload.get("call_id")),
                tool_name=_string_or_none(payload.get("name") or payload.get("tool_name")),
                file_path=_extract_file_path(payload),
                text_content=_extract_current_text(top_type, payload),
                payload=payload,
                line_no=line_no,
            )
            if top_type == "session_meta":
                # Collaborative rollouts use `id` for this transcript and may use
                # `session_id` for the parent thread. Archive by the transcript id.
                event.session_id = _string_or_none(payload.get("id") or payload.get("session_id")) or fallback_session_id
            if top_type not in CURRENT_TYPES:
                event.top_type = "unknown"
                warnings.append(ParseWarning(
                    path=path,
                    line_no=line_no,
                    code="unknown_current_type",
                    message=f"Unknown current rollout type: {top_type}",
                    raw_excerpt=json.dumps(record, ensure_ascii=False)[:1000],
                ))
            return event, warnings

        if record.get("record_type") == "state":
            return NormalizedEvent(
                session_id=fallback_session_id,
                timestamp=timestamp,
                top_type="legacy",
                sub_type="state",
                payload=record,
                line_no=line_no,
            ), warnings

        if "id" in record and "timestamp" in record and "type" not in record:
            return NormalizedEvent(
                session_id=_string_or_none(record.get("id")) or fallback_session_id,
                timestamp=timestamp,
                top_type="legacy",
                sub_type="session_header",
                payload=record,
                line_no=line_no,
            ), warnings

        if isinstance(record.get("type"), str):
            sub_type = _string_or_none(record.get("type"))
            return NormalizedEvent(
                session_id=_string_or_none(record.get("session_id") or record.get("id")) or fallback_session_id,
                timestamp=timestamp,
                top_type="legacy",
                sub_type=sub_type,
                role=_string_or_none(record.get("role")),
                call_id=_string_or_none(record.get("call_id")),
                tool_name=_string_or_none(record.get("name") or record.get("tool_name")),
                file_path=_extract_file_path(record),
                text_content=_extract_legacy_text(record),
                payload=record,
                line_no=line_no,
            ), warnings

        warnings.append(ParseWarning(
            path=path,
            line_no=line_no,
            code="unknown_record",
            message="Record did not match current or legacy Codex JSONL shapes.",
            raw_excerpt=json.dumps(record, ensure_ascii=False)[:1000],
        ))
        return NormalizedEvent(
            session_id=fallback_session_id,
            timestamp=timestamp,
            top_type="unknown",
            payload=record,
            line_no=line_no,
        ), warnings

    def pairing_warnings(self, path: Path, events: list[NormalizedEvent]) -> list[ParseWarning]:
        calls = {event.call_id: event.line_no for event in events if event.sub_type == "function_call" and event.call_id}
        outputs: Counter[str] = Counter(event.call_id for event in events if event.sub_type == "function_call_output" and event.call_id)
        warnings: list[ParseWarning] = []
        for call_id, line_no in calls.items():
            if outputs[call_id] == 0:
                warnings.append(
                    ParseWarning(
                        path=path,
                        line_no=line_no,
                        code="missing_function_call_output",
                        message=f"function_call has no matching function_call_output: {call_id}",
                    )
                )
        for call_id, count in outputs.items():
            if call_id not in calls:
                warnings.append(
                    ParseWarning(
                        path=path,
                        line_no=None,
                        code="orphan_function_call_output",
                        message=f"function_call_output without previous function_call: {call_id}",
                    )
                )
            elif count > 1:
                warnings.append(
                    ParseWarning(
                        path=path,
                        line_no=None,
                        code="duplicate_function_call_output",
                        message=f"Multiple function_call_output records for call_id: {call_id}",
                    )
                )
        return warnings

    def sample_file(self, path: Path, archived: bool = False) -> dict[str, Any]:
        parsed = self.scan_session_file(path, archived=archived)
        stats = AdapterStats()
        for event, warning in self.iter_normalized_events(path, fallback_session_id=parsed.session_id):
            stats.total_records += 1
            if event:
                stats.events += 1
                classification = "legacy" if event.top_type == "legacy" else ("unknown" if event.top_type == "unknown" else "current")
                stats.classifications[classification] += 1
            if warning:
                stats.warnings += 1
                stats.warning_codes[warning.code] += 1
        return {
            "path": str(path),
            "session_id": parsed.session_id,
            "events": stats.events,
            "warnings": stats.warnings,
            "classifications": dict(stats.classifications),
            "warning_codes": dict(stats.warning_codes),
        }


def _extract_current_text(top_type: str, payload: dict[str, Any]) -> str | None:
    if top_type == "compacted":
        return _first_text(payload, ["message"])
    if top_type == "event_msg":
        return _first_text(payload, ["message", "text", "delta"])
    if top_type == "turn_context":
        return _compact_json(payload)
    if top_type != "response_item":
        return None

    sub_type = payload.get("type")
    if sub_type == "message":
        return _content_parts_text(payload.get("content")) or _first_text(payload, ["text"])
    if sub_type == "reasoning":
        return _summary_text(payload.get("summary")) or _content_parts_text(payload.get("content"))
    if sub_type == "function_call":
        name = _string_or_none(payload.get("name"))
        args = _string_or_none(payload.get("arguments"))
        if name and args:
            return f"{name} {args}"
        return name or args
    if sub_type == "function_call_output":
        return _first_text(payload, ["output", "text"])
    return _content_parts_text(payload.get("content")) or _first_text(payload, ["text", "output", "arguments"])


def extract_current_text(top_type: str, payload: dict[str, Any]) -> str | None:
    """Re-extract searchable/display text when hydrating cold event payloads."""
    return _extract_current_text(top_type, payload)


def _extract_legacy_text(record: dict[str, Any]) -> str | None:
    if record.get("type") == "message":
        return _content_parts_text(record.get("content")) or _first_text(record, ["text", "message"])
    if record.get("type") == "function_call":
        name = _string_or_none(record.get("name"))
        args = _string_or_none(record.get("arguments"))
        if name and args:
            return f"{name} {args}"
        return name or args
    return _first_text(record, ["text", "message", "output", "arguments"])


def _content_parts_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        text = _string_or_none(value.get("text") or value.get("content") or value.get("message"))
        if text:
            return text
        return _compact_json(value)
    if not isinstance(value, list):
        return None
    parts: list[str] = []
    for part in value:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, dict):
            text = _string_or_none(part.get("text") or part.get("content") or part.get("message"))
            if text:
                parts.append(text)
    return "\n".join(parts) or None


def _summary_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return None
    parts = [_string_or_none(item.get("text") or item.get("summary")) for item in value if isinstance(item, dict)]
    return "\n".join(part for part in parts if part) or None


def _extract_file_path(payload: dict[str, Any]) -> str | None:
    for key in ("file_path", "path", "cwd"):
        value = _string_or_none(payload.get(key))
        if value:
            return value
    return None


def _first_text(payload: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = _string_or_none(payload.get(key))
        if value:
            return value
    return None


def _compact_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)

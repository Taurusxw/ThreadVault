from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from .cold_store import ColdBlobRecord, ColdBlobStore

TOOL_HEAD_CHARS = 1200
TOOL_TAIL_CHARS = 800
LARGE_PAYLOAD_BYTES = 16 * 1024

NOISE_TYPES = {
    ("event_msg", "token_count"),
    ("event_msg", "task_started"),
    ("event_msg", "task_complete"),
    ("event_msg", "web_search_end"),
    ("event_msg", "thread_goal_updated"),
    ("event_msg", "item_completed"),
    ("event_msg", "turn_aborted"),
    ("event_msg", "thread_rolled_back"),
    ("event_msg", "sub_agent_activity"),
    ("event_msg", "agent_reasoning"),
    ("response_item", "reasoning"),
    ("inter_agent_communication_metadata", None),
}

EVIDENCE_TYPES = {
    ("response_item", "function_call_output"),
    ("response_item", "custom_tool_call_output"),
    ("event_msg", "patch_apply_end"),
    ("event_msg", "mcp_tool_call_end"),
    ("event_msg", "image_generation_end"),
}

METADATA_TYPES = {"session_meta", "world_state", "turn_context"}
KNOWN_TOP_TYPES = {
    "compacted",
    "event_msg",
    "inter_agent_communication_metadata",
    "legacy",
    "response_item",
    "session_meta",
    "turn_context",
    "world_state",
}


@dataclass
class PreparedEventContent:
    text_content: str | None
    payload_json: str
    payload_ref: str | None
    payload_original_bytes: int
    text_original_chars: int
    storage_class: str
    content_flags_json: str
    blob_records: list[ColdBlobRecord] = field(default_factory=list)


def prepare_event_content(event: Any, blob_store: ColdBlobStore) -> PreparedEventContent:
    top_type = _value(event, "top_type")
    sub_type = _value(event, "sub_type")
    payload = _payload(event)
    text = _value(event, "text_content")
    original_json = _json(payload)
    original_bytes = original_json.encode("utf-8")
    original_text_chars = len(text or "")
    flags: list[str] = []
    records: list[ColdBlobRecord] = []
    payload_ref: str | None = None
    storage_class = "core"
    hot_payload: dict[str, Any]
    hot_text = text

    if (top_type, sub_type) in NOISE_TYPES:
        storage_class = "noise"
        hot_text = None
        hot_payload = _dropped_stub(original_bytes, reason="low_value_telemetry")
        flags.extend(["payload_dropped", "text_dropped"])
    elif top_type == "compacted":
        storage_class = "core"
        record = blob_store.put(original_bytes, kind="compacted_history")
        records.append(record)
        payload_ref = record.blob_id
        replacement = payload.get("replacement_history")
        hot_payload = {
            key: value
            for key, value in payload.items()
            if key not in {"replacement_history", "message"}
        }
        hot_payload["message_chars"] = len(str(payload.get("message") or ""))
        hot_payload["message_sha256"] = _text_sha(str(payload.get("message") or ""))
        hot_payload["replacement_history_count"] = len(replacement) if isinstance(replacement, list) else 0
        hot_payload["threadvault_cold_ref"] = record.blob_id
        flags.extend(["payload_cold", "replacement_history_externalized", "payload_slimmed"])
    elif top_type == "response_item" and sub_type == "message":
        hot_payload, image_records = _compact_message_payload(payload, blob_store)
        records.extend(image_records)
        if image_records:
            flags.append("images_externalized")
        flags.append("payload_slimmed")
    elif (top_type, sub_type) in EVIDENCE_TYPES:
        storage_class = "evidence"
        record = blob_store.put(original_bytes, kind=f"{top_type}:{sub_type}")
        records.append(record)
        payload_ref = record.blob_id
        hot_payload = _payload_stub(payload, record, original_bytes)
        if hot_text and len(hot_text) > TOOL_HEAD_CHARS + TOOL_TAIL_CHARS:
            hot_text = _head_tail(hot_text)
            flags.append("text_truncated")
        flags.extend(["payload_cold", "payload_slimmed"])
    elif top_type == "response_item" and sub_type in {"function_call", "custom_tool_call"}:
        hot_payload = _call_stub(payload)
        flags.append("payload_slimmed")
    elif top_type in METADATA_TYPES:
        storage_class = "evidence"
        record = blob_store.put(original_bytes, kind=top_type)
        records.append(record)
        payload_ref = record.blob_id
        hot_payload = _payload_stub(payload, record, original_bytes)
        flags.extend(["payload_cold", "payload_slimmed"])
    elif top_type not in KNOWN_TOP_TYPES or top_type == "unknown":
        storage_class = "quarantine"
        record = blob_store.put(original_bytes, kind="unknown_event")
        records.append(record)
        payload_ref = record.blob_id
        hot_payload = _payload_stub(payload, record, original_bytes)
        flags.extend(["payload_cold", "quarantined"])
    elif len(original_bytes) > LARGE_PAYLOAD_BYTES:
        storage_class = "evidence"
        record = blob_store.put(original_bytes, kind=f"{top_type}:{sub_type or 'none'}")
        records.append(record)
        payload_ref = record.blob_id
        hot_payload = _payload_stub(payload, record, original_bytes)
        flags.extend(["payload_cold", "payload_slimmed"])
    else:
        hot_payload = payload

    return PreparedEventContent(
        text_content=hot_text,
        payload_json=_json(hot_payload),
        payload_ref=payload_ref,
        payload_original_bytes=len(original_bytes),
        text_original_chars=original_text_chars,
        storage_class=storage_class,
        content_flags_json=_json({"flags": sorted(set(flags))}),
        blob_records=records,
    )


def _compact_message_payload(payload: dict[str, Any], blob_store: ColdBlobStore) -> tuple[dict[str, Any], list[ColdBlobRecord]]:
    records: list[ColdBlobRecord] = []
    compact_content: list[dict[str, Any]] = []
    content = payload.get("content")
    if isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                compact_content.append({"type": type(part).__name__})
                continue
            kind = str(part.get("type") or "unknown")
            if kind == "input_image" and isinstance(part.get("image_url"), str):
                asset = _decode_data_url(part["image_url"])
                if asset is not None:
                    media_type, data = asset
                    record = blob_store.put(data, kind=f"asset:{media_type}", compress=False)
                    records.append(record)
                    compact_content.append({
                        "type": kind,
                        "asset_ref": record.blob_id,
                        "media_type": media_type,
                        "bytes": len(data),
                        "detail": part.get("detail"),
                    })
                    continue
            text = part.get("text")
            if isinstance(text, str):
                compact_content.append({"type": kind, "chars": len(text), "sha256": _text_sha(text)})
            else:
                compact_content.append(_small_scalars(part))
    hot = _small_scalars(payload)
    if compact_content:
        hot["content"] = compact_content
    return hot, records


def _payload_stub(payload: dict[str, Any], record: ColdBlobRecord, original_bytes: bytes) -> dict[str, Any]:
    stub = _small_scalars(payload)
    stub.update({
        "threadvault_cold_ref": record.blob_id,
        "original_bytes": len(original_bytes),
        "original_sha256": record.sha256,
    })
    return stub


def _call_stub(payload: dict[str, Any]) -> dict[str, Any]:
    stub = _small_scalars(payload, allowed_long={"name", "call_id", "status"})
    for key in ("arguments", "input"):
        value = payload.get(key)
        if isinstance(value, str):
            stub[f"{key}_chars"] = len(value)
            stub[f"{key}_sha256"] = _text_sha(value)
    return stub


def _small_scalars(payload: dict[str, Any], allowed_long: set[str] | None = None) -> dict[str, Any]:
    allowed_long = allowed_long or set()
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None or isinstance(value, (bool, int, float)):
            result[key] = value
        elif isinstance(value, str) and (len(value) <= 256 or key in allowed_long):
            result[key] = value
    return result


def _dropped_stub(original_bytes: bytes, *, reason: str) -> dict[str, Any]:
    return {
        "threadvault_storage": "dropped",
        "reason": reason,
        "original_bytes": len(original_bytes),
        "original_sha256": hashlib.sha256(original_bytes).hexdigest(),
    }


def _decode_data_url(value: str) -> tuple[str, bytes] | None:
    if not value.startswith("data:") or ";base64," not in value:
        return None
    header, encoded = value.split(",", 1)
    media_type = header[5:].split(";", 1)[0] or "application/octet-stream"
    try:
        return media_type, base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        return None


def _head_tail(text: str) -> str:
    omitted = max(0, len(text) - TOOL_HEAD_CHARS - TOOL_TAIL_CHARS)
    return f"{text[:TOOL_HEAD_CHARS]}\n[... {omitted} chars stored in cold evidence ...]\n{text[-TOOL_TAIL_CHARS:]}"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _payload(event: Any) -> dict[str, Any]:
    value = _value(event, "payload")
    if isinstance(value, dict):
        return value
    payload_json = _value(event, "payload_json")
    if isinstance(payload_json, str):
        parsed = json.loads(payload_json)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    return {}


def _value(event: Any, name: str) -> Any:
    if isinstance(event, dict):
        return event.get(name)
    try:
        return event[name]
    except (KeyError, IndexError, TypeError):
        return getattr(event, name, None)

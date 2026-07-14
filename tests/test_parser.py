from __future__ import annotations

import json
from pathlib import Path

from threadvault.parser import parse_session_file

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def test_parse_current_rollout_with_warnings() -> None:
    parsed = parse_session_file(FIXTURES / "sessions" / "current.jsonl")

    assert parsed.session_id == "sess-current"
    assert parsed.cwd == "E:\\Codex\\ThreadVault"
    assert len(parsed.events) == 8
    assert {warning.code for warning in parsed.warnings} >= {"unknown_current_type", "invalid_json"}
    assert any(event.text_content and "pytest" in event.text_content for event in parsed.events)
    assert any(event.sub_type == "function_call_output" for event in parsed.events)
    assert any(event.top_type == "unknown" and event.payload.get("text") == "unknown shape" for event in parsed.events)


def test_parse_compacted_rollout_as_supported_summary(tmp_path: Path) -> None:
    rollout = tmp_path / "compacted.jsonl"
    records = [
        {
            "timestamp": "2026-07-13T01:00:00Z",
            "type": "session_meta",
            "payload": {"id": "sess-compacted", "cwd": "E:\\Codex\\ThreadVault"},
        },
        {
            "timestamp": "2026-07-13T01:01:00Z",
            "type": "compacted",
            "payload": {
                "message": "Continue from the verified parser checkpoint.",
                "replacement_history": [{"type": "message", "role": "user", "content": []}],
                "window_number": 2,
                "first_window_id": "00000000-0000-0000-0000-000000000001",
                "previous_window_id": "00000000-0000-0000-0000-000000000001",
                "window_id": "00000000-0000-0000-0000-000000000002",
            },
        },
    ]
    rollout.write_text("".join(f"{json.dumps(record)}\n" for record in records), encoding="utf-8")

    parsed = parse_session_file(rollout)

    compacted = next(event for event in parsed.events if event.top_type == "compacted")
    assert parsed.warnings == []
    assert parsed.flags["unknown_records"] == 0
    assert parsed.flags["classifications"] == {"current": 2}
    assert compacted.sub_type is None
    assert compacted.role == "assistant"
    assert compacted.text_content == "Continue from the verified parser checkpoint."
    assert compacted.payload["replacement_history"][0]["role"] == "user"


def test_parse_current_world_and_inter_agent_metadata_without_index_text(tmp_path: Path) -> None:
    rollout = tmp_path / "current-metadata.jsonl"
    records = [
        {
            "timestamp": "2026-07-13T02:00:00Z",
            "type": "session_meta",
            "payload": {"id": "sess-current-metadata", "cwd": "E:\\Codex\\ThreadVault"},
        },
        {
            "timestamp": "2026-07-13T02:00:01Z",
            "type": "world_state",
            "payload": {"full": True, "state": {"agents": []}},
        },
        {
            "timestamp": "2026-07-13T02:00:02Z",
            "type": "inter_agent_communication_metadata",
            "payload": {"trigger_turn": True},
        },
    ]
    rollout.write_text("".join(f"{json.dumps(record)}\n" for record in records), encoding="utf-8")

    parsed = parse_session_file(rollout)

    assert parsed.warnings == []
    assert parsed.flags["unknown_records"] == 0
    assert parsed.flags["classifications"] == {"current": 3}
    assert [event.top_type for event in parsed.events] == [
        "session_meta",
        "world_state",
        "inter_agent_communication_metadata",
    ]
    assert parsed.events[1].text_content is None
    assert parsed.events[2].text_content is None


def test_collaborative_session_meta_prefers_transcript_id_over_parent_session_id(tmp_path: Path) -> None:
    rollout = tmp_path / "child.jsonl"
    rollout.write_text(
        json.dumps(
            {
                "timestamp": "2026-07-13T03:00:00Z",
                "type": "session_meta",
                "payload": {
                    "id": "child-session",
                    "session_id": "parent-session",
                    "forked_from_id": "parent-session",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    parsed = parse_session_file(rollout)

    assert parsed.session_id == "child-session"
    assert parsed.parent_session_id == "parent-session"
    assert parsed.events[0].session_id == "child-session"


def test_parse_legacy_rollout() -> None:
    parsed = parse_session_file(FIXTURES / "archived_sessions" / "legacy.jsonl", archived=True)

    assert parsed.session_id == "sess-legacy"
    assert parsed.archived is True
    assert parsed.flags["legacy"] is True
    assert any(event.top_type == "legacy" and event.sub_type == "function_call" for event in parsed.events)

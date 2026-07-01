from __future__ import annotations

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


def test_parse_legacy_rollout() -> None:
    parsed = parse_session_file(FIXTURES / "archived_sessions" / "legacy.jsonl", archived=True)

    assert parsed.session_id == "sess-legacy"
    assert parsed.archived is True
    assert parsed.flags["legacy"] is True
    assert any(event.top_type == "legacy" and event.sub_type == "function_call" for event in parsed.events)

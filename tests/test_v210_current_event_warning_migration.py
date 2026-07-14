from __future__ import annotations

import json
from pathlib import Path

from threadvault.database import SCHEMA_VERSION, connect, init_db
from threadvault.importer import import_codex_file


def test_v7_migrates_current_metadata_warnings_and_retires_duplicate_meta(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    with connect(db) as conn:
        init_db(conn)
        conn.execute(
            """
            INSERT INTO sessions (
              session_id, source_kind, archived, raw_path, raw_sha256, parse_version, flags_json
            ) VALUES ('session', 'test', 0, 'rollout.jsonl', 'hash', 6, '{}')
            """
        )
        for line_no, event_type, payload in [
            (2, "world_state", {"full": True, "state": {}}),
            (3, "inter_agent_communication_metadata", {"trigger_turn": True}),
        ]:
            conn.execute(
                """
                INSERT INTO events (
                  session_id, top_type, text_content, indexed_text, index_policy,
                  value_level, payload_json, line_no
                ) VALUES ('session', 'unknown', NULL, NULL, 'skip_empty', 'noise', ?, ?)
                """,
                (json.dumps(payload), line_no),
            )
            conn.execute(
                """
                INSERT INTO parse_warnings(session_id, raw_path, line_no, code, message)
                VALUES ('session', 'rollout.jsonl', ?, 'unknown_current_type', ?)
                """,
                (line_no, f"Unknown current rollout type: {event_type}"),
            )
        conn.execute(
            """
            INSERT INTO parse_warnings(session_id, raw_path, line_no, code, message)
            VALUES ('session', 'rollout.jsonl', 1, 'duplicate_session_meta', 'obsolete')
            """
        )
        conn.execute("UPDATE meta SET value = '6' WHERE key = 'schema_version'")
        conn.commit()

        init_db(conn)

        schema_version = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
        events = conn.execute(
            "SELECT top_type, indexed_text, index_policy, value_level FROM events ORDER BY line_no"
        ).fetchall()
        warnings = conn.execute("SELECT code FROM parse_warnings").fetchall()

    assert int(schema_version) == SCHEMA_VERSION == 8
    assert [event["top_type"] for event in events] == [
        "world_state",
        "inter_agent_communication_metadata",
    ]
    assert all(event["indexed_text"] is None for event in events)
    assert all(event["index_policy"] == "skip_empty" for event in events)
    assert all(event["value_level"] == "noise" for event in events)
    assert warnings == []


def test_import_reprocesses_unchanged_file_after_parser_version_advances(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text(
        json.dumps(
            {
                "timestamp": "2026-07-13T04:00:00Z",
                "type": "session_meta",
                "payload": {"id": "session"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    db = tmp_path / "threadvault.db"
    with connect(db) as conn:
        init_db(conn)
        first = import_codex_file(conn, rollout)
        second = import_codex_file(conn, rollout)
        conn.execute("UPDATE sessions SET parse_version = ?", (SCHEMA_VERSION - 1,))
        conn.commit()
        third = import_codex_file(conn, rollout)

    assert first.imported == 1
    assert second.skipped == 1
    assert third.imported == 1

from __future__ import annotations

import json
from pathlib import Path

from threadvault.database import SCHEMA_VERSION, connect, init_db


def test_v6_migrates_supported_compacted_events_and_stale_warnings(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-compacted.db"
    with connect(db_path) as conn:
        init_db(conn)
        conn.execute(
            """
            INSERT INTO sessions (
              session_id, source_kind, raw_path, raw_sha256, parse_version, flags_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("sess-compacted", "current", "missing.jsonl", "sha", 1, "{}"),
        )
        payload = {"message": "Recovered compacted checkpoint.", "window_number": 2}
        cursor = conn.execute(
            """
            INSERT INTO events (
              session_id, top_type, payload_json, line_no, index_policy, value_level
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("sess-compacted", "unknown", json.dumps(payload), 12, "skip_empty", "noise"),
        )
        conn.execute(
            """
            INSERT INTO parse_warnings (session_id, raw_path, line_no, code, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "sess-compacted",
                "missing.jsonl",
                12,
                "unknown_current_type",
                "Unknown current rollout type: compacted",
            ),
        )
        conn.execute("UPDATE meta SET value = '5' WHERE key = 'schema_version'")
        conn.commit()

        init_db(conn)

        event = conn.execute(
            """
            SELECT top_type, role, text_content, indexed_text, index_policy, value_level
            FROM events WHERE event_id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        warning_count = conn.execute("SELECT COUNT(*) FROM parse_warnings").fetchone()[0]
        schema_version = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]

    assert dict(event) == {
        "top_type": "compacted",
        "role": "assistant",
        "text_content": "Recovered compacted checkpoint.",
        "indexed_text": "Recovered compacted checkpoint.",
        "index_policy": "full",
        "value_level": "core",
    }
    assert warning_count == 0
    assert int(schema_version) == SCHEMA_VERSION

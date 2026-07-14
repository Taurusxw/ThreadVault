from __future__ import annotations

import base64
import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.archive_lifecycle import conversation_digest
from threadvault.cli import app
from threadvault.cold_store import ColdBlobStore
from threadvault.database import connect_readonly
from threadvault.storage_policy import prepare_event_content

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def _import_fixture(db: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["failed"] == 0


def test_cold_store_is_content_addressed_and_verifiable(tmp_path: Path) -> None:
    store = ColdBlobStore(tmp_path / "cold")
    first = store.put(b"same evidence" * 100, kind="test")
    second = store.put(b"same evidence" * 100, kind="test-again")

    assert first.blob_id == second.blob_id
    assert store.read(first.relative_path, first.codec) == b"same evidence" * 100
    assert store.verify(first)["ok"] is True
    assert len(list((tmp_path / "cold").rglob("*.zlib"))) == 1


def test_storage_policy_externalizes_compaction_and_message_images(tmp_path: Path) -> None:
    store = ColdBlobStore(tmp_path / "cold")
    compacted = prepare_event_content(
        {
            "top_type": "compacted",
            "sub_type": None,
            "text_content": "current compacted summary",
            "payload": {
                "message": "current compacted summary",
                "replacement_history": [{"large": "value" * 100}],
            },
        },
        store,
    )
    compact_hot = json.loads(compacted.payload_json)
    assert compacted.payload_ref
    assert "replacement_history" not in compact_hot
    assert json.loads(store.read(compacted.blob_records[0].relative_path, "zlib"))["replacement_history"]

    raw_image = b"small-image"
    message = prepare_event_content(
        {
            "top_type": "response_item",
            "sub_type": "message",
            "role": "user",
            "text_content": "keep this message",
            "payload": {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "keep this message"},
                    {
                        "type": "input_image",
                        "image_url": "data:image/png;base64," + base64.b64encode(raw_image).decode(),
                    },
                ],
            },
        },
        store,
    )
    message_hot = json.loads(message.payload_json)
    assert message.text_content == "keep this message"
    assert "keep this message" not in message.payload_json
    assert message_hot["content"][1]["asset_ref"] == message.blob_records[0].blob_id
    assert store.read(message.blob_records[0].relative_path, "raw") == raw_image


def test_import_uses_schema_v8_and_removes_duplicate_turn_bodies(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    _import_fixture(db)

    with connect_readonly(db) as conn:
        assert conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "8"
        event_columns = {row[1] for row in conn.execute("PRAGMA table_info(events)")}
        assert {"payload_ref", "storage_class", "content_flags_json"} <= event_columns
        assert conn.execute("SELECT COUNT(*) FROM turns WHERE user_message_text IS NOT NULL").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM turns WHERE assistant_message_text IS NOT NULL").fetchone()[0] == 0
        duplicate_rows = conn.execute(
            "SELECT COUNT(*) FROM events WHERE index_policy='skip_duplicate'"
        ).fetchone()[0]
        assert duplicate_rows >= 0


def test_copy_on_write_rebuild_preserves_conversation_and_hydrates_payloads(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    cold = tmp_path / "target-cold"
    _import_fixture(source)

    result = CliRunner().invoke(
        app,
        [
            "storage", "rebuild", "--db", str(source), "--target-db", str(target),
            "--cold-root", str(cold), "--apply", "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert all(payload["validations"].values())

    with connect_readonly(source) as source_conn, connect_readonly(target) as target_conn:
        assert conversation_digest(source_conn) == conversation_digest(target_conn)
        cold_event = target_conn.execute(
            "SELECT event_id FROM events WHERE payload_ref IS NOT NULL ORDER BY event_id LIMIT 1"
        ).fetchone()
    assert cold_event is not None
    event_result = CliRunner().invoke(
        app,
        ["storage", "event", "--db", str(target), "--cold-root", str(cold), "--event-id", str(cold_event[0]), "--json"],
    )
    assert event_result.exit_code == 0, event_result.output
    assert isinstance(json.loads(event_result.output)["payload"], dict)


def test_storage_backup_profiles_and_deep_verification(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    _import_fixture(db)
    runner = CliRunner()
    for profile in ("core", "evidence", "forensic"):
        out = tmp_path / profile
        result = runner.invoke(
            app,
            [
                "storage", "backup", "--db", str(db), "--out", str(out),
                "--profile", profile, "--codex-home", str(FIXTURES), "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        manifest = Path(json.loads(result.output)["manifest"])
        verify = runner.invoke(
            app,
            ["storage", "verify-backup", "--manifest", str(manifest), "--deep", "--json"],
        )
        assert verify.exit_code == 0, verify.output
        assert json.loads(verify.output)["ok"] is True


def test_storage_audit_and_verify_cli_contract(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    _import_fixture(db)
    runner = CliRunner()
    audit = runner.invoke(app, ["storage", "audit", "--db", str(db), "--json"])
    assert audit.exit_code == 0, audit.output
    audit_payload = json.loads(audit.output)
    assert audit_payload["ok"] is True
    assert audit_payload["event_totals"]["events"] > 0

    verify = runner.invoke(app, ["storage", "verify", "--db", str(db), "--deep", "--json"])
    assert verify.exit_code == 0, verify.output
    assert json.loads(verify.output)["ok"] is True

    ColdBlobStore(tmp_path / "threadvault-cold").put(b"unreferenced", kind="orphan")
    plan = runner.invoke(app, ["storage", "prune", "--db", str(db), "--json"])
    assert json.loads(plan.output)["orphan_files"] == 1
    applied = runner.invoke(app, ["storage", "prune", "--db", str(db), "--apply", "--json"])
    assert applied.exit_code == 0, applied.output
    assert json.loads(applied.output)["deleted_files"] == 1

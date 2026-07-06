from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import classify_index_text, connect
from threadvault.retrieval import RetrievalQuery, retrieve
from threadvault.schemas import validate_payload
from threadvault.store import ArchiveStore

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_retrieval_query_fts_returns_fixture_results(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)

    with connect(db) as conn:
        results = retrieve(conn, RetrievalQuery(text="pytest", fields="full"))

    assert results
    assert all(result.event_id for result in results)
    assert any(result.rank is not None for result in results)


def test_clean_knowledge_index_skips_binary_and_low_value_noise() -> None:
    binary = classify_index_text(
        {
            "top_type": "response_item",
            "sub_type": "function_call_output",
            "tool_name": None,
            "file_path": None,
            "text_content": "data:image/png;base64,AAAA",
        }
    )
    token_count = classify_index_text(
        {
            "top_type": "event_msg",
            "sub_type": "token_count",
            "tool_name": None,
            "file_path": None,
            "text_content": '{"total": 123}',
        }
    )

    assert binary["index_policy"] == "metadata_only"
    assert "AAAA" not in (binary["indexed_text"] or "")
    assert token_count["index_policy"] == "skip_low_value"
    assert token_count["indexed_text"] is None


def test_archive_store_search_preserves_cli_json_contracts(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    for fields, schema in [
        ("minimal", "search_minimal"),
        ("standard", "search_standard"),
        ("full", "search_full"),
    ]:
        result = runner.invoke(app, ["search", "pytest", "--db", str(db), "--json", "--fields", fields])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert validate_payload(schema, payload)["ok"] is True


def test_retrieval_filters_match_existing_search_behavior(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    store = ArchiveStore(db)

    by_session = store.search("pytest", session_id="sess-current")
    assert by_session
    assert {result.session_id for result in by_session} == {"sess-current"}

    by_project = store.search("pytest", cwd="E:\\Codex\\ThreadVault")
    assert by_project
    assert any(result.session_id == "sess-current" for result in by_project)

    by_type = store.search("failed", top_type="function_call_output")
    assert by_type
    assert all(result.sub_type == "function_call_output" or result.top_type == "function_call_output" for result in by_type)

    by_tool = store.search("pytest", tool="shell")
    assert by_tool
    assert all(result.tool_name == "shell" for result in by_tool)


def test_retrieval_handles_awkward_fts_input_through_retry(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    store = ArchiveStore(db)

    results = store.search("parser.py)", fields="minimal")

    assert results


def test_retrieval_rejects_unsupported_mode(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)

    with connect(db) as conn, pytest.raises(ValueError, match="Only fts retrieval mode"):
        retrieve(conn, RetrievalQuery(text="pytest", mode="semantic"))


def test_capabilities_include_v2_retrieval_module() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["capabilities", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["feature_flags"]["retrieval_module"] is True
    assert payload["retrieval_modes"] == ["fts"]
    assert validate_payload("capabilities", payload)["ok"] is True


def test_v201_docs_exist() -> None:
    for path in [
        Path("docs/progress/archive/legacy-v2/README.md"),
        Path("docs/progress/archive/legacy-v2/phases/phase-01-retrieval-module-fts-wrapper/plan.md"),
        Path("docs/progress/archive/legacy-v2/phases/phase-01-retrieval-module-fts-wrapper/acceptance.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"

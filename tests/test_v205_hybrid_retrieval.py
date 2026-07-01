from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def enabled_vector_config(tmp_path: Path) -> Path:
    config = tmp_path / "threadvault.toml"
    config.write_text(
        "\n".join([
            "[retrieval.vector]",
            "enabled = true",
            'adapter = "local-hash"',
            "dimensions = 64",
            "",
        ]),
        encoding="utf-8",
    )
    return config


def test_hybrid_retrieval_degrades_to_fts_without_vector_config(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["retrieval", "hybrid", "pytest", "--db", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("hybrid_retrieval", payload)["ok"] is True
    assert payload["contract_version"] == "hybrid_retrieval.v1"
    assert payload["diagnostics"]["capabilities_used"] == ["fts", "hybrid"]
    assert payload["diagnostics"]["vector"]["status"] == "disabled_by_config"
    assert payload["diagnostics"]["fts"]["used"] is True
    assert payload["results"]
    assert {result["source"] for result in payload["results"]} == {"fts"}
    assert all(result["evidence_event_ids"] for result in payload["results"])
    assert all("fts" in result["explanation"]["matched_by"] for result in payload["results"])


def test_hybrid_retrieval_combines_fts_and_vector_with_explanations(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    config = enabled_vector_config(tmp_path)
    index_result = runner.invoke(
        app,
        ["vector", "index", "--session", "sess-current", "--db", str(db), "--config", str(config), "--json"],
    )
    assert index_result.exit_code == 0, index_result.output

    result = runner.invoke(
        app,
        ["retrieval", "hybrid", "parser failure", "--db", str(db), "--config", str(config), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("hybrid_retrieval", payload)["ok"] is True
    assert payload["diagnostics"]["capabilities_used"] == ["fts", "vector", "hybrid"]
    assert payload["diagnostics"]["vector"]["status"] == "used"
    sources = {item["source"] for item in payload["results"]}
    assert {"fts", "vector"} <= sources
    assert payload["results"] == sorted(payload["results"], key=lambda item: (-item["score"], item["source"], item["hybrid_id"]))
    for item in payload["results"]:
        assert item["score"] >= 0
        assert set(item["scores"]) == {"fts", "vector", "same_project", "exact_hint"}
        assert item["evidence_event_ids"]
        assert item["explanation"]["rank_factors"]
        assert item["source"] in item["explanation"]["matched_by"]
    assert any(item["source"] == "vector" and item["chunk_id"] for item in payload["results"])


def test_hybrid_retrieval_filter_and_limit_contract(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["retrieval", "hybrid", "pytest", "--db", str(db), "--session", "sess-current", "--limit", "2", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("hybrid_retrieval", payload)["ok"] is True
    assert payload["query"]["filters"]["session_id"] is True
    assert len(payload["results"]) <= 2
    assert all(result["session_id"] == "sess-current" for result in payload["results"])


def test_capabilities_robot_docs_and_schema_registry_include_hybrid_retrieval() -> None:
    caps = capabilities()
    assert "retrieval hybrid" in caps["json_outputs"]
    assert caps["feature_flags"]["hybrid_retrieval"] is True

    guide = robot_guide()
    assert guide["retrieval"]["hybrid_contract_version"] == "hybrid_retrieval.v1"
    assert guide["retrieval"]["hybrid_degrades_to_fts"] is True
    assert "hybrid_retrieval" in guide["retrieval"]["schemas"]
    assert "threadvault retrieval hybrid QUERY --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "hybrid_retrieval" in schemas
    assert get_schema("hybrid_retrieval")["type"] == "object"


def test_v205_docs_exist() -> None:
    for path in [
        Path("docs/v2/phases/phase-05-hybrid-ranking-explanations/plan.md"),
        Path("docs/v2/phases/phase-05-hybrid-ranking-explanations/design-notes.md"),
        Path("docs/v2/README.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"

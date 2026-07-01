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


def test_v2_acceptance_fts_only_retrieval_and_agent_path(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    retrieval_result = runner.invoke(app, ["retrieval", "query", "pytest", "--db", str(db), "--json"])
    assert retrieval_result.exit_code == 0, retrieval_result.output
    retrieval_payload = json.loads(retrieval_result.output)
    assert validate_payload("retrieval_query", retrieval_payload)["ok"] is True
    assert retrieval_payload["diagnostics"]["used_mode"] == "fts"
    assert retrieval_payload["results"]

    hybrid_result = runner.invoke(app, ["retrieval", "hybrid", "pytest", "--db", str(db), "--json"])
    assert hybrid_result.exit_code == 0, hybrid_result.output
    hybrid_payload = json.loads(hybrid_result.output)
    assert validate_payload("hybrid_retrieval", hybrid_payload)["ok"] is True
    assert hybrid_payload["diagnostics"]["capabilities_used"] == ["fts", "hybrid"]
    assert hybrid_payload["diagnostics"]["vector"]["status"] == "disabled_by_config"
    assert all(result["evidence_event_ids"] for result in hybrid_payload["results"])

    agent_result = runner.invoke(app, ["agent", "retrieve", "pytest", "--db", str(db), "--json"])
    assert agent_result.exit_code == 0, agent_result.output
    agent_payload = json.loads(agent_result.output)
    assert validate_payload("agent_retrieval", agent_payload)["ok"] is True
    assert agent_payload["diagnostics"]["capabilities_used"] == ["fts", "hybrid"]
    assert agent_payload["privacy"]["raw_paths_included"] is False
    assert all("metadata" not in result for result in agent_payload["results"])
    assert all(result["evidence_event_ids"] for result in agent_payload["results"])


def test_v2_acceptance_vector_enabled_hybrid_and_agent_path(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    config = enabled_vector_config(tmp_path)

    index_result = runner.invoke(
        app,
        ["vector", "index", "--session", "sess-current", "--db", str(db), "--config", str(config), "--json"],
    )
    assert index_result.exit_code == 0, index_result.output
    index_payload = json.loads(index_result.output)
    assert validate_payload("vector_index", index_payload)["ok"] is True
    assert index_payload["indexed"]["chunks"] > 0

    status_result = runner.invoke(app, ["vector", "status", "--db", str(db), "--config", str(config), "--json"])
    assert status_result.exit_code == 0, status_result.output
    status_payload = json.loads(status_result.output)
    assert validate_payload("vector_status", status_payload)["ok"] is True
    assert status_payload["config"]["enabled"] is True
    assert status_payload["index"]["matching_chunks"] > 0

    hybrid_result = runner.invoke(
        app,
        ["retrieval", "hybrid", "parser failure", "--db", str(db), "--config", str(config), "--json"],
    )
    assert hybrid_result.exit_code == 0, hybrid_result.output
    hybrid_payload = json.loads(hybrid_result.output)
    assert validate_payload("hybrid_retrieval", hybrid_payload)["ok"] is True
    assert hybrid_payload["diagnostics"]["capabilities_used"] == ["fts", "vector", "hybrid"]
    assert {"fts", "vector"} <= {result["source"] for result in hybrid_payload["results"]}

    agent_result = runner.invoke(
        app,
        ["agent", "retrieve", "parser failure", "--db", str(db), "--config", str(config), "--json"],
    )
    assert agent_result.exit_code == 0, agent_result.output
    agent_payload = json.loads(agent_result.output)
    assert validate_payload("agent_retrieval", agent_payload)["ok"] is True
    assert agent_payload["diagnostics"]["capabilities_used"] == ["fts", "vector", "hybrid"]
    assert {"fts", "vector"} <= {result["source"] for result in agent_payload["results"]}
    assert agent_payload["privacy"]["raw_paths_included"] is False


def test_v2_acceptance_discovery_contracts_and_docs() -> None:
    caps = capabilities()
    for flag in [
        "retrieval_module",
        "retrieval_diagnostics",
        "summary_evidence_chunks",
        "local_vector_adapter",
        "hybrid_retrieval",
        "agent_retrieval_interface",
    ]:
        assert caps["feature_flags"][flag] is True
    assert caps["feature_flags"]["local_vector_enabled_by_default"] is False

    guide = robot_guide()
    assert guide["retrieval"]["schemas"] == ["retrieval_query", "retrieval_diagnostics", "hybrid_retrieval"]
    assert guide["summary_pipeline"]["schemas"] == ["summary_chunks"]
    assert guide["vector"]["schemas"] == ["vector_index", "vector_query", "vector_status"]
    assert guide["agent_interface"]["schemas"] == ["agent_interface_manifest", "agent_retrieval"]

    schemas = robot_schemas()
    for schema_name in [
        "retrieval_query",
        "retrieval_diagnostics",
        "summary_chunks",
        "vector_index",
        "vector_query",
        "vector_status",
        "hybrid_retrieval",
        "agent_interface_manifest",
        "agent_retrieval",
    ]:
        assert schema_name in schemas
        assert get_schema(schema_name)["type"] == "object"
        assert (Path("docs/schemas") / f"{schema_name}.schema.json").exists()

    for path in [
        Path("docs/v2/phases/phase-01-retrieval-module-fts-wrapper/plan.md"),
        Path("docs/v2/phases/phase-01-retrieval-module-fts-wrapper/acceptance.md"),
        Path("docs/v2/phases/phase-02-retrieval-json-contracts-diagnostics/plan.md"),
        Path("docs/v2/phases/phase-02-retrieval-json-contracts-diagnostics/acceptance.md"),
        Path("docs/v2/phases/phase-03-summary-evidence-chunks/plan.md"),
        Path("docs/v2/phases/phase-03-summary-evidence-chunks/acceptance.md"),
        Path("docs/v2/phases/phase-04-local-vector-adapter/plan.md"),
        Path("docs/v2/phases/phase-04-local-vector-adapter/acceptance.md"),
        Path("docs/v2/phases/phase-05-hybrid-ranking-explanations/plan.md"),
        Path("docs/v2/phases/phase-05-hybrid-ranking-explanations/acceptance.md"),
        Path("docs/v2/phases/phase-06-agent-facing-retrieval-interface/plan.md"),
        Path("docs/v2/phases/phase-06-agent-facing-retrieval-interface/acceptance.md"),
        Path("docs/v2/phases/phase-07-v2-acceptance-smoke/plan.md"),
        Path("docs/v2/README.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

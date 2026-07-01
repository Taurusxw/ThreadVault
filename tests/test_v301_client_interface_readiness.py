from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_v3_phase_01_docs_and_navigation_exist() -> None:
    for path in [
        Path("docs/v3/README.md"),
        Path("docs/v3/phases/phase-01-client-interface-readiness-audit/plan.md"),
        Path("docs/v3/phases/phase-01-client-interface-readiness-audit/design-notes.md"),
        Path("docs/v3/phases/phase-01-client-interface-readiness-audit/acceptance.md"),
        Path("docs/roadmap/v3-clients-and-team-governance.md"),
        Path("docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"

    docs_readme = Path("docs/README.md").read_text(encoding="utf-8")
    v3_readme = Path("docs/v3/README.md").read_text(encoding="utf-8")
    phase_plan = Path("docs/v3/phases/phase-01-client-interface-readiness-audit/plan.md").read_text(encoding="utf-8")
    phase_notes = Path("docs/v3/phases/phase-01-client-interface-readiness-audit/design-notes.md").read_text(
        encoding="utf-8"
    )

    assert "v3/" in docs_readme
    assert "v3-clients-and-team-governance.md" in docs_readme
    assert "richer clients and optional team governance" in v3_readme
    assert "must not be recreated" in v3_readme
    assert "Do not rewrite FTS retrieval" in v3_readme
    assert "threadvault agent manifest" in phase_plan
    assert "threadvault.agent_interface" in phase_notes
    assert not Path("deep-research-report.md").exists()


def test_v3_readiness_discovery_surfaces_cover_client_needs() -> None:
    caps = capabilities()
    for command in ["retrieval", "summary-pipeline", "vector", "agent", "export-target"]:
        assert command in caps["commands"]
    for json_output in [
        "retrieval query",
        "retrieval hybrid",
        "summary-pipeline chunks",
        "vector status",
        "agent manifest",
        "agent retrieve",
        "export-target markdown",
    ]:
        assert json_output in caps["json_outputs"]

    flags = caps["feature_flags"]
    assert flags["local_first"] is True
    assert flags["agent_retrieval_interface"] is True
    assert flags["summary_evidence_chunks"] is True
    assert flags["hybrid_retrieval"] is True
    assert flags["local_vector_adapter"] is True
    assert flags["local_vector_enabled_by_default"] is False
    assert flags["cloud_sync"] is False
    assert flags["external_llm_summary"] is False

    guide = robot_guide()
    assert guide["agent_interface"]["module"] == "threadvault.agent_interface"
    assert guide["agent_interface"]["default_mode"] == "hybrid"
    assert guide["agent_interface"]["mcp_runtime_included"] is False
    assert guide["agent_interface"]["local_debug_opt_in"] is True
    assert guide["retrieval"]["hybrid_degrades_to_fts"] is True
    assert guide["summary_pipeline"]["embedding_generated"] is False
    assert guide["vector"]["enabled_by_default"] is False
    assert guide["vector"]["source_schema"] == "summary_chunks"


def test_v3_readiness_contracts_and_agent_manifest_are_client_safe() -> None:
    schemas = robot_schemas()
    for schema_name in [
        "agent_interface_manifest",
        "agent_retrieval",
        "hybrid_retrieval",
        "summary_chunks",
        "vector_status",
        "export_target_manifest",
    ]:
        assert schema_name in schemas
        assert get_schema(schema_name)["type"] == "object"

    runner = CliRunner()
    result = runner.invoke(app, ["agent", "manifest", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("agent_interface_manifest", payload)["ok"] is True
    assert payload["capabilities"]["mcp_runtime_included"] is False
    assert payload["capabilities"]["vector_optional"] is True
    assert payload["capabilities"]["local_vector_enabled"] is False
    assert payload["privacy"]["local_first"] is True
    assert payload["privacy"]["raw_paths_in_default_output"] is False
    assert payload["privacy"]["local_debug_opt_in"] is True
    assert payload["privacy"]["external_model_calls"] is False

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import ArchiveStore, capabilities, robot_guide, robot_schemas


def test_client_manifest_cli_contract_and_defaults() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["client", "manifest", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_interface_manifest", payload)["ok"] is True
    assert payload["contract_version"] == "client_interface.v1"
    assert payload["interface"]["module"] == "threadvault.client_interface"
    assert payload["interface"]["client_families"] == ["desktop", "ide", "web", "tui", "server"]
    assert {family["name"] for family in payload["client_families"]} == {"desktop", "ide", "web", "tui", "server"}
    server_family = next(family for family in payload["client_families"] if family["name"] == "server")
    assert server_family["opt_in"] is True
    assert server_family["server_required"] is False
    defaults = payload["defaults"]
    assert defaults["local_first"] is True
    assert defaults["server_required"] is False
    assert defaults["server_available"] is False
    assert defaults["server_opt_in"] is True
    assert defaults["cloud_sync"] is False
    assert defaults["external_model_calls"] is False
    assert defaults["raw_paths_in_default_output"] is False
    assert defaults["vector_enabled_by_default"] is False


def test_client_manifest_points_to_existing_interfaces() -> None:
    manifest = ArchiveStore(Path("unused.db")).client_manifest()

    assert "threadvault capabilities --json" in manifest["entrypoints"]["discovery"]
    assert "threadvault agent retrieve QUERY --json" in manifest["entrypoints"]["retrieval"]
    assert "threadvault retrieval hybrid QUERY --json" in manifest["entrypoints"]["retrieval"]
    assert "threadvault export-target markdown --session SESSION_ID --out OUT --json" in manifest["entrypoints"]["export"]
    assert "threadvault vector status --json" in manifest["entrypoints"]["vector"]
    assert "threadvault schemas show client_interface_manifest --json" in manifest["entrypoints"]["schemas"]
    assert manifest["schemas"]["manifest"] == "client_interface_manifest"
    assert manifest["schemas"]["agent"] == ["agent_interface_manifest", "agent_retrieval"]
    assert "hybrid_retrieval" in manifest["schemas"]["retrieval"]
    assert manifest["schemas"]["summary"] == ["summary_chunks"]
    assert manifest["schemas"]["vector"] == ["vector_index", "vector_query", "vector_status"]
    assert manifest["schemas"]["export"] == ["export_target_manifest"]
    assert manifest["integration_policy"]["reuse_existing_interfaces"] is True
    assert manifest["integration_policy"]["do_not_reparse_codex_transcripts"] is True
    assert manifest["integration_policy"]["do_not_bypass_privacy_scan_for_export"] is True
    assert manifest["integration_policy"]["prefer_agent_retrieval_for_search"] is True
    assert manifest["governance"]["contract_version"] == "governance_status.v1"
    assert manifest["governance"]["diagnostics"]["team_permissions_implemented"] is False
    assert manifest["governance"]["diagnostics"]["shared_server_implemented"] is False
    assert manifest["governance"]["defaults"]["server_required"] is False


def test_client_manifest_discovery_and_schema_registry() -> None:
    caps = capabilities()
    assert "client" in caps["commands"]
    assert "client manifest" in caps["json_outputs"]
    assert caps["feature_flags"]["client_interface_manifest"] is True

    guide = robot_guide()
    assert guide["client_interface"]["module"] == "threadvault.client_interface"
    assert guide["client_interface"]["manifest_contract_version"] == "client_interface.v1"
    assert guide["client_interface"]["schemas"] == [
        "client_interface_manifest",
        "client_overview",
        "client_tui_runtime",
        "client_session",
        "client_export_preview",
        "client_warnings",
    ]
    assert guide["client_interface"]["server_required"] is False
    assert guide["client_interface"]["server_opt_in"] is True
    assert "threadvault client manifest --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "client_interface_manifest" in schemas
    assert get_schema("client_interface_manifest")["type"] == "object"
    assert Path("docs/schemas/client_interface_manifest.schema.json").exists()


def test_v302_docs_exist_and_retired_report_policy_holds() -> None:
    for path in [
        Path("docs/v3/phases/phase-02-client-manifest-entrypoint/plan.md"),
        Path("docs/v3/phases/phase-02-client-manifest-entrypoint/design-notes.md"),
        Path("docs/v3/phases/phase-02-client-manifest-entrypoint/acceptance.md"),
        Path("docs/v3/README.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

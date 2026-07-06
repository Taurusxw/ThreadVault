from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.mcp import McpRuntimeConfig, handle_mcp_message, mcp_manifest
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def rpc(method: str, params: dict | None = None, request_id: int = 1) -> str:
    payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        payload["params"] = params
    return json.dumps(payload)


def test_mcp_manifest_contract_and_discovery() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["mcp", "manifest", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("mcp_manifest", payload)["ok"] is True
    assert payload == mcp_manifest()
    assert payload["server"]["transport"] == "stdio"
    assert payload["privacy"]["writes_files"] is False
    assert {tool["name"] for tool in payload["tools"]} == {
        "threadvault_capabilities",
        "threadvault_stats",
        "threadvault_doctor",
        "threadvault_retrieve",
        "threadvault_session",
        "threadvault_export_preview",
    }

    caps = capabilities()
    assert "mcp" in caps["commands"]
    assert "mcp manifest" in caps["json_outputs"]
    assert "mcp serve" in caps["json_outputs"]
    assert caps["feature_flags"]["mcp_stdio_server"] is True
    assert caps["feature_flags"]["mcp_read_only_tools"] is True

    guide = robot_guide()
    assert guide["mcp_interface"]["module"] == "threadvault.mcp"
    assert guide["mcp_interface"]["transport"] == "stdio"
    assert "threadvault mcp serve" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "mcp_manifest" in schemas
    assert get_schema("mcp_manifest")["type"] == "object"


def test_mcp_stdio_lifecycle_and_tool_list(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    config = McpRuntimeConfig(db_path=db)

    initialized = handle_mcp_message(rpc("initialize", request_id=1), config)

    assert initialized is not None
    assert initialized["result"]["protocolVersion"] == "2025-06-18"
    assert initialized["result"]["capabilities"]["tools"] == {}
    assert initialized["result"]["serverInfo"]["name"] == "threadvault"

    listed = handle_mcp_message(rpc("tools/list", request_id=2), config)

    assert listed is not None
    names = {tool["name"] for tool in listed["result"]["tools"]}
    assert "threadvault_retrieve" in names
    assert "threadvault_export_preview" in names


def test_mcp_retrieve_session_and_export_preview_tools_are_read_only(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    config = McpRuntimeConfig(db_path=db)
    out = tmp_path / "preview-out"

    retrieved = handle_mcp_message(
        rpc(
            "tools/call",
            {
                "name": "threadvault_retrieve",
                "arguments": {"query": "pytest", "mode": "fts", "limit": 5},
            },
            request_id=3,
        ),
        config,
    )

    assert retrieved is not None
    retrieval_payload = retrieved["result"]["structuredContent"]
    assert validate_payload("agent_retrieval", retrieval_payload)["ok"] is True
    assert retrieval_payload["diagnostics"]["used_mode"] == "fts"
    assert retrieval_payload["privacy"]["raw_paths_included"] is False
    assert retrieval_payload["results"]
    assert json.loads(retrieved["result"]["content"][0]["text"]) == retrieval_payload

    session = handle_mcp_message(
        rpc("tools/call", {"name": "threadvault_session", "arguments": {"session": "sess-current"}}, request_id=4),
        config,
    )

    assert session is not None
    session_payload = session["result"]["structuredContent"]
    assert validate_payload("client_session", session_payload)["ok"] is True
    assert session_payload["session"]["session_id"] == "sess-current"

    preview = handle_mcp_message(
        rpc(
            "tools/call",
            {
                "name": "threadvault_export_preview",
                "arguments": {"session": "sess-current", "profile": "obsidian", "out": str(out)},
            },
            request_id=5,
        ),
        config,
    )

    assert preview is not None
    preview_payload = preview["result"]["structuredContent"]
    assert validate_payload("client_export_preview", preview_payload)["ok"] is True
    assert preview_payload["request"]["profile"] == "obsidian"
    assert preview_payload["diagnostics"]["preview"] is True
    assert preview_payload["diagnostics"]["writes_files"] is False
    assert not out.exists()


def test_mcp_tool_errors_are_jsonrpc_errors(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    config = McpRuntimeConfig(db_path=db)

    response = handle_mcp_message(
        rpc("tools/call", {"name": "threadvault_session", "arguments": {"session": "missing"}}, request_id=6),
        config,
    )

    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["message"] == "Unknown session: missing"

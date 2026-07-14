from __future__ import annotations

import json
from hashlib import sha256
from io import StringIO
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.mcp import McpRuntimeConfig, handle_mcp_message, mcp_manifest, serve_mcp
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


def initialize_params() -> dict:
    return {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "threadvault-tests", "version": "1.0"},
    }


def initialized_config(db: Path) -> McpRuntimeConfig:
    config = McpRuntimeConfig(db_path=db)
    response = handle_mcp_message(rpc("initialize", initialize_params()), config)
    assert response is not None and "result" in response
    notification = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    assert handle_mcp_message(notification, config) is None
    return config


def test_mcp_manifest_contract_and_discovery() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["mcp", "manifest", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("mcp_manifest", payload)["ok"] is True
    assert payload == mcp_manifest()
    assert payload["server"]["transport"] == "stdio"
    assert payload["privacy"]["writes_files"] is False
    assert all(tool["annotations"]["readOnlyHint"] is True for tool in payload["tools"])
    assert all(tool["annotations"]["destructiveHint"] is False for tool in payload["tools"])
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

    ping_before_initialize = handle_mcp_message(rpc("ping", request_id=-1), config)
    assert ping_before_initialize is not None
    assert ping_before_initialize["error"]["code"] == -32600

    before_initialize = handle_mcp_message(rpc("tools/list", request_id=0), config)
    assert before_initialize is not None
    assert before_initialize["error"]["code"] == -32600

    missing_fields = handle_mcp_message(rpc("initialize", {}, request_id=1), config)
    assert missing_fields is not None
    assert missing_fields["error"]["code"] == -32602

    initialized = handle_mcp_message(rpc("initialize", initialize_params(), request_id=2), config)

    assert initialized is not None
    assert initialized["result"]["protocolVersion"] == "2025-06-18"
    assert initialized["result"]["capabilities"]["tools"] == {"listChanged": False}
    assert initialized["result"]["serverInfo"]["name"] == "threadvault"

    ping = handle_mcp_message(rpc("ping", request_id=-2), config)
    assert ping is not None
    assert ping["result"] == {}

    before_notification = handle_mcp_message(rpc("tools/list", request_id=3), config)
    assert before_notification is not None
    assert before_notification["error"]["code"] == -32600

    notification = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    assert handle_mcp_message(notification, config) is None

    listed = handle_mcp_message(rpc("tools/list", request_id=4), config)

    assert listed is not None
    names = {tool["name"] for tool in listed["result"]["tools"]}
    assert "threadvault_retrieve" in names
    assert "threadvault_export_preview" in names
    assert all(tool["annotations"]["readOnlyHint"] is True for tool in listed["result"]["tools"])

    reused_id = handle_mcp_message(rpc("tools/list", request_id=4), config)
    assert reused_id is not None
    assert reused_id["error"]["code"] == -32600


def test_mcp_retrieve_session_and_export_preview_tools_are_read_only(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    config = initialized_config(db)
    out = tmp_path / "preview-out"
    before_hash = sha256(db.read_bytes()).hexdigest()

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
    assert sha256(db.read_bytes()).hexdigest() == before_hash


def test_mcp_tool_errors_are_jsonrpc_errors(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    config = initialized_config(db)

    response = handle_mcp_message(
        rpc("tools/call", {"name": "threadvault_session", "arguments": {"session": "missing"}}, request_id=6),
        config,
    )

    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["message"] == "Requested session was not found."


def test_mcp_validates_jsonrpc_envelope_and_request_ids(tmp_path: Path) -> None:
    config = McpRuntimeConfig(db_path=tmp_path / "unused.db")

    wrong_version = handle_mcp_message(
        json.dumps({"jsonrpc": "1.0", "id": 1, "method": "initialize", "params": initialize_params()}),
        config,
    )
    assert wrong_version is not None
    assert wrong_version["error"]["code"] == -32600

    boolean_id = handle_mcp_message(
        json.dumps({"jsonrpc": "2.0", "id": True, "method": "initialize", "params": initialize_params()}),
        config,
    )
    assert boolean_id is not None
    assert boolean_id["error"]["code"] == -32600


def test_mcp_tool_arguments_follow_advertised_schema_strictly(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    config = initialized_config(db)

    cases = [
        {"name": "threadvault_stats", "arguments": {"unexpected": True}},
        {"name": "threadvault_retrieve", "arguments": {"query": "pytest", "limit": True}},
        {"name": "threadvault_session", "arguments": {"session": "sess-current", "local_debug": 1}},
        {
            "name": "threadvault_export_preview",
            "arguments": {"out": "preview", "session": ["sess-current", 7]},
        },
    ]
    for request_id, params in enumerate(cases, start=10):
        response = handle_mcp_message(rpc("tools/call", params, request_id=request_id), config)
        assert response is not None
        assert response["error"]["code"] == -32602


def test_mcp_doctor_redacts_paths_unless_local_debug_is_enabled(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    codex_home = tmp_path / "secret-codex-home"
    (codex_home / "sessions").mkdir(parents=True)
    (codex_home / "archived_sessions").mkdir()
    config = initialized_config(db)

    redacted = handle_mcp_message(
        rpc(
            "tools/call",
            {"name": "threadvault_doctor", "arguments": {"codex_home": str(codex_home)}},
            request_id=20,
        ),
        config,
    )
    assert redacted is not None
    redacted_payload = redacted["result"]["structuredContent"]
    assert redacted_payload["db_path"] == "<redacted:threadvault-db>"
    assert redacted_payload["codex_home"] == "<redacted:codex-home>"
    assert str(tmp_path) not in json.dumps(redacted_payload)
    assert validate_payload("doctor", redacted_payload)["ok"] is True

    debug = handle_mcp_message(
        rpc(
            "tools/call",
            {
                "name": "threadvault_doctor",
                "arguments": {"codex_home": str(codex_home), "local_debug": True},
            },
            request_id=21,
        ),
        config,
    )
    assert debug is not None
    debug_payload = debug["result"]["structuredContent"]
    assert debug_payload["codex_home"] == str(codex_home)
    assert debug_payload["db_path"] == str(db)
    assert validate_payload("doctor", debug_payload)["ok"] is True


def test_mcp_missing_database_is_not_created_and_errors_do_not_leak_paths(tmp_path: Path) -> None:
    db = tmp_path / "private" / "missing.db"
    config = initialized_config(db)

    response = handle_mcp_message(
        rpc("tools/call", {"name": "threadvault_stats", "arguments": {}}, request_id=30),
        config,
    )

    assert response is not None
    assert response["error"] == {"code": -32603, "message": "Internal error"}
    assert str(db) not in json.dumps(response)
    assert not db.exists()
    assert not db.parent.exists()


def test_mcp_stdio_transport_emits_only_newline_delimited_jsonrpc(tmp_path: Path) -> None:
    messages = [
        rpc("initialize", initialize_params(), request_id=40),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        rpc(
            "tools/call",
            {"name": "threadvault_capabilities", "arguments": {}},
            request_id=41,
        ),
    ]
    stdout = StringIO()

    serve_mcp(
        McpRuntimeConfig(db_path=tmp_path / "not-needed.db"),
        stdin=StringIO("\n".join(messages) + "\n"),
        stdout=stdout,
    )

    lines = stdout.getvalue().splitlines()
    assert len(lines) == 2
    responses = [json.loads(line) for line in lines]
    assert [response["id"] for response in responses] == [40, 41]
    assert all(response["jsonrpc"] == "2.0" for response in responses)
    assert responses[1]["result"]["structuredContent"]["name"] == "threadvault"

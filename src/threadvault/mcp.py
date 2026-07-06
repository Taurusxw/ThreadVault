from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from . import __version__
from .mcp_contracts import MCP_MANIFEST_CONTRACT_VERSION, MCP_PROTOCOL_VERSION, MCP_SERVER_NAME
from .store import ArchiveStore, capabilities

JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603


@dataclass(frozen=True)
class McpRuntimeConfig:
    db_path: Path
    config_path: Path | None = None


def mcp_manifest() -> dict[str, Any]:
    return {
        "contract_version": MCP_MANIFEST_CONTRACT_VERSION,
        "server": {
            "name": MCP_SERVER_NAME,
            "module": "threadvault.mcp",
            "transport": "stdio",
            "protocol_version": MCP_PROTOCOL_VERSION,
            "version": __version__,
        },
        "tools": [_tool_manifest(tool) for tool in mcp_tools()],
        "privacy": {
            "local_first": True,
            "cloud_sync": False,
            "external_model_calls": False,
            "raw_paths_in_default_output": False,
            "local_debug_opt_in": True,
            "writes_files": False,
        },
        "integration_guidance": {
            "codex": "Register this server as an MCP stdio server and use retrieval/session/export preview tools for local memory.",
            "zcode": "Register this server through ZCode MCP settings or import compatible MCP configuration.",
            "opencode": (
                "Register this server through OpenCode MCP configuration and keep write/export flows outside "
                "the read-only tool set."
            ),
            "obsidian": (
                "Use threadvault_export_preview to inspect planned Obsidian output, then run export-target obsidian "
                "explicitly after review."
            ),
        },
    }


def mcp_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "threadvault_capabilities",
            "description": "Return ThreadVault command, format, and feature discovery metadata.",
            "inputSchema": _object_schema({}),
        },
        {
            "name": "threadvault_stats",
            "description": "Return local archive counts and clean search-index diagnostics.",
            "inputSchema": _object_schema({}),
        },
        {
            "name": "threadvault_doctor",
            "description": "Run local archive, FTS, and Codex discovery diagnostics.",
            "inputSchema": _object_schema(
                {
                    "codex_home": {"type": "string", "description": "Optional Codex home directory to inspect."},
                }
            ),
        },
        {
            "name": "threadvault_retrieve",
            "description": "Search the local archive through the agent-facing retrieval interface.",
            "inputSchema": _object_schema(
                {
                    "query": {"type": "string", "description": "Search text."},
                    "mode": {"type": "string", "enum": ["hybrid", "fts"], "default": "hybrid"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                    "vector_limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                    "session": {"type": "string", "description": "Optional session id filter."},
                    "cwd": {"type": "string", "description": "Optional project cwd filter."},
                    "since": {"type": "string", "description": "Optional lower timestamp bound."},
                    "until": {"type": "string", "description": "Optional upper timestamp bound."},
                    "type": {"type": "string", "description": "Optional top_type or sub_type filter."},
                    "tool": {"type": "string", "description": "Optional tool-name filter."},
                    "local_debug": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include local debug metadata such as raw paths.",
                    },
                },
                required=["query"],
            ),
        },
        {
            "name": "threadvault_session",
            "description": "Return a session summary, evidence, and event previews by session id.",
            "inputSchema": _object_schema(
                {
                    "session": {"type": "string", "description": "Session id to inspect."},
                    "event_limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 20},
                    "max_chars": {"type": "integer", "minimum": 50, "maximum": 5000, "default": 500},
                    "local_debug": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include local debug metadata such as raw paths.",
                    },
                },
                required=["session"],
            ),
        },
        {
            "name": "threadvault_export_preview",
            "description": "Preview Markdown, Obsidian, or Skill export files without writing anything.",
            "inputSchema": _object_schema(
                {
                    "out": {"type": "string", "description": "Future export output directory."},
                    "profile": {"type": "string", "enum": ["markdown", "obsidian", "skill"], "default": "markdown"},
                    "session": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                        "description": "Session id or session ids to include.",
                    },
                    "project": {"type": "string", "description": "Project cwd to include."},
                    "privacy_mode": {"type": "string", "enum": ["warn", "redact", "fail"], "default": "warn"},
                    "privacy_config": {"type": "string", "description": "Optional threadvault.toml privacy config path."},
                    "skill_name": {"type": "string", "description": "Skill name for skill profile previews."},
                    "skill_description": {"type": "string", "description": "Skill description for skill profile previews."},
                },
                required=["out"],
            ),
        },
    ]


def serve_mcp(config: McpRuntimeConfig, stdin: TextIO | None = None, stdout: TextIO | None = None) -> None:
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    for line in input_stream:
        raw = line.strip()
        if not raw:
            continue
        response = handle_mcp_message(raw, config)
        if response is None:
            continue
        output_stream.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
        output_stream.flush()


def handle_mcp_message(raw: str, config: McpRuntimeConfig) -> dict[str, Any] | None:
    try:
        message = json.loads(raw)
    except json.JSONDecodeError:
        return _jsonrpc_error(None, JSONRPC_PARSE_ERROR, "Parse error")
    return handle_mcp_request(message, config)


def handle_mcp_request(message: Any, config: McpRuntimeConfig) -> dict[str, Any] | None:
    if not isinstance(message, dict):
        return _jsonrpc_error(None, JSONRPC_INVALID_REQUEST, "Invalid Request")
    request_id = message.get("id")
    method = message.get("method")
    if not isinstance(method, str):
        return _jsonrpc_error(request_id, JSONRPC_INVALID_REQUEST, "Invalid Request")
    if request_id is None:
        _handle_notification(method)
        return None
    try:
        result = _dispatch(method, message.get("params") or {}, config)
    except ValueError as exc:
        return _jsonrpc_error(request_id, JSONRPC_INVALID_PARAMS, str(exc))
    except KeyError as exc:
        return _jsonrpc_error(request_id, JSONRPC_INVALID_PARAMS, f"Unknown session: {exc.args[0]}")
    except NotImplementedError:
        return _jsonrpc_error(request_id, JSONRPC_METHOD_NOT_FOUND, f"Method not found: {method}")
    except Exception as exc:  # pragma: no cover - defensive JSON-RPC guard
        return _jsonrpc_error(request_id, JSONRPC_INTERNAL_ERROR, f"Internal error: {exc}")
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _dispatch(method: str, params: Any, config: McpRuntimeConfig) -> dict[str, Any]:
    if method == "initialize":
        return _initialize_result()
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": mcp_tools()}
    if method == "tools/call":
        if not isinstance(params, dict):
            raise ValueError("tools/call params must be an object.")
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str):
            raise ValueError("tools/call requires a string name.")
        if not isinstance(arguments, dict):
            raise ValueError("tools/call arguments must be an object.")
        return _call_tool(name, arguments, config)
    raise NotImplementedError


def _initialize_result() -> dict[str, Any]:
    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": MCP_SERVER_NAME, "version": __version__},
        "instructions": (
            "ThreadVault provides local-first, read-only archive retrieval, session inspection, "
            "export preview, diagnostics, and capability discovery tools."
        ),
    }


def _call_tool(name: str, args: dict[str, Any], config: McpRuntimeConfig) -> dict[str, Any]:
    store = ArchiveStore(config.db_path)
    if name == "threadvault_capabilities":
        payload = capabilities()
    elif name == "threadvault_stats":
        payload = store.stats()
    elif name == "threadvault_doctor":
        payload = store.doctor(codex_home=_optional_path(args.get("codex_home")))
    elif name == "threadvault_retrieve":
        payload = store.agent_retrieve(
            query=_required_str(args, "query"),
            config_path=config.config_path,
            mode=_str(args.get("mode"), "hybrid"),
            limit=_int(args.get("limit"), 20, minimum=1, maximum=100),
            vector_limit=_int(args.get("vector_limit"), 10, minimum=1, maximum=50),
            session_id=_optional_str(args.get("session")),
            cwd=_optional_str(args.get("cwd")),
            since=_optional_str(args.get("since")),
            until=_optional_str(args.get("until")),
            top_type=_optional_str(args.get("type")),
            tool=_optional_str(args.get("tool")),
            local_debug=_bool(args.get("local_debug"), False),
        )
    elif name == "threadvault_session":
        payload = store.client_session(
            session_id=_required_str(args, "session"),
            event_limit=_int(args.get("event_limit"), 20, minimum=1, maximum=200),
            max_chars=_int(args.get("max_chars"), 500, minimum=50, maximum=5000),
            local_debug=_bool(args.get("local_debug"), False),
        )
    elif name == "threadvault_export_preview":
        session_ids = _session_ids(args.get("session"))
        project = _optional_str(args.get("project"))
        if not session_ids and not project:
            raise ValueError("threadvault_export_preview requires session or project.")
        payload = store.client_export_preview(
            out_dir=Path(_required_str(args, "out")),
            profile=_str(args.get("profile"), "markdown"),
            session_ids=session_ids,
            project=project,
            privacy_mode=_str(args.get("privacy_mode"), "warn"),
            privacy_config_path=_optional_path(args.get("privacy_config")),
            skill_name=_optional_str(args.get("skill_name")),
            skill_description=_optional_str(args.get("skill_description")),
        )
    else:
        raise ValueError(f"Unknown tool: {name}")
    return _tool_result(payload)


def _tool_result(payload: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": payload,
        "isError": False,
    }


def _handle_notification(method: str) -> None:
    if method in {"notifications/initialized", "notifications/cancelled", "notifications/progress"}:
        return


def _jsonrpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _object_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required or [],
    }


def _tool_manifest(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": tool["name"],
        "description": tool["description"],
        "input_schema": tool["inputSchema"],
    }


def _required_str(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required.")
    return value


def _str(value: Any, default: str) -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError("Expected a string value.")
    return value


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Expected a string value.")
    return value


def _optional_path(value: Any) -> Path | None:
    text = _optional_str(value)
    return Path(text) if text else None


def _bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError("Expected a boolean value.")
    return value


def _int(value: Any, default: int, *, minimum: int, maximum: int) -> int:
    if value is None:
        return default
    if not isinstance(value, int):
        raise ValueError("Expected an integer value.")
    if value < minimum or value > maximum:
        raise ValueError(f"Integer value must be between {minimum} and {maximum}.")
    return value


def _session_ids(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise ValueError("session must be a string or array of strings.")

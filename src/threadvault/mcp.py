from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

from . import __version__
from .export_targets import ExportTargetRequest
from .mcp_contracts import MCP_MANIFEST_CONTRACT_VERSION, MCP_PROTOCOL_VERSION, MCP_SERVER_NAME
from .mcp_runtime import McpReadOnlyArchive
from .mcp_validation import McpValidationError, validate_initialize_params, validate_tool_arguments
from .store import capabilities

JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603


@dataclass
class McpRuntimeConfig:
    db_path: Path
    config_path: Path | None = None
    _initialize_requested: bool = field(default=False, init=False, repr=False)
    _initialized: bool = field(default=False, init=False, repr=False)
    _request_ids: set[str | int] = field(default_factory=set, init=False, repr=False)

    def register_request_id(self, request_id: str | int) -> None:
        if request_id in self._request_ids:
            raise McpProtocolError(JSONRPC_INVALID_REQUEST, "Request id was already used in this session.")
        self._request_ids.add(request_id)

    def begin_initialize(self) -> None:
        if self._initialize_requested:
            raise McpProtocolError(JSONRPC_INVALID_REQUEST, "Server initialization was already requested.")
        self._initialize_requested = True

    def finish_initialize(self) -> None:
        if self._initialize_requested:
            self._initialized = True

    def require_initialize_requested(self) -> None:
        if not self._initialize_requested:
            raise McpProtocolError(JSONRPC_INVALID_REQUEST, "Server initialization has not started.")

    def require_initialized(self) -> None:
        if not self._initialized:
            raise McpProtocolError(JSONRPC_INVALID_REQUEST, "Server initialization is not complete.")


class McpProtocolError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


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
                "Register this server through OpenCode MCP configuration and keep write/export flows outside the read-only tool set."
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
            "annotations": _read_only_annotations("ThreadVault capabilities"),
        },
        {
            "name": "threadvault_stats",
            "description": "Return local archive counts and clean search-index diagnostics.",
            "inputSchema": _object_schema({}),
            "annotations": _read_only_annotations("ThreadVault archive statistics"),
        },
        {
            "name": "threadvault_doctor",
            "description": "Run local archive, FTS, and Codex discovery diagnostics.",
            "inputSchema": _object_schema(
                {
                    "codex_home": {"type": "string", "description": "Optional Codex home directory to inspect."},
                    "local_debug": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include local filesystem paths in diagnostic output.",
                    },
                }
            ),
            "annotations": _read_only_annotations("ThreadVault diagnostics"),
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
            "annotations": _read_only_annotations("Retrieve ThreadVault evidence"),
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
            "annotations": _read_only_annotations("Inspect a ThreadVault session"),
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
            "annotations": _read_only_annotations("Preview a ThreadVault export"),
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
    has_request_id = "id" in message
    request_id = message.get("id")
    if has_request_id and not _valid_request_id(request_id):
        return _jsonrpc_error(None, JSONRPC_INVALID_REQUEST, "Invalid Request")
    if message.get("jsonrpc") != "2.0":
        return _jsonrpc_error(request_id, JSONRPC_INVALID_REQUEST, "Invalid Request")
    method = message.get("method")
    if not isinstance(method, str):
        return _jsonrpc_error(request_id, JSONRPC_INVALID_REQUEST, "Invalid Request")
    params = message.get("params", {})
    if not has_request_id:
        _handle_notification(method, params, config)
        return None
    try:
        config.register_request_id(request_id)
        result = _dispatch(method, params, config)
    except McpProtocolError as exc:
        return _jsonrpc_error(request_id, exc.code, exc.message)
    except McpValidationError as exc:
        return _jsonrpc_error(request_id, JSONRPC_INVALID_PARAMS, str(exc))
    except KeyError:
        return _jsonrpc_error(request_id, JSONRPC_INVALID_PARAMS, "Requested session was not found.")
    except NotImplementedError:
        return _jsonrpc_error(request_id, JSONRPC_METHOD_NOT_FOUND, f"Method not found: {method}")
    except Exception:  # pragma: no cover - defensive JSON-RPC guard
        return _jsonrpc_error(request_id, JSONRPC_INTERNAL_ERROR, "Internal error")
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _dispatch(method: str, params: Any, config: McpRuntimeConfig) -> dict[str, Any]:
    if method == "initialize":
        validate_initialize_params(params)
        config.begin_initialize()
        return _initialize_result()
    if method == "ping":
        config.require_initialize_requested()
        _require_object_params(params, "ping")
        return {}
    config.require_initialized()
    if method == "tools/list":
        _validate_tools_list_params(params)
        return {"tools": mcp_tools()}
    if method == "tools/call":
        if not isinstance(params, dict):
            raise McpValidationError("tools/call params must be an object.")
        unexpected = sorted(set(params) - {"name", "arguments", "_meta"})
        if unexpected:
            raise McpValidationError(f"tools/call contains an unexpected field: {unexpected[0]}.")
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str):
            raise McpValidationError("tools/call requires a string name.")
        tool = _tool_by_name(name)
        return _call_tool(name, validate_tool_arguments(tool, arguments), config)
    raise NotImplementedError


def _initialize_result() -> dict[str, Any]:
    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": {"name": MCP_SERVER_NAME, "version": __version__},
        "instructions": (
            "ThreadVault provides local-first, read-only archive retrieval, session inspection, "
            "export preview, diagnostics, and capability discovery tools."
        ),
    }


def _call_tool(name: str, args: dict[str, Any], config: McpRuntimeConfig) -> dict[str, Any]:
    archive = McpReadOnlyArchive(config.db_path, config.config_path)
    if name == "threadvault_capabilities":
        payload = capabilities()
    elif name == "threadvault_stats":
        payload = archive.stats()
    elif name == "threadvault_doctor":
        payload = archive.doctor(
            codex_home=_optional_path(args.get("codex_home")),
            local_debug=_bool(args.get("local_debug"), False),
        )
    elif name == "threadvault_retrieve":
        payload = archive.retrieve(
            query=_required_str(args, "query"),
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
        payload = archive.session(
            session_id=_required_str(args, "session"),
            event_limit=_int(args.get("event_limit"), 20, minimum=1, maximum=200),
            max_chars=_int(args.get("max_chars"), 500, minimum=50, maximum=5000),
            local_debug=_bool(args.get("local_debug"), False),
        )
    elif name == "threadvault_export_preview":
        session_ids = _session_ids(args.get("session"))
        project = _optional_str(args.get("project"))
        if not session_ids and not project:
            raise McpValidationError("threadvault_export_preview requires session or project.")
        payload = archive.export_preview(
            ExportTargetRequest(
                out_dir=Path(_required_str(args, "out")),
                profile=_str(args.get("profile"), "markdown"),
                session_ids=session_ids,
                project=project,
                privacy_mode=_str(args.get("privacy_mode"), "warn"),
                privacy_config_path=_optional_path(args.get("privacy_config")),
                skill_name=_optional_str(args.get("skill_name")),
                skill_description=_optional_str(args.get("skill_description")),
            )
        )
    else:
        raise McpValidationError("Unknown tool.")
    return _tool_result(payload)


def _tool_result(payload: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": payload,
        "isError": False,
    }


def _handle_notification(method: str, params: Any, config: McpRuntimeConfig) -> None:
    if method == "notifications/initialized":
        if isinstance(params, dict):
            config.finish_initialize()
        return
    if method in {"notifications/cancelled", "notifications/progress"}:
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


def _read_only_annotations(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }


def _tool_manifest(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": tool["name"],
        "description": tool["description"],
        "input_schema": tool["inputSchema"],
        "annotations": tool["annotations"],
    }


def _tool_by_name(name: str) -> dict[str, Any]:
    for tool in mcp_tools():
        if tool["name"] == name:
            return tool
    raise McpValidationError("Unknown tool.")


def _valid_request_id(value: Any) -> bool:
    return isinstance(value, str) or type(value) is int


def _require_object_params(params: Any, method: str) -> dict[str, Any]:
    if not isinstance(params, dict):
        raise McpValidationError(f"{method} params must be an object.")
    return params


def _validate_tools_list_params(params: Any) -> None:
    params = _require_object_params(params, "tools/list")
    unexpected = sorted(set(params) - {"cursor", "_meta"})
    if unexpected:
        raise McpValidationError(f"tools/list contains an unexpected field: {unexpected[0]}.")
    cursor = params.get("cursor")
    if cursor is not None and not isinstance(cursor, str):
        raise McpValidationError("tools/list cursor must be a string.")


def _required_str(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise McpValidationError(f"{key} is required.")
    return value


def _str(value: Any, default: str) -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise McpValidationError("Expected a string value.")
    return value


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise McpValidationError("Expected a string value.")
    return value


def _optional_path(value: Any) -> Path | None:
    text = _optional_str(value)
    return Path(text) if text else None


def _bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise McpValidationError("Expected a boolean value.")
    return value


def _int(value: Any, default: int, *, minimum: int, maximum: int) -> int:
    if value is None:
        return default
    if type(value) is not int:
        raise McpValidationError("Expected an integer value.")
    if value < minimum or value > maximum:
        raise McpValidationError(f"Integer value must be between {minimum} and {maximum}.")
    return value


def _session_ids(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise McpValidationError("session must be a string or array of strings.")

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .app_config import AppConfig

READ_ONLY_SERVER_MANIFEST_CONTRACT_VERSION = "governance_read_only_server_manifest.v1"
READ_ONLY_SERVER_SMOKE_CONTRACT_VERSION = "governance_read_only_server_smoke.v1"
READ_ONLY_SERVER_MANIFEST_COMMAND = "threadvault governance server read-only-manifest --json"
READ_ONLY_SERVER_SMOKE_COMMAND = "threadvault governance server read-only-smoke --json"
READ_ONLY_SERVER_START_COMMAND = "threadvault governance server serve-read-only --enable --host 127.0.0.1 --port 8765"


READ_ONLY_ROUTES = [
    {
        "method": "GET",
        "path": "/health",
        "operation": "health",
        "source_interface": "threadvault.shared_server",
        "schema": "governance_read_only_server_smoke",
        "access_level": "summary_search",
        "mutates_state": False,
        "raw_paths_included": False,
    },
    {
        "method": "GET",
        "path": "/manifest",
        "operation": "server_manifest",
        "source_interface": "threadvault.shared_server",
        "schema": "governance_read_only_server_manifest",
        "access_level": "summary_search",
        "mutates_state": False,
        "raw_paths_included": False,
    },
    {
        "method": "GET",
        "path": "/client/manifest",
        "operation": "client_manifest",
        "source_interface": "ArchiveStore.client_manifest",
        "schema": "client_interface_manifest",
        "access_level": "summary_search",
        "mutates_state": False,
        "raw_paths_included": False,
    },
    {
        "method": "GET",
        "path": "/client/overview",
        "operation": "client_overview",
        "source_interface": "ArchiveStore.client_overview",
        "schema": "client_overview",
        "access_level": "summary_search",
        "mutates_state": False,
        "raw_paths_included": False,
    },
    {
        "method": "GET",
        "path": "/agent/retrieve",
        "operation": "agent_retrieve",
        "source_interface": "ArchiveStore.agent_retrieve",
        "schema": "agent_retrieval",
        "access_level": "summary_search",
        "mutates_state": False,
        "raw_paths_included": False,
    },
    {
        "method": "GET",
        "path": "/governance/status",
        "operation": "governance_status",
        "source_interface": "ArchiveStore.governance_status",
        "schema": "governance_status",
        "access_level": "summary_search",
        "mutates_state": False,
        "raw_paths_included": False,
    },
    {
        "method": "GET",
        "path": "/governance/server/policy-readiness",
        "operation": "governance_server_policy_readiness",
        "source_interface": "ArchiveStore.governance_server_policy_readiness",
        "schema": "governance_server_policy_readiness",
        "access_level": "summary_search",
        "mutates_state": False,
        "raw_paths_included": False,
    },
]


def shared_server_manifest(config: AppConfig, *, db_path: Path | None = None) -> dict[str, Any]:
    return {
        "contract_version": READ_ONLY_SERVER_MANIFEST_CONTRACT_VERSION,
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "team_enforcement_ready": False,
        },
        "runtime": {
            "implemented": True,
            "prototype": True,
            "production_ready": False,
            "framework": "python-stdlib-http-server",
            "default_host": "127.0.0.1",
            "bind_requires_enable": True,
            "running": False,
            "required_for_local_cli": False,
        },
        "routes": READ_ONLY_ROUTES,
        "read_only": {
            "all_routes_read_only": True,
            "write_routes": [],
            "mutation_commands_exposed": False,
            "export_execution_exposed": False,
            "restore_execution_exposed": False,
            "retention_mutation_exposed": False,
            "external_model_calls": False,
        },
        "security": {
            "loopback_default": True,
            "authentication_implemented": False,
            "identity_binding_implemented": False,
            "central_policy_enforced": False,
            "public_network_default": False,
        },
        "integration": {
            "uses_archive_store": True,
            "reuses_client_interface": True,
            "reuses_agent_interface": True,
            "reuses_governance_interface": True,
            "reparses_codex_transcripts": False,
            "v2_retrieval_core_changed": False,
        },
        "commands": {
            "manifest": READ_ONLY_SERVER_MANIFEST_COMMAND,
            "smoke": READ_ONLY_SERVER_SMOKE_COMMAND,
            "start": READ_ONLY_SERVER_START_COMMAND,
        },
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "db_path": str(db_path) if db_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "new_dependency_required": False,
            "route_count": len(READ_ONLY_ROUTES),
        },
    }


def read_only_server_smoke(store: Any, config_path: Path | None = None, *, query: str = "pytest") -> dict[str, Any]:
    targets = [
        "/health",
        "/manifest",
        "/client/manifest",
        "/client/overview",
        f"/agent/retrieve?query={query}",
        "/governance/status",
        "/governance/server/policy-readiness",
    ]
    checks = []
    for target in targets:
        response = handle_read_only_request(store, target, config_path=config_path)
        checks.append(
            {
                "path": target.split("?", 1)[0],
                "status_code": response["status_code"],
                "ok": response["ok"],
                "schema": response["schema"],
            }
        )
    return {
        "contract_version": READ_ONLY_SERVER_SMOKE_CONTRACT_VERSION,
        "ok": all(check["ok"] for check in checks),
        "request": {
            "query": query,
            "config_path": str(config_path) if config_path else None,
        },
        "checks": checks,
        "summary": {
            "checked_route_count": len(checks),
            "passed_route_count": sum(1 for check in checks if check["ok"]),
            "failed_route_count": sum(1 for check in checks if not check["ok"]),
        },
        "governance": {
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "read_only": True,
            "team_enforcement_ready": False,
        },
        "diagnostics": {
            "local_first": True,
            "privacy_first": True,
            "server_required": False,
            "external_model_calls": False,
            "v2_retrieval_core_changed": False,
        },
    }


def handle_read_only_request(store: Any, target: str, config_path: Path | None = None) -> dict[str, Any]:
    parsed = urlparse(target)
    params = parse_qs(parsed.query)
    path = parsed.path.rstrip("/") or "/"
    try:
        if path == "/health":
            return _response(
                HTTPStatus.OK,
                "health",
                {
                    "ok": True,
                    "status": "ok",
                    "read_only": True,
                    "server_required": False,
                    "external_model_calls": False,
                },
            )
        if path == "/manifest":
            return _response(
                HTTPStatus.OK,
                "governance_read_only_server_manifest",
                shared_server_manifest(store_config(store, config_path), db_path=getattr(store, "db_path", None)),
            )
        if path == "/client/manifest":
            return _response(HTTPStatus.OK, "client_interface_manifest", store.client_manifest(config_path=config_path))
        if path == "/client/overview":
            return _response(
                HTTPStatus.OK,
                "client_overview",
                store.client_overview(
                    config_path=config_path,
                    query=_first(params, "query"),
                    cwd=_first(params, "cwd"),
                    limit=_int_param(params, "limit", 20),
                    local_debug=False,
                ),
            )
        if path == "/agent/retrieve":
            query = _first(params, "query") or _first(params, "q")
            if not query:
                return _response(
                    HTTPStatus.BAD_REQUEST,
                    "error",
                    {"ok": False, "error": "query_required", "message": "Provide query or q."},
                )
            return _response(
                HTTPStatus.OK,
                "agent_retrieval",
                store.agent_retrieve(
                    query=query,
                    config_path=config_path,
                    mode=_first(params, "mode") or "hybrid",
                    limit=_int_param(params, "limit", 20),
                    vector_limit=_int_param(params, "vector_limit", 10),
                    session_id=_first(params, "session"),
                    cwd=_first(params, "cwd"),
                    local_debug=False,
                ),
            )
        if path == "/governance/status":
            return _response(HTTPStatus.OK, "governance_status", store.governance_status(config_path=config_path))
        if path == "/governance/server/policy-readiness":
            return _response(
                HTTPStatus.OK,
                "governance_server_policy_readiness",
                store.governance_server_policy_readiness(config_path=config_path),
            )
        return _response(HTTPStatus.NOT_FOUND, "error", {"ok": False, "error": "route_not_found", "path": path})
    except Exception as exc:
        return _response(HTTPStatus.INTERNAL_SERVER_ERROR, "error", {"ok": False, "error": "handler_error", "message": str(exc)})


def build_read_only_server(store: Any, host: str, port: int, config_path: Path | None = None) -> ThreadingHTTPServer:
    class ReadOnlyHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            response = handle_read_only_request(store, self.path, config_path=config_path)
            body = json.dumps(response["payload"], ensure_ascii=False, indent=2, default=str).encode("utf-8")
            self.send_response(response["status_code"])
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            self._reject_write()

        def do_PUT(self) -> None:  # noqa: N802
            self._reject_write()

        def do_PATCH(self) -> None:  # noqa: N802
            self._reject_write()

        def do_DELETE(self) -> None:  # noqa: N802
            self._reject_write()

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _reject_write(self) -> None:
            body = json.dumps({"ok": False, "error": "read_only_server"}, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer((host, port), ReadOnlyHandler)


def store_config(store: Any, config_path: Path | None) -> AppConfig:
    from .app_config import load_app_config

    return load_app_config(config_path)


def _response(status: HTTPStatus, schema: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": status.value < 400,
        "status_code": status.value,
        "schema": schema,
        "payload": payload,
    }


def _first(params: dict[str, list[str]], name: str) -> str | None:
    values = params.get(name)
    if not values:
        return None
    return values[0]


def _int_param(params: dict[str, list[str]], name: str, default: int) -> int:
    value = _first(params, name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return max(1, parsed)

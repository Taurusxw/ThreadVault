from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import default_db_path
from .mcp import mcp_manifest
from .schemas import get_schema, schema_names, write_schema_files
from .store import ArchiveStore, robot_guide, robot_schemas

DESKTOP_APP_CONTRACT_VERSION = "desktop_app.v1"
DESKTOP_SMOKE_CONTRACT_VERSION = "desktop_smoke.v1"
DESKTOP_APP_LAUNCH_COMMAND = "threadvault desktop launch"
DESKTOP_SMOKE_COMMAND = "threadvault desktop smoke --json"


@dataclass(frozen=True)
class DesktopAppConfig:
    db_path: Path | None = None
    config_path: Path | None = None
    language: str = "zh"
    limit: int = 20

    @property
    def resolved_db_path(self) -> Path:
        return (self.db_path or default_db_path(self.config_path)).expanduser()


@dataclass(frozen=True)
class DesktopSessionRow:
    session_id: str
    cwd: str
    updated_at: str
    event_count: int
    warning_count: int


@dataclass(frozen=True)
class DesktopSearchRow:
    session_id: str
    score: str
    preview: str


@dataclass(frozen=True)
class DesktopSnapshot:
    contract_version: str
    db_path: str
    sessions: list[DesktopSessionRow]
    search_rows: list[DesktopSearchRow]
    selected_session_id: str
    selected_summary: str
    status: str
    has_query: bool


@dataclass(frozen=True)
class DesktopTextResult:
    title: str
    text: str
    status: str


class DesktopDataGateway:
    """Small desktop-facing interface over ArchiveStore client contracts."""

    def __init__(self, store: ArchiveStore, config: DesktopAppConfig) -> None:
        self.store = store
        self.config = config

    def snapshot(self, query: str = "", session_id: str = "") -> DesktopSnapshot:
        overview = self.store.client_overview(query=query or None, limit=self.config.limit, local_debug=False)
        sessions = [_session_row(item) for item in overview.get("sessions", [])]
        search_rows = [_search_row(item) for item in _search_results(overview)]
        selected_session_id = session_id or (sessions[0].session_id if sessions else "")
        selected_summary = ""
        if selected_session_id:
            selected_summary = self.session_summary(selected_session_id)
        return DesktopSnapshot(
            contract_version=DESKTOP_APP_CONTRACT_VERSION,
            db_path=str(self.config.resolved_db_path),
            sessions=sessions,
            search_rows=search_rows,
            selected_session_id=selected_session_id,
            selected_summary=selected_summary,
            status=_status_text(len(sessions), len(search_rows), bool(query)),
            has_query=bool(query),
        )

    def session_summary(self, session_id: str) -> str:
        payload = self.store.client_session(session_id=session_id, event_limit=12, local_debug=False)
        summary = payload.get("summary") or {}
        text = summary.get("title") or summary.get("topic") or ""
        if not text:
            event_count = len(payload.get("events", []))
            return f"{session_id}\n事件预览: {event_count}"
        return str(text).strip()

    def export_preview(
        self,
        *,
        session_id: str,
        out_dir: str,
        profile: str = "markdown",
        privacy_mode: str = "warn",
    ) -> DesktopTextResult:
        payload = self.store.client_export_preview(
            out_dir=Path(out_dir or "threadvault-desktop-export"),
            profile=profile,
            session_ids=[session_id],
            privacy_mode=privacy_mode,
            skill_name="threadvault-reuse" if profile == "skill" else None,
            skill_description="Reusable ThreadVault session export." if profile == "skill" else None,
        )
        diagnostics = payload.get("diagnostics", {})
        privacy = payload.get("privacy", {})
        lines = [
            f"Profile: {payload.get('request', {}).get('profile', profile)}",
            f"Planned files: {diagnostics.get('planned_file_count', 0)}",
            f"Skipped: {diagnostics.get('skipped_count', 0)}",
            f"Privacy findings: {privacy.get('effective_findings_count', privacy.get('findings_count', 0))}",
            f"Blocked: {privacy.get('blocked', False)}",
            "",
            "Files:",
        ]
        for file in payload.get("planned_files", [])[:40]:
            lines.append(f"- {file.get('kind', 'file')}  {file.get('path', '')}")
        lines.extend(["", "Execute after review:", str(payload.get("actions", {}).get("execute", ""))])
        return DesktopTextResult(
            title="导出预览",
            text="\n".join(lines).strip(),
            status=f"预览 {diagnostics.get('planned_file_count', 0)} 个文件，未写入磁盘",
        )

    def warnings_summary(self, session_id: str) -> DesktopTextResult:
        payload = self.store.client_warnings(session_id=session_id, local_debug=False)
        warnings = payload.get("warnings", {})
        privacy = payload.get("privacy", {})
        lines = [
            f"Session: {session_id}",
            f"Warnings: {warnings.get('count', 0)}",
            f"Privacy findings: {privacy.get('summary', {}).get('effective_findings_count', 0)}",
            "",
            "Warnings:",
        ]
        for item in warnings.get("items", [])[:40]:
            lines.append(f"- {item.get('code', '')}: {item.get('message', '')}")
        findings = privacy.get("findings", [])
        if findings:
            lines.extend(["", "Privacy findings:"])
            for item in findings[:20]:
                lines.append(f"- {item.get('severity', '')} {item.get('kind', '')}: {item.get('excerpt', '')}")
        return DesktopTextResult(
            title="隐私告警",
            text="\n".join(lines).strip(),
            status=f"告警 {warnings.get('count', 0)} 条",
        )

    def integration_summary(self) -> DesktopTextResult:
        manifest = mcp_manifest()
        tools = manifest.get("tools", [])
        lines = [
            "MCP stdio server",
            "Manifest: threadvault mcp manifest --json",
            "Serve: threadvault mcp serve",
            "",
            "Tools:",
        ]
        for tool in tools:
            lines.append(f"- {tool.get('name', '')}: {tool.get('description', '')}")
        lines.extend([
            "",
            "Privacy:",
            "- local_first: True",
            "- writes_files: False",
            "- external_model_calls: False",
        ])
        return DesktopTextResult(title="MCP 联动", text="\n".join(lines), status=f"MCP 工具 {len(tools)} 个")

    def health_summary(self) -> DesktopTextResult:
        stats = self.store.stats()
        doctor = self.store.doctor()
        lines = [
            f"DB: {self.config.resolved_db_path}",
            f"Doctor OK: {doctor.get('ok')}",
            f"Python: {doctor.get('python', '')}",
            f"Platform: {doctor.get('platform', '')}",
            "",
            "Stats:",
        ]
        for key in sorted(stats):
            lines.append(f"- {key}: {stats[key]}")
        if doctor.get("errors"):
            lines.extend(["", "Errors:"])
            lines.extend(f"- {item}" for item in doctor.get("errors", []))
        return DesktopTextResult(
            title="健康诊断",
            text="\n".join(lines),
            status="诊断通过" if doctor.get("ok") else "诊断发现问题",
        )

    def backup_database(self, out: str, *, force: bool = False) -> DesktopTextResult:
        payload = self.store.backup(Path(out or "threadvault-desktop-backups"), force=force)
        lines = [
            f"OK: {payload.get('ok')}",
            f"Destination: {payload.get('destination', '')}",
            f"Bytes: {payload.get('bytes', 0)}",
            f"Schema version: {payload.get('schema_version')}",
            f"Manifest: {_manifest_status(payload.get('manifest'))}",
        ]
        if payload.get("error"):
            lines.append(f"Error: {payload.get('error')}")
        return DesktopTextResult(
            title="备份",
            text="\n".join(lines),
            status="备份完成" if payload.get("ok") else "备份未完成",
        )

    def verify_backup(self, backup: str) -> DesktopTextResult:
        payload = self.store.verify_backup(Path(backup), manifest=True)
        lines = [
            f"OK: {payload.get('ok')}",
            f"Backup: {payload.get('backup', '')}",
            f"Exists: {payload.get('exists')}",
            f"Bytes: {payload.get('bytes', 0)}",
            f"Integrity: {payload.get('integrity_check')}",
            f"Schema version: {payload.get('schema_version')}",
            f"Manifest: {_manifest_status(payload.get('manifest'))}",
        ]
        if payload.get("errors"):
            lines.extend(["", "Errors:", _pretty_json(payload.get("errors"))])
        return DesktopTextResult(
            title="备份验证",
            text="\n".join(lines),
            status="备份验证通过" if payload.get("ok") else "备份验证失败",
        )

    def restore_plan(self, backup: str, target_db: str) -> DesktopTextResult:
        payload = self.store.restore_plan(Path(backup), Path(target_db or self.config.resolved_db_path))
        lines = [
            f"OK: {payload.get('ok')}",
            f"Mode: {payload.get('mode')}",
            f"Backup: {payload.get('backup', '')}",
            f"Target DB: {payload.get('target_db', '')}",
            "",
            "Warnings:",
            _pretty_json(payload.get("warnings", [])),
            "",
            "Errors:",
            _pretty_json(payload.get("errors", [])),
            "",
            "Recommended actions:",
        ]
        lines.extend(f"- {item}" for item in payload.get("recommended_actions", []))
        return DesktopTextResult(
            title="恢复预检",
            text="\n".join(lines).strip(),
            status="恢复预检通过" if payload.get("ok") else "恢复预检发现阻塞",
        )

    def restore_to_new_target(self, backup: str, target_db: str) -> DesktopTextResult:
        target = Path(target_db)
        if target.exists():
            return DesktopTextResult(
                title="恢复执行",
                text=f"Target already exists, desktop restore apply refuses overwrite:\n{target}",
                status="恢复未执行：目标已存在",
            )
        payload = self.store.restore(
            backup=Path(backup),
            target_db=target,
            apply=True,
            overwrite=False,
            allow_missing_manifest=False,
        )
        lines = [
            f"OK: {payload.get('ok')}",
            f"Mode: {payload.get('mode')}",
            f"Backup: {payload.get('backup', '')}",
            f"Target DB: {payload.get('target_db', '')}",
            f"Apply: {payload.get('apply')}",
            f"Overwrite: {payload.get('overwrite')}",
            "",
            "Errors:",
            _pretty_json(payload.get("errors", [])),
            "",
            "Warnings:",
            _pretty_json(payload.get("warnings", [])),
        ]
        verification = payload.get("restored_verification")
        if verification:
            lines.extend(["", "Restored verification:", _pretty_json(_restore_verification_preview(verification))])
        return DesktopTextResult(
            title="恢复执行",
            text="\n".join(lines).strip(),
            status="恢复已执行" if payload.get("ok") and payload.get("mode") == "applied" else "恢复未执行",
        )

    def reindex_search(self) -> DesktopTextResult:
        payload = self.store.reindex()
        aligned = payload.get("events") == payload.get("events_fts")
        return DesktopTextResult(
            title="重建索引",
            text=_pretty_json(payload),
            status="索引已重建" if aligned else "索引重建失败",
        )

    def vacuum_database(self) -> DesktopTextResult:
        payload = self.store.vacuum()
        return DesktopTextResult(
            title="数据库压缩",
            text=_pretty_json(payload),
            status="数据库压缩完成" if payload.get("ok") else "数据库压缩失败",
        )

    def schema_summary(self, schema_name: str = "") -> DesktopTextResult:
        names = schema_names()
        selected = schema_name.strip() or (names[0] if names else "")
        lines = [
            f"Schema count: {len(names)}",
            "",
            "Schemas:",
        ]
        lines.extend(f"- {name}" for name in names[:120])
        if selected:
            schema = get_schema(selected)
            lines.extend([
                "",
                f"Selected: {selected}",
                _pretty_json(_schema_preview(schema)),
            ])
        return DesktopTextResult(
            title="结构定义",
            text="\n".join(lines),
            status=f"结构定义 {len(names)} 个",
        )

    def robot_docs_summary(self) -> DesktopTextResult:
        guide = robot_guide()
        schemas = robot_schemas()
        commands = guide.get("recommended_commands", [])
        lines = [
            f"Purpose: {guide.get('purpose', '')}",
            f"JSON contract: {guide.get('json_contract', '')}",
            f"Recommended commands: {len(commands)}",
            f"Robot schema entries: {len(schemas)}",
            "",
            "Recommended commands:",
        ]
        lines.extend(f"- {command}" for command in commands[:80])
        return DesktopTextResult(
            title="机器人文档",
            text="\n".join(lines),
            status=f"机器人命令 {len(commands)} 条",
        )

    def governance_summary(self) -> DesktopTextResult:
        payload = self.store.governance_status(config_path=self.config.config_path)
        governance = payload.get("governance", {})
        lines = [
            f"Contract: {payload.get('contract_version', '')}",
            f"Enabled: {governance.get('enabled')}",
            f"Server required: {governance.get('server_required')}",
            f"Team mode: {governance.get('team_mode')}",
            f"External model calls: {governance.get('external_model_calls')}",
            "",
            _pretty_json(payload),
        ]
        return DesktopTextResult(
            title="治理状态",
            text="\n".join(lines),
            status="治理状态已读取",
        )

    def governance_diagnostics_summary(self) -> DesktopTextResult:
        checks = [
            ("status", lambda: self.store.governance_status(config_path=self.config.config_path)),
            ("enforcement_gaps", lambda: self.store.governance_enforcement_gaps(config_path=self.config.config_path)),
            ("policy_readiness", lambda: self.store.governance_policy_readiness(config_path=self.config.config_path)),
            ("server_policy_readiness", lambda: self.store.governance_server_policy_readiness(config_path=self.config.config_path)),
            ("centralized_audit_readiness", lambda: self.store.governance_centralized_audit_readiness(config_path=self.config.config_path)),
            ("central_policy_readiness", lambda: self.store.governance_central_policy_readiness(config_path=self.config.config_path)),
            ("central_backup_readiness", lambda: self.store.governance_central_backup_readiness(config_path=self.config.config_path)),
            ("identity_actor_readiness", lambda: self.store.governance_identity_actor_readiness(config_path=self.config.config_path)),
            ("v3_completion_gap_audit", lambda: self.store.governance_v3_completion_gap_audit(config_path=self.config.config_path)),
        ]
        results: dict[str, Any] = {}
        lines = ["Governance diagnostics:", ""]
        for name, run in checks:
            try:
                payload = run()
            except Exception as exc:  # noqa: BLE001 - diagnostics should report individual failures.
                results[name] = {"ok": False, "error": str(exc)}
                lines.append(f"- {name}: error")
                continue
            results[name] = payload
            lines.append(f"- {name}: {_diagnostic_status(payload)}")
        lines.extend(["", _pretty_json(results)])
        return DesktopTextResult(
            title="治理诊断",
            text="\n".join(lines),
            status=f"治理诊断 {len(results)} 项",
        )

    def write_schemas(self, out_dir: str) -> DesktopTextResult:
        paths = write_schema_files(Path(out_dir or "threadvault-desktop-schemas"))
        lines = [
            f"Written files: {len(paths)}",
            "",
            "Files:",
        ]
        lines.extend(f"- {path}" for path in paths[:160])
        return DesktopTextResult(
            title="写出结构定义",
            text="\n".join(lines),
            status=f"已写出 {len(paths)} 个结构定义文件",
        )

    def advanced_summary(self) -> DesktopTextResult:
        lines = [
            "高级能力优先提供只读原生入口，避免误触破坏性操作。",
            "",
            "Read-only desktop actions:",
            "- threadvault schemas list --json",
            "- threadvault robot-docs guide --json",
            "- threadvault governance status --json",
            "",
            "Dangerous operations still require explicit CLI confirmation gates.",
        ]
        return DesktopTextResult(title="高级", text="\n".join(lines), status="高级命令入口已列出")


def build_desktop_gateway(config: DesktopAppConfig) -> DesktopDataGateway:
    return DesktopDataGateway(ArchiveStore(config.resolved_db_path), config)


def desktop_snapshot_payload(snapshot: DesktopSnapshot) -> dict[str, Any]:
    return {
        "contract_version": snapshot.contract_version,
        "db_path": snapshot.db_path,
        "sessions": [row.__dict__ for row in snapshot.sessions],
        "search_rows": [row.__dict__ for row in snapshot.search_rows],
        "selected_session_id": snapshot.selected_session_id,
        "selected_summary": snapshot.selected_summary,
        "status": snapshot.status,
        "has_query": snapshot.has_query,
    }


def run_desktop_smoke(config: DesktopAppConfig) -> dict[str, Any]:
    gateway = build_desktop_gateway(config)
    snapshot = gateway.snapshot()
    integration = gateway.integration_summary()
    advanced = gateway.advanced_summary()
    return {
        "contract_version": DESKTOP_SMOKE_CONTRACT_VERSION,
        "ok": bool(_tkinter_available() and snapshot.contract_version == DESKTOP_APP_CONTRACT_VERSION),
        "desktop": {
            "launch_command": DESKTOP_APP_LAUNCH_COMMAND,
            "smoke_command": DESKTOP_SMOKE_COMMAND,
            "toolkit": "tkinter",
            "tkinter_available": _tkinter_available(),
            "server_required": False,
            "browser_required": False,
            "frontend_build_pipeline": False,
            "background_worker_threads": True,
        },
        "snapshot": {
            "db_path": snapshot.db_path,
            "session_count": len(snapshot.sessions),
            "search_result_count": len(snapshot.search_rows),
            "selected_session_id": snapshot.selected_session_id,
            "has_query": snapshot.has_query,
        },
        "diagnostics": {
            "integration_status": integration.status,
            "advanced_status": advanced.status,
        },
    }


def _session_row(item: dict[str, Any]) -> DesktopSessionRow:
    return DesktopSessionRow(
        session_id=str(item.get("session_id") or ""),
        cwd=str(item.get("cwd") or ""),
        updated_at=str(item.get("updated_at") or item.get("first_seen_at") or ""),
        event_count=int(item.get("event_count") or 0),
        warning_count=int(item.get("warning_count") or 0),
    )


def _search_results(overview: dict[str, Any]) -> list[dict[str, Any]]:
    search = overview.get("search") or {}
    results = search.get("results")
    return results if isinstance(results, list) else []


def _search_row(item: dict[str, Any]) -> DesktopSearchRow:
    return DesktopSearchRow(
        session_id=str(item.get("session_id") or ""),
        score=str(item.get("score") or ""),
        preview=str(item.get("snippet") or item.get("text") or item.get("summary") or ""),
    )


def _status_text(session_count: int, result_count: int, has_query: bool) -> str:
    if has_query:
        return f"搜索结果 {result_count} 条，归档会话 {session_count} 条"
    return f"归档会话 {session_count} 条"


def _tkinter_available() -> bool:
    return importlib.util.find_spec("tkinter") is not None


def _manifest_status(manifest: Any) -> str:
    if not manifest:
        return "none"
    if isinstance(manifest, dict):
        return f"ok={manifest.get('ok')} path={manifest.get('path') or manifest.get('manifest') or ''}"
    return str(manifest)


def _pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _diagnostic_status(payload: dict[str, Any]) -> str:
    if "ok" in payload:
        return f"ok={payload.get('ok')}"
    for section in ("governance", "policy", "server", "readiness", "audit", "backup_restore"):
        value = payload.get(section)
        if isinstance(value, dict):
            flags = [f"{key}={flag}" for key, flag in value.items() if isinstance(flag, bool)]
            if flags:
                return ", ".join(flags[:4])
    return "read"


def _schema_preview(schema: dict[str, Any]) -> dict[str, Any]:
    properties = schema.get("properties", {})
    return {
        "$schema": schema.get("$schema"),
        "title": schema.get("title"),
        "type": schema.get("type"),
        "required": schema.get("required", []),
        "property_count": len(properties) if isinstance(properties, dict) else 0,
        "properties": sorted(properties)[:80] if isinstance(properties, dict) else [],
    }


def _restore_verification_preview(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": payload.get("ok"),
        "backup": payload.get("backup"),
        "schema_version": payload.get("schema_version"),
        "integrity_check": payload.get("integrity_check"),
        "bytes": payload.get("bytes"),
    }

from __future__ import annotations

import importlib.util
import json
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path, PureWindowsPath
from typing import Any

from .codex_integration import codex_integration_status, install_codex_integration
from .config import default_codex_home, default_db_path
from .mcp import mcp_manifest
from .schemas import get_schema, schema_names, write_schema_files
from .state import load_state_thread_index, state_candidates
from .store import ArchiveStore, robot_guide, robot_schemas

DESKTOP_APP_CONTRACT_VERSION = "desktop_app.v2"
DESKTOP_SMOKE_CONTRACT_VERSION = "desktop_smoke.v2"
DESKTOP_APP_LAUNCH_COMMAND = "threadvault desktop launch"
DESKTOP_SMOKE_COMMAND = "threadvault desktop smoke --json"


@dataclass(frozen=True)
class DesktopAppConfig:
    db_path: Path | None = None
    config_path: Path | None = None
    codex_home: Path | None = None
    cold_root: Path | None = None
    backup_root: Path | None = None
    automation_id: str = "threadvault"
    language: str = "zh"
    limit: int = 20

    @property
    def resolved_db_path(self) -> Path:
        return (self.db_path or default_db_path(self.config_path)).expanduser()

    @property
    def resolved_codex_home(self) -> Path:
        return (self.codex_home or default_codex_home()).expanduser()

    @property
    def resolved_backup_root(self) -> Path:
        return (self.backup_root or self.resolved_db_path.parent / "storage-backups").expanduser()

    @property
    def recommended_restore_target(self) -> Path:
        source = self.resolved_db_path
        candidate = source.with_name(f"{source.stem}-restored.db")
        index = 2
        while candidate.exists():
            candidate = source.with_name(f"{source.stem}-restored-{index}.db")
            index += 1
        return candidate


@dataclass(frozen=True)
class DesktopSessionRow:
    session_id: str
    title: str
    project: str
    cwd: str
    updated_at: str
    event_count: int
    warning_count: int


@dataclass(frozen=True)
class DesktopSearchRow:
    session_id: str
    title: str
    project: str
    score: str
    preview: str


@dataclass(frozen=True)
class DesktopExportPlan:
    session_id: str
    out_dir: str
    profile: str
    privacy_mode: str
    planned_files: int
    privacy_findings: int
    blocked: bool
    text: str
    status: str

    @property
    def can_export(self) -> bool:
        return self.planned_files > 0 and not self.blocked


@dataclass(frozen=True)
class DesktopBackupCenter:
    headline: str
    detail: str
    last_run: str
    next_run: str
    schedule: str
    disk: str
    out_root: str
    action: str
    profile: str | None
    can_run: bool
    text: str
    status: str


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
        self._state_index_cache: dict[str, dict[str, Any]] = {}
        self._state_index_signature: tuple[tuple[str, int | None, int | None], ...] | None = None

    def snapshot(self, query: str = "", session_id: str = "") -> DesktopSnapshot:
        overview = self.store.client_overview(query=query or None, limit=self.config.limit, local_debug=False)
        thread_index = self._state_index()
        sessions = [_session_row(item, thread_index) for item in overview.get("sessions", [])]
        session_index = {row.session_id: row for row in sessions}
        search_rows = [_search_row(item, thread_index, session_index) for item in _search_results(overview)]
        selected_session_id = session_id or (sessions[0].session_id if sessions else "")
        selected_summary = ""
        if selected_session_id:
            selected = session_index.get(selected_session_id)
            selected_summary = _session_card_summary(selected) if selected else self.session_summary(selected_session_id)
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
        state = self._state_index().get(session_id, {})
        project = _project_name(payload.get("session", {}).get("cwd"))
        text = _friendly_title(state.get("title"), project)
        if not text:
            text = _friendly_title(summary.get("title") or summary.get("topic"), project)
        if not text:
            event_count = len(payload.get("events", []))
            return f"未命名会话\n事件预览：{event_count}"
        session = payload.get("session") or {}
        return "\n".join([
            str(text).strip(),
            f"项目：{project}",
            f"最近更新：{_friendly_time(session.get('updated_at'))}",
            f"事件：{session.get('event_count', 0)}　警告：{session.get('warning_count', 0)}",
        ])

    def prepare_export(
        self,
        *,
        session_id: str,
        out_dir: str,
        profile: str = "markdown",
        privacy_mode: str = "warn",
    ) -> DesktopExportPlan:
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
        planned = int(diagnostics.get("planned_file_count", 0))
        findings = int(privacy.get("effective_findings_count", privacy.get("findings_count", 0)) or 0)
        blocked = bool(privacy.get("blocked", False))
        lines = [
            f"导出格式：{_profile_label(profile)}",
            f"计划写入：{planned} 个文件",
            f"隐私发现：{findings} 条",
            f"处理方式：{_privacy_label(privacy_mode)}",
            f"是否阻止：{'是' if blocked else '否'}",
            "",
            "文件清单：",
        ]
        for file in payload.get("planned_files", [])[:40]:
            lines.append(f"- {file.get('path', '')}")
        lines.extend(["", "预览未写入磁盘。确认内容和隐私处理方式后，可点击“确认导出”。"])
        return DesktopExportPlan(
            session_id=session_id,
            out_dir=str(Path(out_dir or "threadvault-desktop-export")),
            profile=profile,
            privacy_mode=privacy_mode,
            planned_files=planned,
            privacy_findings=findings,
            blocked=blocked,
            text="\n".join(lines).strip(),
            status=("预览被隐私规则阻止" if blocked else f"预览完成：{planned} 个文件，尚未写入"),
        )

    def execute_export(self, plan: DesktopExportPlan) -> DesktopTextResult:
        if not plan.can_export:
            return DesktopTextResult("导出", "当前预览不可执行，请重新预览并处理阻塞项。", "导出未执行")
        payload = self.store.export_target(
            Path(plan.out_dir),
            profile=plan.profile,
            session_ids=[plan.session_id],
            privacy_mode=plan.privacy_mode,
            skill_name="threadvault-reuse" if plan.profile == "skill" else None,
            skill_description="Reusable ThreadVault session export." if plan.profile == "skill" else None,
        )
        files = payload.get("files", [])
        manifest = Path(plan.out_dir) / "threadvault-export-manifest.json"
        return DesktopTextResult(
            title="导出完成",
            text="\n".join([
                "导出已完成。",
                f"格式：{_profile_label(plan.profile)}",
                f"文件：{len(files)} 个",
                f"输出目录：{Path(plan.out_dir).resolve()}",
                f"清单：{manifest.resolve()}",
            ]),
            status=f"导出完成：{len(files)} 个文件",
        )

    def export_preview(
        self,
        *,
        session_id: str,
        out_dir: str,
        profile: str = "markdown",
        privacy_mode: str = "warn",
    ) -> DesktopTextResult:
        plan = self.prepare_export(
            session_id=session_id,
            out_dir=out_dir,
            profile=profile,
            privacy_mode=privacy_mode,
        )
        return DesktopTextResult(title="导出预览", text=plan.text, status=plan.status)

    def warnings_summary(self, session_id: str) -> DesktopTextResult:
        payload = self.store.client_warnings(session_id=session_id, local_debug=False)
        warnings = payload.get("warnings", {})
        privacy = payload.get("privacy", {})
        lines = [
            f"解析警告：{warnings.get('count', 0)} 条",
            f"隐私发现：{privacy.get('summary', {}).get('effective_findings_count', 0)} 条",
            "",
            "警告详情：",
        ]
        for item in warnings.get("items", [])[:40]:
            lines.append(f"- {item.get('code', '')}: {item.get('message', '')}")
        findings = privacy.get("findings", [])
        if findings:
            lines.extend(["", "隐私发现："])
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
        integration = codex_integration_status(
            self.config.resolved_codex_home,
            self.config.resolved_db_path,
        )
        hook = integration["hook"]
        mcp = integration["mcp"]
        freshness = integration["source_freshness"]
        schedule = _automation_schedule(self.config.resolved_codex_home, self.config.automation_id)
        freshness_text = "已同步" if freshness["fresh"] else f"待补导 {freshness['pending_files']} 个文件"
        lines = [
            f"Codex MCP：{'配置正确' if mcp['matches'] else ('配置已漂移' if mcp['configured'] else '未安装')}",
            f"自动入库 Hook：{'配置正确' if hook['matches'] else ('配置已漂移' if hook['configured'] else '未安装')}",
            f"Hook 实际记录：{'已覆盖最新源会话' if hook['activity']['current'] else '未覆盖最新源变化，请在 /hooks 检查信任'}",
            f"归档新鲜度：{freshness_text}",
            f"每日智能备份：{schedule['label']}",
            "",
            f"ThreadVault 提供 {len(tools)} 个只读 MCP 工具，可检索历史、查看会话、诊断和预览导出。",
            "MCP 不会修改归档，也不会自动上传会话。",
            "",
            "可用工具：",
        ]
        for tool in tools:
            lines.append(f"- {tool.get('name', '')}")
        if integration["healthy"]:
            status = "Codex 联动与归档均正常"
        elif integration["ok"]:
            status = "Codex 已配置，但仍需完成信任或归档补导"
        else:
            status = "Codex 联动需要重新安装"
        return DesktopTextResult(title="MCP 联动", text="\n".join(lines), status=status)

    def install_codex(self, *, apply: bool = True) -> DesktopTextResult:
        payload = install_codex_integration(
            self.config.resolved_codex_home,
            self.config.resolved_db_path,
            apply=apply,
        )
        hook = payload["hook"]
        mcp = payload["mcp"]
        lines = [
            f"Hook：{hook['action']}",
            f"MCP：{mcp['action']}",
            f"配置模式：{'已应用' if apply else '仅预览'}",
        ]
        if payload["hook_trust_required"]:
            lines.append("请在 Codex 中打开 /hooks，检查并信任 ThreadVault Stop Hook。")
        elif not payload["status"]["hook"]["activity"]["observed"]:
            lines.append("尚未观察到 Hook 运行记录；请在 /hooks 检查它是否已信任。")
        if payload["restart_required"]:
            lines.append("请重启 Codex，使新 MCP 配置生效。")
        return DesktopTextResult(
            title="Codex 一键联动",
            text="\n".join(lines),
            status="Codex 联动已安装" if payload["ok"] and apply else "Codex 联动安装预览",
        )

    def health_summary(self) -> DesktopTextResult:
        stats = self.store.stats()
        doctor = self.store.doctor()
        freshness = self.store.storage_sync(codex_home=self.config.resolved_codex_home, apply=False)
        healthy = bool(doctor.get("ok") and freshness["fresh"])
        lines = [
            f"总体状态：{'健康' if healthy else '需要处理'}",
            f"数据库：{self.config.resolved_db_path}",
            f"会话：{stats.get('sessions', 0)}　事件：{stats.get('events', 0)}　警告：{stats.get('warnings', 0)}",
            f"源会话：{freshness['source_files']} 个　待补导：{freshness['pending_files']} 个",
            f"Python：{doctor.get('python', '')}",
            "",
            "检查项目：",
        ]
        for check in doctor.get("checks", []):
            lines.append(f"- {'通过' if check.get('ok') else '失败'}：{check.get('name', '')} — {check.get('message', '')}")
        suggestions = doctor.get("maintenance_suggestions", [])
        if not freshness["fresh"]:
            suggestions = [f"运行智能备份或 storage sync --apply，先补导 {freshness['pending_files']} 个源会话文件。", *suggestions]
        lines.extend(["", "维护建议："])
        lines.extend(f"- {item}" for item in suggestions)
        if not suggestions:
            lines.append("- 当前没有必须执行的维护操作。")
        return DesktopTextResult(
            title="健康诊断",
            text="\n".join(lines),
            status="诊断通过" if healthy else "诊断发现问题",
        )

    def backup_center_status(self, out_root: str | Path | None = None) -> DesktopBackupCenter:
        root = Path(out_root).expanduser() if out_root else self.config.resolved_backup_root
        plan = self.store.storage_auto_backup(
            out_root=root,
            cold_root=self.config.cold_root,
            codex_home=self.config.resolved_codex_home,
            apply=False,
        )
        schedule = _automation_schedule(self.config.resolved_codex_home, self.config.automation_id)
        last_run = _last_backup_run(root)
        action = str(plan.get("action") or "unknown")
        profile = plan.get("profile")
        if action == "sync":
            pending = (plan.get("source_sync") or {}).get("pending_files", 0)
            headline = f"有 {pending} 个会话文件等待入库"
            detail = "点击立即智能备份后会先补齐归档，再重新判断是否需要创建并验证新备份。"
        elif action == "skip":
            headline = "备份状态正常"
            detail = "当前备份仍新鲜，或归档内容没有需要创建新副本的变化。"
        elif action == "backup":
            headline = f"需要创建{_profile_label(profile)}备份"
            detail = _backup_reason(plan.get("reason"))
        else:
            headline = "备份需要处理"
            detail = _backup_reason(plan.get("reason"))
        disk = plan.get("disk") or {}
        enough = bool(disk.get("enough", True))
        if not enough:
            headline = "磁盘空间不足，已阻止备份"
        latest = plan.get("latest") or {}
        latest_core = latest.get("core") or {}
        disk_text = (
            f"磁盘：可用 {_format_bytes(disk.get('free_bytes', 0))}，"
            f"本次预计 {_format_bytes(disk.get('required_bytes', 0))}，"
            f"安全余量 {_format_bytes(disk.get('reserve_bytes', 0))}"
        )
        text = "\n".join([
            headline,
            detail,
            "",
            f"最近可用备份：{_profile_label(latest_core.get('profile')) if latest_core else '尚无'}",
            f"最近自动检查：{last_run}",
            f"自动计划：{schedule['label']}",
            f"下次运行：{schedule['next_run']}",
            disk_text,
            f"备份目录：{root}",
            "",
            "保留策略：核心 3 份、证据 2 份、取证 1 份；手动备份不会被自动清理。",
        ])
        return DesktopBackupCenter(
            headline=headline,
            detail=detail,
            last_run=last_run,
            next_run=schedule["next_run"],
            schedule=schedule["label"],
            disk=f"可用 {_format_bytes(disk.get('free_bytes', 0))} / 预计 {_format_bytes(disk.get('required_bytes', 0))}",
            out_root=str(root),
            action=action,
            profile=str(profile) if profile else None,
            can_run=enough,
            text=text,
            status=headline,
        )

    def run_smart_backup(self, out_root: str | Path | None = None) -> DesktopTextResult:
        root = Path(out_root).expanduser() if out_root else self.config.resolved_backup_root
        payload = self.store.storage_auto_backup(
            out_root=root,
            cold_root=self.config.cold_root,
            codex_home=self.config.resolved_codex_home,
            apply=True,
        )
        action = payload.get("action")
        if action == "created":
            backup = payload.get("backup") or {}
            status = f"{_profile_label(payload.get('profile'))}备份已创建并验证"
            lines = [status, f"清单：{backup.get('manifest', '')}"]
        elif action == "skip":
            status = "无需创建新备份"
            lines = [status, "已有备份仍新鲜或归档内容没有变化。"]
        else:
            status = "智能备份未完成"
            lines = [status, f"原因：{_backup_reason(payload.get('reason'))}"]
        return DesktopTextResult("智能备份", "\n".join(lines), status)

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
                text=f"目标数据库已经存在。为防止覆盖，桌面版拒绝执行恢复：\n{target}",
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
            "这里提供面向维护者的结构定义和机器人说明。日常归档、检索和备份不需要使用本页。",
            "",
            "“查看结构定义”和“查看机器人说明”不会写入文件。",
            "“导出全部结构定义”会在确认后写入所选目录。",
        ]
        return DesktopTextResult(title="高级", text="\n".join(lines), status="高级维护入口已就绪")

    def _state_index(self) -> dict[str, dict[str, Any]]:
        """Reuse friendly local titles only while their SQLite inputs are unchanged."""

        signature = _state_index_signature(self.config.resolved_codex_home)
        if signature != self._state_index_signature:
            self._state_index_cache = load_state_thread_index(self.config.resolved_codex_home)
            self._state_index_signature = signature
        return self._state_index_cache


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
            "smart_backup_center": True,
            "confirmed_export": True,
            "friendly_session_titles": True,
            "directory_pickers": True,
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


def _session_row(item: dict[str, Any], thread_index: dict[str, dict[str, Any]]) -> DesktopSessionRow:
    session_id = str(item.get("session_id") or "")
    state = thread_index.get(session_id, {})
    project = _project_name(item.get("cwd") or state.get("cwd"))
    return DesktopSessionRow(
        session_id=session_id,
        title=_friendly_title(state.get("title"), project) or f"{project} 会话",
        project=project,
        cwd=str(item.get("cwd") or ""),
        updated_at=str(item.get("updated_at") or item.get("first_seen_at") or ""),
        event_count=int(item.get("event_count") or 0),
        warning_count=int(item.get("warning_count") or 0),
    )


def _search_results(overview: dict[str, Any]) -> list[dict[str, Any]]:
    search = overview.get("search") or {}
    results = search.get("results")
    return results if isinstance(results, list) else []


def _search_row(
    item: dict[str, Any],
    thread_index: dict[str, dict[str, Any]],
    session_index: dict[str, DesktopSessionRow],
) -> DesktopSearchRow:
    session_id = str(item.get("session_id") or "")
    session = session_index.get(session_id)
    state = thread_index.get(session_id, {})
    project = session.project if session else _project_name(state.get("cwd"))
    return DesktopSearchRow(
        session_id=session_id,
        title=session.title if session else (_friendly_title(state.get("title"), project) or f"{project} 会话"),
        project=project,
        score=str(item.get("score") or ""),
        preview=str(item.get("snippet") or item.get("text") or item.get("summary") or ""),
    )


def _status_text(session_count: int, result_count: int, has_query: bool) -> str:
    if has_query:
        return f"搜索结果 {result_count} 条，归档会话 {session_count} 条"
    return f"归档会话 {session_count} 条"


def _tkinter_available() -> bool:
    return importlib.util.find_spec("tkinter") is not None


def _state_index_signature(codex_home: Path) -> tuple[tuple[str, int | None, int | None], ...]:
    """Return a cheap invalidation signature for Codex state SQLite and its WAL files."""

    signatures: list[tuple[str, int | None, int | None]] = []
    for database in state_candidates(codex_home):
        for candidate in (database, database.with_name(f"{database.name}-wal"), database.with_name(f"{database.name}-shm")):
            try:
                stat = candidate.stat()
            except OSError:
                signatures.append((str(candidate), None, None))
            else:
                signatures.append((str(candidate), stat.st_mtime_ns, stat.st_size))
    return tuple(signatures)


def _manifest_status(manifest: Any) -> str:
    if not manifest:
        return "none"
    if isinstance(manifest, dict):
        return f"ok={manifest.get('ok')} path={manifest.get('path') or manifest.get('manifest') or ''}"
    return str(manifest)


def _pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


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


def _session_card_summary(row: DesktopSessionRow) -> str:
    return "\n".join([
        row.title,
        f"项目：{row.project}",
        f"最近更新：{_friendly_time(row.updated_at)}",
        f"事件：{row.event_count}　警告：{row.warning_count}",
    ])


def _friendly_title(value: Any, project: str) -> str:
    text = " ".join(str(value or "").split()).strip(" #")
    if not text:
        return ""
    lowered = text.lower()
    if (
        "agents.md instructions" in lowered
        or lowered.startswith("codex://threads/")
        or text.startswith("[$")
        or "<instructions>" in lowered
        or re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", lowered)
    ):
        return ""
    if len(text) > 58:
        text = f"{text[:57].rstrip()}…"
    return text or f"{project} 会话"


def _project_name(value: Any) -> str:
    text = str(value or "").replace("\\\\?\\", "").rstrip("\\/")
    if not text:
        return "未分类项目"
    name = PureWindowsPath(text).name
    return name or text


def _friendly_time(value: Any) -> str:
    text = str(value or "")
    if len(text) >= 16:
        return text[:10] + " " + text[11:16]
    return text or "未知"


def _profile_label(profile: Any) -> str:
    return {
        "core": "核心",
        "evidence": "证据",
        "forensic": "取证",
        "markdown": "Markdown 文档",
        "obsidian": "Obsidian 知识库",
        "skill": "Codex Skill",
    }.get(str(profile or ""), str(profile or "未知"))


def _privacy_label(mode: str) -> str:
    return {
        "warn": "提示风险后继续",
        "redact": "自动脱敏",
        "fail": "发现风险则阻止",
    }.get(mode, mode)


def _backup_reason(value: Any) -> str:
    return {
        "bootstrap_evidence": "尚无备份基线，需要建立第一份证据备份。",
        "daily_core_due": "归档有变化，且每日核心备份已经到期。",
        "weekly_evidence_due": "归档有变化，且每周证据备份已经到期。",
        "monthly_forensic_due": "归档有变化，且每月取证备份已经到期。",
        "fresh_or_unchanged": "已有备份仍新鲜，或归档内容没有变化。",
        "source_sync_required": "源会话比归档更新，需要先自动补导。",
        "source_sync_failed": "源会话补导没有完整通过，已阻止备份。",
        "insufficient_disk_space": "可用磁盘空间不足，系统已安全阻止写入。",
        "backup_already_running": "另一个智能备份正在运行。",
    }.get(str(value or ""), str(value or "未知原因"))


def _format_bytes(value: Any) -> str:
    size = float(value or 0)
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{int(value or 0)} B"


def _last_backup_run(root: Path) -> str:
    path = root / "auto" / "last-run.json"
    if not path.is_file():
        return "尚无自动运行记录"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        action = payload.get("action")
        suffix = {
            "created": "已创建备份",
            "skip": "检查正常，无需新备份",
            "blocked": "已阻止",
        }.get(action, str(action or "状态未知"))
        stamp = datetime.fromtimestamp(path.stat().st_mtime).astimezone().strftime("%Y-%m-%d %H:%M")
        return f"{stamp}（{suffix}）"
    except (OSError, ValueError, json.JSONDecodeError):
        return "运行记录不可读取"


def _automation_schedule(codex_home: Path, automation_id: str) -> dict[str, str]:
    path = codex_home / "automations" / automation_id / "automation.toml"
    if not path.is_file():
        return {"label": "未检测到自动任务", "next_run": "未计划"}
    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
        if str(payload.get("status", "")).upper() != "ACTIVE":
            return {"label": "自动任务已暂停", "next_run": "未计划"}
        rrule = str(payload.get("rrule") or "")
        hour_match = re.search(r"(?:^|;)BYHOUR=(\d{1,2})(?:;|$)", rrule)
        minute_match = re.search(r"(?:^|;)BYMINUTE=(\d{1,2})(?:;|$)", rrule)
        hour = int(hour_match.group(1)) if hour_match else 3
        minute = int(minute_match.group(1)) if minute_match else 15
        now = datetime.now().astimezone()
        upcoming = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if upcoming <= now:
            upcoming += timedelta(days=1)
        return {
            "label": f"每天 {hour:02d}:{minute:02d}（Codex 本地任务）",
            "next_run": upcoming.strftime("%Y-%m-%d %H:%M"),
        }
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        return {"label": "自动任务配置不可读取", "next_run": "未知"}

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import BOTH, END, LEFT, RIGHT, Listbox, StringVar, TclError, Text, Tk, X, messagebox, ttk
from typing import TypeVar

from .desktop_data import DesktopAppConfig, DesktopDataGateway, DesktopSnapshot, DesktopTextResult, build_desktop_gateway

T = TypeVar("T")


@dataclass(frozen=True)
class DesktopAppTheme:
    font_family: str = "Segoe UI"
    font_size: int = 10
    window_width: int = 860
    window_height: int = 520


class ThreadVaultDesktopApp:
    """Minimal native desktop shell over the desktop data gateway."""

    def __init__(self, gateway: DesktopDataGateway, theme: DesktopAppTheme | None = None) -> None:
        self.gateway = gateway
        self.theme = theme or DesktopAppTheme()
        self.root = Tk()
        self.query = StringVar()
        self.status = StringVar(value="启动中")
        self.selected_session = StringVar()
        self.export_out = StringVar(value="threadvault-desktop-export")
        self.export_profile = StringVar(value="markdown")
        self.privacy_mode = StringVar(value="warn")
        self.backup_out = StringVar(value="threadvault-desktop-backups")
        self.backup_file = StringVar()
        self.restore_target = StringVar(value=str(self.gateway.config.resolved_db_path))
        self.schema_name = StringVar(value="search_minimal")
        self.schema_out = StringVar(value="threadvault-desktop-schemas")
        self.busy = False
        self.session_ids: list[str] = []
        self.search_ids: list[str] = []
        self.buttons: list[ttk.Button] = []
        self._configure_root()
        self._build_widgets()
        self.show_advanced()
        self._render_text_result(self.gateway.integration_summary(), self.integration_text)
        self.root.after(0, self.refresh)

    def run(self) -> None:
        self.root.mainloop()

    def refresh(self) -> None:
        query = self.query.get().strip()
        self._load_async("正在加载", lambda: self.gateway.snapshot(query=query), self._render_snapshot)

    def open_selected(self) -> None:
        selection = self.session_list.curselection()
        if not selection:
            return
        self._open_session(self.session_ids[selection[0]])

    def open_search_selected(self) -> None:
        selection = self.result_list.curselection()
        if not selection:
            return
        self._open_session(self.search_ids[selection[0]])

    def preview_export(self) -> None:
        session_id = self.selected_session.get().strip()
        if not session_id:
            self.status.set("先选择一个会话")
            return
        out_dir = self.export_out.get().strip()
        profile = self.export_profile.get()
        privacy_mode = self.privacy_mode.get()
        self._load_async(
            "正在生成导出预览",
            lambda: self.gateway.export_preview(
                session_id=session_id,
                out_dir=out_dir,
                profile=profile,
                privacy_mode=privacy_mode,
            ),
            lambda result: self._render_text_result(result, self.export_text),
        )

    def show_warnings(self) -> None:
        session_id = self.selected_session.get().strip()
        if not session_id:
            self.status.set("先选择一个会话")
            return
        self._load_async(
            "正在检查隐私告警",
            lambda: self.gateway.warnings_summary(session_id),
            lambda result: self._render_text_result(result, self.safety_text),
        )

    def create_backup(self) -> None:
        if not self._confirm("备份会写入本地 .db 文件和 manifest，是否继续？"):
            return
        out = self.backup_out.get().strip()
        self._load_async(
            "正在备份",
            lambda: self.gateway.backup_database(out),
            lambda result: self._render_backup_result(result),
        )

    def verify_backup(self) -> None:
        backup = self.backup_file.get().strip()
        if not backup:
            self.status.set("先填写备份文件路径")
            return
        self._load_async(
            "正在验证备份",
            lambda: self.gateway.verify_backup(backup),
            lambda result: self._render_text_result(result, self.safety_text),
        )

    def plan_restore(self) -> None:
        backup = self.backup_file.get().strip()
        if not backup:
            self.status.set("先填写备份文件路径")
            return
        target = self.restore_target.get().strip()
        self._load_async(
            "正在生成恢复预检",
            lambda: self.gateway.restore_plan(backup, target),
            lambda result: self._render_text_result(result, self.safety_text),
        )

    def apply_restore(self) -> None:
        backup = self.backup_file.get().strip()
        target = self.restore_target.get().strip()
        if not backup:
            self.status.set("先填写备份文件路径")
            return
        if not target:
            self.status.set("先填写目标库路径")
            return
        if not self._confirm("仅恢复到不存在的新目标库；不会覆盖现有数据库。是否继续？"):
            return
        self._load_async(
            "正在执行恢复",
            lambda: self.gateway.restore_to_new_target(backup, target),
            lambda result: self._render_text_result(result, self.safety_text),
        )

    def show_integrations(self) -> None:
        self._load_async(
            "正在读取 MCP 联动",
            self.gateway.integration_summary,
            lambda result: self._render_text_result(result, self.integration_text),
        )

    def show_health(self) -> None:
        self._load_async("正在诊断", self.gateway.health_summary, lambda result: self._render_text_result(result, self.health_text))

    def reindex_search(self) -> None:
        if not self._confirm("重建 FTS 搜索索引可能需要一点时间，是否继续？"):
            return
        self._load_async(
            "正在重建索引",
            self.gateway.reindex_search,
            lambda result: self._render_text_result(result, self.health_text),
        )

    def vacuum_database(self) -> None:
        if not self._confirm("数据库压缩会写入当前 SQLite 文件，是否继续？"):
            return
        self._load_async(
            "正在压缩数据库",
            self.gateway.vacuum_database,
            lambda result: self._render_text_result(result, self.health_text),
        )

    def show_advanced(self) -> None:
        self._render_text_result(self.gateway.advanced_summary(), self.advanced_text)

    def show_schema(self) -> None:
        schema_name = self.schema_name.get().strip()
        self._load_async(
            "正在读取结构定义",
            lambda: self.gateway.schema_summary(schema_name),
            lambda result: self._render_text_result(result, self.advanced_text),
        )

    def show_robot_docs(self) -> None:
        self._load_async(
            "正在读取机器人文档",
            self.gateway.robot_docs_summary,
            lambda result: self._render_text_result(result, self.advanced_text),
        )

    def show_governance(self) -> None:
        self._load_async(
            "正在读取治理状态",
            self.gateway.governance_summary,
            lambda result: self._render_text_result(result, self.advanced_text),
        )

    def show_governance_diagnostics(self) -> None:
        self._load_async(
            "正在读取治理诊断",
            self.gateway.governance_diagnostics_summary,
            lambda result: self._render_text_result(result, self.advanced_text),
        )

    def write_schemas(self) -> None:
        if not self._confirm("写出 JSON Schema 文件到本地目录，是否继续？"):
            return
        out_dir = self.schema_out.get().strip()
        self._load_async(
            "正在写出结构定义",
            lambda: self.gateway.write_schemas(out_dir),
            lambda result: self._render_text_result(result, self.advanced_text),
        )

    def _open_session(self, session_id: str) -> None:
        self.selected_session.set(session_id)
        self._load_async(
            f"正在打开 {session_id}",
            lambda: self.gateway.session_summary(session_id),
            lambda summary: self._render_summary(session_id, summary),
        )

    def _render_snapshot(self, snapshot: DesktopSnapshot) -> None:
        self.session_ids = [row.session_id for row in snapshot.sessions]
        self.session_list.delete(0, END)
        for row in snapshot.sessions:
            warning = f" W{row.warning_count}" if row.warning_count else ""
            label = f"{row.updated_at[:16]}  {row.event_count:>5}{warning:>5}  {row.session_id}"
            self.session_list.insert(END, label)
        self.search_ids = [row.session_id for row in snapshot.search_rows]
        self.result_list.delete(0, END)
        for row in snapshot.search_rows:
            label = f"{row.score}  {row.session_id}  {row.preview[:96]}"
            self.result_list.insert(END, label)
        if not snapshot.search_rows:
            self.result_list.insert(END, "没有搜索结果" if snapshot.has_query else "输入关键词后显示搜索结果")
        if snapshot.selected_session_id:
            self.selected_session.set(snapshot.selected_session_id)
        self.summary.delete("1.0", END)
        self.summary.insert(END, snapshot.selected_summary or "暂无会话摘要")
        self.status.set(f"{snapshot.status}    DB: {snapshot.db_path}")

    def _render_summary(self, session_id: str, summary: str) -> None:
        self.summary.delete("1.0", END)
        self.summary.insert(END, summary)
        self.status.set(f"已打开 {session_id}")

    def _render_text_result(self, result: DesktopTextResult, widget: Text) -> None:
        widget.delete("1.0", END)
        widget.insert(END, result.text)
        self.status.set(result.status)

    def _render_backup_result(self, result: DesktopTextResult) -> None:
        self._render_text_result(result, self.safety_text)
        for line in result.text.splitlines():
            if line.startswith("Destination: "):
                self.backup_file.set(line.removeprefix("Destination: ").strip())
                break

    def _confirm(self, message: str) -> bool:
        return bool(messagebox.askyesno("ThreadVault", message, parent=self.root))

    def _load_async(self, label: str, work: Callable[[], T], apply_result: Callable[[T], None]) -> None:
        if self.busy:
            return
        self._set_busy(True, label)

        def runner() -> None:
            try:
                result = work()
            except Exception as exc:  # noqa: BLE001 - surface local runtime errors in the desktop shell.
                self.root.after(0, lambda error=exc: self._show_error(error))
                return
            self.root.after(0, lambda: self._finish_load(apply_result, result))

        threading.Thread(target=runner, daemon=True).start()

    def _finish_load(self, apply_result: Callable[[T], None], result: T) -> None:
        try:
            apply_result(result)
        finally:
            self._set_busy(False)

    def _show_error(self, exc: Exception) -> None:
        self.status.set(f"失败: {exc}")
        self._set_busy(False)

    def _set_busy(self, busy: bool, label: str | None = None) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        for button in self.buttons:
            button.configure(state=state)
        if label:
            self.status.set(label)

    def _configure_root(self) -> None:
        self.root.title("ThreadVault")
        self.root.geometry(f"{self.theme.window_width}x{self.theme.window_height}")
        self.root.minsize(720, 420)
        self.root.option_add("*Font", (self.theme.font_family, self.theme.font_size))
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except TclError:
            pass
        style.configure("TButton", padding=(8, 3))
        style.configure("TEntry", padding=(4, 2))
        style.configure("TLabelframe", padding=5)
        style.configure("TNotebook.Tab", padding=(10, 4))

    def _build_widgets(self) -> None:
        self._build_topbar()
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=8, pady=(0, 6))
        self._build_browse_tab()
        self._build_export_tab()
        self._build_safety_tab()
        self._build_integration_tab()
        self._build_health_tab()
        self._build_advanced_tab()
        bottom = ttk.Frame(self.root, padding=(8, 0, 8, 6))
        bottom.pack(fill=X)
        ttk.Label(bottom, textvariable=self.status).pack(side=LEFT, fill=X, expand=True)

    def _build_topbar(self) -> None:
        top = ttk.Frame(self.root, padding=(8, 6))
        top.pack(fill=X)
        ttk.Label(top, text="搜索").pack(side=LEFT)
        entry = ttk.Entry(top, textvariable=self.query, width=46)
        entry.pack(side=LEFT, fill=X, expand=True, padx=(6, 6))
        entry.bind("<Return>", lambda _event: self.refresh())
        search_button = ttk.Button(top, text="搜索", command=self.refresh)
        search_button.pack(side=LEFT)
        refresh_button = ttk.Button(top, text="刷新", command=self.refresh)
        refresh_button.pack(side=LEFT, padx=(6, 0))
        self.buttons.extend([search_button, refresh_button])

    def _build_browse_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="浏览")
        body = ttk.PanedWindow(tab, orient="horizontal")
        body.pack(fill=BOTH, expand=True)
        left = ttk.Labelframe(body, text="会话")
        self.session_list = Listbox(left, height=16, activestyle="dotbox", exportselection=False)
        self.session_list.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.session_list.bind("<Double-Button-1>", lambda _event: self.open_selected())
        body.add(left, weight=2)
        right = ttk.PanedWindow(body, orient="vertical")
        search_frame = ttk.Labelframe(right, text="搜索结果")
        self.result_list = Listbox(search_frame, height=7, activestyle="dotbox", exportselection=False)
        self.result_list.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.result_list.bind("<Double-Button-1>", lambda _event: self.open_search_selected())
        right.add(search_frame, weight=1)
        summary_frame = ttk.Labelframe(right, text="摘要")
        self.summary = Text(summary_frame, height=8, wrap="word")
        self.summary.pack(fill=BOTH, expand=True, padx=5, pady=5)
        right.add(summary_frame, weight=1)
        body.add(right, weight=3)
        open_button = ttk.Button(tab, text="打开会话", command=self.open_selected)
        open_button.pack(side=RIGHT, pady=(6, 0))
        self.buttons.append(open_button)

    def _build_export_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="导出")
        controls = ttk.Frame(tab)
        controls.pack(fill=X, pady=(0, 6))
        ttk.Label(controls, text="会话").pack(side=LEFT)
        ttk.Entry(controls, textvariable=self.selected_session, width=28).pack(side=LEFT, padx=(5, 10))
        ttk.Label(controls, text="格式").pack(side=LEFT)
        ttk.Combobox(controls, textvariable=self.export_profile, values=("markdown", "obsidian", "skill"), width=10, state="readonly").pack(
            side=LEFT,
            padx=(5, 10),
        )
        ttk.Label(controls, text="隐私").pack(side=LEFT)
        ttk.Combobox(controls, textvariable=self.privacy_mode, values=("warn", "redact", "fail"), width=8, state="readonly").pack(
            side=LEFT,
            padx=(5, 10),
        )
        preview_button = ttk.Button(controls, text="预览", command=self.preview_export)
        preview_button.pack(side=RIGHT)
        self.buttons.append(preview_button)
        out_row = ttk.Frame(tab)
        out_row.pack(fill=X, pady=(0, 6))
        ttk.Label(out_row, text="输出目录").pack(side=LEFT)
        ttk.Entry(out_row, textvariable=self.export_out).pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        self.export_text = Text(tab, height=18, wrap="none")
        self.export_text.pack(fill=BOTH, expand=True)

    def _build_safety_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="安全")
        controls = ttk.Frame(tab)
        controls.pack(fill=X, pady=(0, 6))
        ttk.Label(controls, text="会话").pack(side=LEFT)
        ttk.Entry(controls, textvariable=self.selected_session, width=36).pack(side=LEFT, padx=(5, 8))
        button = ttk.Button(controls, text="检查", command=self.show_warnings)
        button.pack(side=LEFT)
        self.buttons.append(button)
        backup_row = ttk.Frame(tab)
        backup_row.pack(fill=X, pady=(0, 6))
        ttk.Label(backup_row, text="备份目录").pack(side=LEFT)
        ttk.Entry(backup_row, textvariable=self.backup_out).pack(side=LEFT, fill=X, expand=True, padx=(5, 8))
        backup_button = ttk.Button(backup_row, text="备份", command=self.create_backup)
        backup_button.pack(side=LEFT)
        self.buttons.append(backup_button)
        restore_row = ttk.Frame(tab)
        restore_row.pack(fill=X, pady=(0, 6))
        ttk.Label(restore_row, text="备份文件").pack(side=LEFT)
        ttk.Entry(restore_row, textvariable=self.backup_file).pack(side=LEFT, fill=X, expand=True, padx=(5, 8))
        verify_button = ttk.Button(restore_row, text="验证", command=self.verify_backup)
        verify_button.pack(side=LEFT)
        plan_button = ttk.Button(restore_row, text="恢复预检", command=self.plan_restore)
        plan_button.pack(side=LEFT, padx=(6, 0))
        apply_button = ttk.Button(restore_row, text="执行恢复", command=self.apply_restore)
        apply_button.pack(side=LEFT, padx=(6, 0))
        self.buttons.extend([verify_button, plan_button, apply_button])
        target_row = ttk.Frame(tab)
        target_row.pack(fill=X, pady=(0, 6))
        ttk.Label(target_row, text="目标库").pack(side=LEFT)
        ttk.Entry(target_row, textvariable=self.restore_target).pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        self.safety_text = Text(tab, height=18, wrap="word")
        self.safety_text.pack(fill=BOTH, expand=True)

    def _build_integration_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="MCP")
        button = ttk.Button(tab, text="刷新", command=self.show_integrations)
        button.pack(anchor="e", pady=(0, 6))
        self.buttons.append(button)
        self.integration_text = Text(tab, height=18, wrap="word")
        self.integration_text.pack(fill=BOTH, expand=True)

    def _build_health_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="健康")
        controls = ttk.Frame(tab)
        controls.pack(fill=X, pady=(0, 6))
        button = ttk.Button(controls, text="诊断", command=self.show_health)
        button.pack(side=RIGHT)
        reindex_button = ttk.Button(controls, text="重建索引", command=self.reindex_search)
        reindex_button.pack(side=RIGHT, padx=(0, 6))
        vacuum_button = ttk.Button(controls, text="压缩数据库", command=self.vacuum_database)
        vacuum_button.pack(side=RIGHT, padx=(0, 6))
        self.buttons.extend([button, reindex_button, vacuum_button])
        self.health_text = Text(tab, height=18, wrap="word")
        self.health_text.pack(fill=BOTH, expand=True)

    def _build_advanced_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="高级")
        controls = ttk.Frame(tab)
        controls.pack(fill=X, pady=(0, 6))
        ttk.Label(controls, text="Schema").pack(side=LEFT)
        ttk.Entry(controls, textvariable=self.schema_name, width=24).pack(side=LEFT, padx=(5, 8))
        schema_button = ttk.Button(controls, text="结构定义", command=self.show_schema)
        schema_button.pack(side=LEFT)
        robot_button = ttk.Button(controls, text="机器人文档", command=self.show_robot_docs)
        robot_button.pack(side=LEFT, padx=(6, 0))
        governance_row = ttk.Frame(tab)
        governance_row.pack(fill=X, pady=(0, 6))
        ttk.Label(governance_row, text="治理").pack(side=LEFT)
        governance_button = ttk.Button(governance_row, text="治理状态", command=self.show_governance)
        governance_button.pack(side=LEFT, padx=(5, 0))
        governance_diagnostics_button = ttk.Button(governance_row, text="治理诊断", command=self.show_governance_diagnostics)
        governance_diagnostics_button.pack(side=LEFT, padx=(6, 0))
        self.buttons.extend([schema_button, robot_button, governance_button, governance_diagnostics_button])
        write_row = ttk.Frame(tab)
        write_row.pack(fill=X, pady=(0, 6))
        ttk.Label(write_row, text="输出目录").pack(side=LEFT)
        ttk.Entry(write_row, textvariable=self.schema_out).pack(side=LEFT, fill=X, expand=True, padx=(5, 8))
        write_button = ttk.Button(write_row, text="写出结构定义", command=self.write_schemas)
        write_button.pack(side=LEFT)
        self.buttons.append(write_button)
        self.advanced_text = Text(tab, height=18, wrap="word")
        self.advanced_text.pack(fill=BOTH, expand=True)


def launch_desktop_app(config: DesktopAppConfig) -> None:
    app = ThreadVaultDesktopApp(build_desktop_gateway(config))
    app.run()

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, StringVar, TclError, Text, Tk, filedialog, messagebox, ttk
from typing import TypeVar

from .desktop_data import (
    DesktopAppConfig,
    DesktopBackupCenter,
    DesktopDataGateway,
    DesktopExportPlan,
    DesktopSnapshot,
    DesktopTextResult,
    build_desktop_gateway,
)

T = TypeVar("T")

EXPORT_PROFILES = {
    "Markdown 文档": "markdown",
    "Obsidian 知识库": "obsidian",
    "Codex Skill": "skill",
}
PRIVACY_MODES = {
    "提示风险后继续": "warn",
    "自动脱敏": "redact",
    "发现风险则阻止": "fail",
}


@dataclass(frozen=True)
class DesktopAppTheme:
    font_family: str = "Segoe UI"
    font_size: int = 10
    window_width: int = 1080
    window_height: int = 700


class ThreadVaultDesktopApp:
    """Native desktop shell over the desktop workflow gateway."""

    def __init__(self, gateway: DesktopDataGateway, theme: DesktopAppTheme | None = None) -> None:
        self.gateway = gateway
        self.theme = theme or DesktopAppTheme()
        self.root = Tk()
        self.query = StringVar()
        self.status = StringVar(value="正在启动")
        self.selected_session = StringVar()
        self.selected_session_label = StringVar(value="尚未选择会话")
        self.export_out = StringVar(value="threadvault-desktop-export")
        self.export_profile = StringVar(value="Markdown 文档")
        self.privacy_mode = StringVar(value="提示风险后继续")
        self.smart_backup_out = StringVar(value=str(self.gateway.config.resolved_backup_root))
        self.backup_out = StringVar(value=str(self.gateway.config.resolved_backup_root / "manual"))
        self.backup_file = StringVar()
        self.restore_target = StringVar(value=str(self.gateway.config.recommended_restore_target))
        self.schema_name = StringVar(value="search_minimal")
        self.schema_out = StringVar(value="threadvault-desktop-schemas")
        self.backup_headline = StringVar(value="正在读取备份状态")
        self.backup_last_run = StringVar(value="—")
        self.backup_next_run = StringVar(value="—")
        self.backup_schedule = StringVar(value="—")
        self.backup_disk = StringVar(value="—")
        self.health_headline = StringVar(value="打开本页后自动诊断")
        self.busy = False
        self.buttons: list[ttk.Button] = []
        self.session_rows: dict[str, object] = {}
        self.search_rows: dict[str, object] = {}
        self.export_plan: DesktopExportPlan | None = None
        self.backup_loaded = False
        self.backup_can_run = True
        self.health_loaded = False
        self._configure_root()
        self._build_widgets()
        self._bind_shortcuts()
        self._bind_export_invalidation()
        self._render_text_result(self.gateway.integration_summary(), self.integration_text)
        self._render_text_result(self.gateway.advanced_summary(), self.advanced_text)
        self.root.after(0, self.refresh)

    def run(self) -> None:
        self.root.mainloop()

    def refresh(self) -> None:
        query = self.query.get().strip()
        self._load_async("正在刷新会话", lambda: self.gateway.snapshot(query=query), self._render_snapshot)

    def open_selected(self) -> None:
        selection = self.session_tree.selection()
        if selection:
            self._open_session(selection[0])

    def open_search_selected(self) -> None:
        selection = self.search_tree.selection()
        if selection and selection[0] in self.search_rows:
            self._open_session(selection[0])

    def use_selected_for_export(self) -> None:
        if not self.selected_session.get().strip():
            self.status.set("请先选择一个会话")
            return
        self.notebook.select(self.export_tab)

    def preview_export(self) -> None:
        session_id = self.selected_session.get().strip()
        if not session_id:
            self.status.set("请先选择一个会话")
            return
        out_dir = self.export_out.get().strip()
        profile = EXPORT_PROFILES[self.export_profile.get()]
        privacy_mode = PRIVACY_MODES[self.privacy_mode.get()]
        self._load_async(
            "正在生成安全预览",
            lambda: self.gateway.prepare_export(
                session_id=session_id,
                out_dir=out_dir,
                profile=profile,
                privacy_mode=privacy_mode,
            ),
            self._render_export_plan,
        )

    def execute_export(self) -> None:
        plan = self.export_plan
        if plan is None or not plan.can_export:
            self.status.set("请先生成可执行的导出预览")
            return
        message = (
            f"将写入 {plan.planned_files} 个文件到：\n{Path(plan.out_dir).resolve()}\n\n"
            f"隐私发现 {plan.privacy_findings} 条，是否按当前预览确认导出？"
        )
        if not self._confirm(message, title="确认导出"):
            return
        self._load_async("正在导出", lambda: self.gateway.execute_export(plan), self._render_export_result)

    def show_warnings(self) -> None:
        session_id = self.selected_session.get().strip()
        if not session_id:
            self.status.set("请先选择一个会话")
            return
        self._load_async(
            "正在扫描当前会话",
            lambda: self.gateway.warnings_summary(session_id),
            lambda result: self._render_text_result(result, self.safety_text),
        )

    def refresh_backup_center(self) -> None:
        out_root = self.smart_backup_out.get().strip()
        self._load_async(
            "正在检查备份状态",
            lambda: self.gateway.backup_center_status(out_root),
            self._render_backup_center,
        )

    def run_smart_backup(self) -> None:
        if not self.backup_can_run:
            self.status.set("当前磁盘空间不足，不能执行智能备份")
            return
        if not self._confirm(
            "ThreadVault 将自动判断备份档位、写入本地备份，并在验证成功后清理超出保留数量的自动旧代。是否继续？",
            title="立即智能备份",
        ):
            return
        out_root = self.smart_backup_out.get().strip()
        self._load_async("正在执行智能备份", lambda: self.gateway.run_smart_backup(out_root), self._render_smart_backup_result)

    def create_backup(self) -> None:
        if not self._confirm("这会创建仅含当前数据库的手动备份。日常使用优先选择智能备份。是否继续？", title="手动备份"):
            return
        out = self.backup_out.get().strip()
        self._load_async("正在创建手动备份", lambda: self.gateway.backup_database(out), self._render_backup_result)

    def verify_backup(self) -> None:
        backup = self.backup_file.get().strip()
        if not backup:
            self.status.set("请先选择备份文件")
            return
        self._load_async(
            "正在验证备份",
            lambda: self.gateway.verify_backup(backup),
            lambda result: self._render_text_result(result, self.safety_text),
        )

    def plan_restore(self) -> None:
        backup = self.backup_file.get().strip()
        if not backup:
            self.status.set("请先选择备份文件")
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
            self.status.set("请先选择备份文件")
            return
        if not target:
            self.status.set("请先选择新的目标数据库")
            return
        if not self._confirm(f"恢复只会写入这个新的数据库：\n{target}\n\n不会覆盖当前归档。是否继续？", title="确认恢复"):
            return
        self._load_async(
            "正在恢复到新数据库",
            lambda: self.gateway.restore_to_new_target(backup, target),
            lambda result: self._render_text_result(result, self.safety_text),
        )

    def show_integrations(self) -> None:
        self._load_async(
            "正在检查 Codex 联动",
            self.gateway.integration_summary,
            lambda result: self._render_text_result(result, self.integration_text),
        )

    def show_health(self) -> None:
        self._load_async("正在诊断", self.gateway.health_summary, self._render_health)

    def reindex_search(self) -> None:
        if not self._confirm("仅在诊断建议时重建搜索索引。操作可能需要一些时间，是否继续？", title="重建搜索索引"):
            return
        self._load_async(
            "正在重建搜索索引",
            self.gateway.reindex_search,
            lambda result: self._render_text_result(result, self.health_text),
        )

    def vacuum_database(self) -> None:
        if not self._confirm("仅在诊断建议时压缩当前数据库。操作会写入 SQLite 文件，是否继续？", title="压缩数据库"):
            return
        self._load_async(
            "正在压缩数据库",
            self.gateway.vacuum_database,
            lambda result: self._render_text_result(result, self.health_text),
        )

    def show_schema(self) -> None:
        schema_name = self.schema_name.get().strip()
        self._load_async(
            "正在读取结构定义",
            lambda: self.gateway.schema_summary(schema_name),
            lambda result: self._render_text_result(result, self.advanced_text),
        )

    def show_robot_docs(self) -> None:
        self._load_async(
            "正在读取机器人说明",
            self.gateway.robot_docs_summary,
            lambda result: self._render_text_result(result, self.advanced_text),
        )

    def write_schemas(self) -> None:
        if not self._confirm("将全部 JSON Schema 写入所选目录，是否继续？", title="导出结构定义"):
            return
        out_dir = self.schema_out.get().strip()
        self._load_async(
            "正在导出结构定义",
            lambda: self.gateway.write_schemas(out_dir),
            lambda result: self._render_text_result(result, self.advanced_text),
        )

    def choose_export_directory(self) -> None:
        self._choose_directory(self.export_out, "选择导出目录")

    def choose_smart_backup_directory(self) -> None:
        if self._choose_directory(self.smart_backup_out, "选择智能备份目录"):
            self.backup_loaded = False
            self.refresh_backup_center()

    def choose_manual_backup_directory(self) -> None:
        self._choose_directory(self.backup_out, "选择手动备份目录")

    def choose_backup_file(self) -> None:
        value = filedialog.askopenfilename(
            parent=self.root,
            title="选择备份数据库",
            filetypes=(("SQLite 数据库", "*.db"), ("所有文件", "*.*")),
        )
        if value:
            self.backup_file.set(value)

    def choose_restore_target(self) -> None:
        value = filedialog.asksaveasfilename(
            parent=self.root,
            title="选择新的恢复目标数据库",
            defaultextension=".db",
            initialfile=Path(self.restore_target.get()).name,
            filetypes=(("SQLite 数据库", "*.db"),),
        )
        if value:
            self.restore_target.set(value)

    def choose_schema_directory(self) -> None:
        self._choose_directory(self.schema_out, "选择结构定义输出目录")

    def _choose_directory(self, variable: StringVar, title: str) -> bool:
        value = filedialog.askdirectory(parent=self.root, title=title, initialdir=variable.get() or ".")
        if value:
            variable.set(value)
            return True
        return False

    def _open_session(self, session_id: str) -> None:
        self._set_selected_session(session_id)
        self._load_async(
            "正在加载会话详情",
            lambda: self.gateway.session_summary(session_id),
            lambda summary: self._render_summary(session_id, summary),
        )

    def _select_session_from_tree(self, tree: ttk.Treeview) -> None:
        selection = tree.selection()
        if selection and selection[0] in {**self.session_rows, **self.search_rows}:
            self._set_selected_session(selection[0])

    def _set_selected_session(self, session_id: str) -> None:
        self.selected_session.set(session_id)
        row = self.session_rows.get(session_id) or self.search_rows.get(session_id)
        title = getattr(row, "title", "当前会话")
        project = getattr(row, "project", "未分类项目")
        self.selected_session_label.set(f"{title}　·　{project}")

    def _render_snapshot(self, snapshot: DesktopSnapshot) -> None:
        self.session_rows = {row.session_id: row for row in snapshot.sessions}
        self.search_rows = {row.session_id: row for row in snapshot.search_rows}
        self.session_tree.delete(*self.session_tree.get_children())
        for row in snapshot.sessions:
            self.session_tree.insert(
                "",
                END,
                iid=row.session_id,
                values=(row.title, row.project, _display_time(row.updated_at), row.event_count, row.warning_count or ""),
            )
        self.search_tree.delete(*self.search_tree.get_children())
        for row in snapshot.search_rows:
            preview = " ".join(row.preview.split())[:120]
            self.search_tree.insert("", END, iid=row.session_id, values=(row.title, row.project, preview))
        self.search_empty.set(
            "" if snapshot.search_rows else ("没有找到匹配内容" if snapshot.has_query else "输入关键词后显示搜索结果")
        )
        if snapshot.selected_session_id:
            self._set_selected_session(snapshot.selected_session_id)
            if snapshot.selected_session_id in self.session_rows:
                self.session_tree.selection_set(snapshot.selected_session_id)
        self._set_text(self.summary, snapshot.selected_summary or "选择会话后查看摘要")
        self.status.set(f"{snapshot.status}　　数据库：{snapshot.db_path}")

    def _render_summary(self, session_id: str, summary: str) -> None:
        self._set_text(self.summary, summary)
        self.status.set(f"已打开：{self.selected_session_label.get()}")

    def _render_export_plan(self, plan: DesktopExportPlan) -> None:
        self.export_plan = plan
        self._set_text(self.export_text, plan.text)
        self.status.set(plan.status)
        self._sync_guarded_buttons()

    def _render_export_result(self, result: DesktopTextResult) -> None:
        self._render_text_result(result, self.export_text)
        self.export_plan = None
        self._sync_guarded_buttons()

    def _render_backup_center(self, center: DesktopBackupCenter) -> None:
        self.backup_loaded = True
        self.backup_can_run = center.can_run
        self.backup_headline.set(center.headline)
        self.backup_last_run.set(center.last_run)
        self.backup_next_run.set(center.next_run)
        self.backup_schedule.set(center.schedule)
        self.backup_disk.set(center.disk)
        self._set_text(self.backup_text, center.text)
        self.status.set(center.status)
        self._sync_guarded_buttons()

    def _render_smart_backup_result(self, result: DesktopTextResult) -> None:
        self._render_text_result(result, self.backup_text)
        self.backup_loaded = False
        self.root.after(100, self.refresh_backup_center)

    def _render_backup_result(self, result: DesktopTextResult) -> None:
        self._render_text_result(result, self.safety_text)
        for line in result.text.splitlines():
            if line.startswith("Destination: "):
                self.backup_file.set(line.removeprefix("Destination: ").strip())
                break

    def _render_health(self, result: DesktopTextResult) -> None:
        self.health_loaded = True
        self.health_headline.set("归档健康" if result.status == "诊断通过" else "归档需要处理")
        self._render_text_result(result, self.health_text)

    def _render_text_result(self, result: DesktopTextResult, widget: Text) -> None:
        self._set_text(widget, result.text)
        self.status.set(result.status)

    @staticmethod
    def _set_text(widget: Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", END)
        widget.insert(END, value)
        widget.configure(state="disabled")

    def _confirm(self, message: str, *, title: str = "ThreadVault") -> bool:
        return bool(messagebox.askyesno(title, message, parent=self.root))

    def _load_async(self, label: str, work: Callable[[], T], apply_result: Callable[[T], None]) -> None:
        if self.busy:
            return
        self._set_busy(True, label)

        def runner() -> None:
            try:
                result = work()
            except Exception as exc:  # noqa: BLE001 - local failures must be visible in the desktop shell.
                self.root.after(0, lambda error=exc: self._show_error(error))
                return
            self.root.after(0, lambda: self._finish_load(apply_result, result))

        threading.Thread(target=runner, daemon=True).start()

    def _finish_load(self, apply_result: Callable[[T], None], result: T) -> None:
        try:
            apply_result(result)
        finally:
            self._set_busy(False)
            self.root.after_idle(self._ensure_current_tab_loaded)

    def _show_error(self, exc: Exception) -> None:
        self.status.set(f"操作失败：{exc}")
        self._set_busy(False)

    def _set_busy(self, busy: bool, label: str | None = None) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        for button in self.buttons:
            button.configure(state=state)
        if busy:
            self.progress.pack(side=RIGHT, padx=(8, 0))
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.pack_forget()
        if label:
            self.status.set(label)
        self._sync_guarded_buttons()

    def _sync_guarded_buttons(self) -> None:
        if hasattr(self, "export_button"):
            allowed = not self.busy and self.export_plan is not None and self.export_plan.can_export
            self.export_button.configure(state="normal" if allowed else "disabled")
        if hasattr(self, "smart_backup_button"):
            allowed = not self.busy and self.backup_can_run
            self.smart_backup_button.configure(state="normal" if allowed else "disabled")

    def _invalidate_export_preview(self, *_args: object) -> None:
        if self.export_plan is not None:
            self.export_plan = None
            self._set_text(self.export_text, "导出参数已变化，请重新生成预览。")
            self.status.set("导出参数已变化，需要重新预览")
        self._sync_guarded_buttons()

    def _on_tab_changed(self, _event: object | None = None) -> None:
        self._ensure_current_tab_loaded()

    def _ensure_current_tab_loaded(self) -> None:
        if self.busy:
            return
        selected = self.notebook.select()
        if selected == str(self.backup_tab) and not self.backup_loaded:
            self.refresh_backup_center()
        elif selected == str(self.health_tab) and not self.health_loaded:
            self.show_health()

    def _configure_root(self) -> None:
        self.root.title("ThreadVault")
        self.root.geometry(f"{self.theme.window_width}x{self.theme.window_height}")
        self.root.minsize(880, 560)
        self.root.option_add("*Font", (self.theme.font_family, self.theme.font_size))
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except TclError:
            pass
        style.configure("TButton", padding=(9, 5))
        style.configure("TEntry", padding=(5, 3))
        style.configure("TLabelframe", padding=7)
        style.configure("TNotebook.Tab", padding=(12, 6))
        style.configure("Heading.TLabel", font=(self.theme.font_family, 14, "bold"))
        style.configure("Hint.TLabel", foreground="#555555")
        style.map("TButton", relief=[("focus", "solid")])

    def _build_widgets(self) -> None:
        self._build_topbar()
        self.notebook = ttk.Notebook(self.root, takefocus=True)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=(0, 8))
        self._build_browse_tab()
        self._build_export_tab()
        self._build_backup_tab()
        self._build_integration_tab()
        self._build_health_tab()
        self._build_advanced_tab()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        bottom = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        bottom.pack(fill="x")
        ttk.Label(bottom, textvariable=self.status).pack(side=LEFT, fill="x", expand=True)
        self.progress = ttk.Progressbar(bottom, mode="indeterminate", length=130)

    def _build_topbar(self) -> None:
        top = ttk.Frame(self.root, padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(top, text="搜索（Ctrl+F）").pack(side=LEFT)
        self.search_entry = ttk.Entry(top, textvariable=self.query, width=46, takefocus=True)
        self.search_entry.pack(side=LEFT, fill="x", expand=True, padx=(8, 8))
        self.search_entry.bind("<Return>", lambda _event: self.refresh())
        search_button = ttk.Button(top, text="搜索", command=self.refresh, takefocus=True)
        search_button.pack(side=LEFT)
        refresh_button = ttk.Button(top, text="刷新（F5）", command=self.refresh, takefocus=True)
        refresh_button.pack(side=LEFT, padx=(8, 0))
        self.buttons.extend([search_button, refresh_button])

    def _build_browse_tab(self) -> None:
        self.browse_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.browse_tab, text="会话")
        body = ttk.PanedWindow(self.browse_tab, orient="horizontal")
        body.pack(fill=BOTH, expand=True)
        sessions = ttk.Labelframe(body, text="最近会话")
        self.session_tree = _scrolled_tree(
            sessions,
            columns=("title", "project", "updated", "events", "warnings"),
            headings=("标题", "项目", "更新时间", "事件", "警告"),
            widths=(300, 130, 120, 70, 60),
        )
        self.session_tree.bind("<<TreeviewSelect>>", lambda _event: self._select_session_from_tree(self.session_tree))
        self.session_tree.bind("<Double-Button-1>", lambda _event: self.open_selected())
        self.session_tree.bind("<Return>", lambda _event: self.open_selected())
        body.add(sessions, weight=3)
        right = ttk.PanedWindow(body, orient="vertical")
        search_frame = ttk.Labelframe(right, text="搜索结果")
        self.search_tree = _scrolled_tree(
            search_frame,
            columns=("title", "project", "preview"),
            headings=("会话", "项目", "匹配内容"),
            widths=(230, 110, 390),
        )
        self.search_tree.bind("<<TreeviewSelect>>", lambda _event: self._select_session_from_tree(self.search_tree))
        self.search_tree.bind("<Double-Button-1>", lambda _event: self.open_search_selected())
        self.search_tree.bind("<Return>", lambda _event: self.open_search_selected())
        self.search_empty = StringVar(value="输入关键词后显示搜索结果")
        ttk.Label(search_frame, textvariable=self.search_empty, style="Hint.TLabel").pack(anchor="w", padx=7, pady=(0, 4))
        right.add(search_frame, weight=2)
        summary_frame = ttk.Labelframe(right, text="会话摘要")
        self.summary = _scrolled_text(summary_frame, wrap="word", height=8)
        right.add(summary_frame, weight=1)
        body.add(right, weight=4)
        actions = ttk.Frame(self.browse_tab)
        actions.pack(fill="x", pady=(8, 0))
        export_button = ttk.Button(actions, text="导出当前会话", command=self.use_selected_for_export, takefocus=True)
        export_button.pack(side=RIGHT)
        open_button = ttk.Button(actions, text="查看详情", command=self.open_selected, takefocus=True)
        open_button.pack(side=RIGHT, padx=(0, 8))
        self.buttons.extend([open_button, export_button])

    def _build_export_tab(self) -> None:
        self.export_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.export_tab, text="导出")
        current = ttk.Labelframe(self.export_tab, text="当前会话")
        current.pack(fill="x", pady=(0, 8))
        ttk.Label(current, textvariable=self.selected_session_label).pack(anchor="w")
        controls = ttk.Frame(self.export_tab)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(controls, text="格式").pack(side=LEFT)
        ttk.Combobox(
            controls,
            textvariable=self.export_profile,
            values=tuple(EXPORT_PROFILES),
            width=18,
            state="readonly",
            takefocus=True,
        ).pack(side=LEFT, padx=(6, 14))
        ttk.Label(controls, text="隐私处理").pack(side=LEFT)
        ttk.Combobox(
            controls,
            textvariable=self.privacy_mode,
            values=tuple(PRIVACY_MODES),
            width=18,
            state="readonly",
            takefocus=True,
        ).pack(side=LEFT, padx=(6, 14))
        self.export_button = ttk.Button(controls, text="确认导出", command=self.execute_export, takefocus=True, state="disabled")
        self.export_button.pack(side=RIGHT)
        preview_button = ttk.Button(controls, text="生成安全预览", command=self.preview_export, takefocus=True)
        preview_button.pack(side=RIGHT, padx=(0, 8))
        self.buttons.extend([preview_button, self.export_button])
        out_row = ttk.Frame(self.export_tab)
        out_row.pack(fill="x", pady=(0, 6))
        ttk.Label(out_row, text="输出目录").pack(side=LEFT)
        ttk.Entry(out_row, textvariable=self.export_out, takefocus=True).pack(side=LEFT, fill="x", expand=True, padx=(6, 8))
        choose = ttk.Button(out_row, text="选择目录…", command=self.choose_export_directory, takefocus=True)
        choose.pack(side=LEFT)
        self.buttons.append(choose)
        ttk.Label(
            self.export_tab,
            text="先预览文件和隐私结果；只有当前参数与预览一致时，“确认导出”才可用。",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 6))
        self.export_text = _scrolled_text(self.export_tab, wrap="word", height=18)

    def _build_backup_tab(self) -> None:
        self.backup_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.backup_tab, text="备份")
        sections = ttk.Notebook(self.backup_tab, takefocus=True)
        sections.pack(fill=BOTH, expand=True)
        center = ttk.Frame(sections, padding=10)
        expert = ttk.Frame(sections, padding=10)
        sections.add(center, text="智能备份中心")
        sections.add(expert, text="隐私、手动备份与恢复")

        ttk.Label(center, textvariable=self.backup_headline, style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        info = ttk.Frame(center)
        info.pack(fill="x", pady=(0, 8))
        _info_row(info, 0, "最近检查", self.backup_last_run)
        _info_row(info, 1, "自动计划", self.backup_schedule)
        _info_row(info, 2, "下次运行", self.backup_next_run)
        _info_row(info, 3, "磁盘空间", self.backup_disk)
        out = ttk.Frame(center)
        out.pack(fill="x", pady=(0, 8))
        ttk.Label(out, text="备份目录").pack(side=LEFT)
        ttk.Entry(out, textvariable=self.smart_backup_out, takefocus=True).pack(side=LEFT, fill="x", expand=True, padx=(6, 8))
        choose_smart = ttk.Button(out, text="选择目录…", command=self.choose_smart_backup_directory, takefocus=True)
        choose_smart.pack(side=LEFT)
        actions = ttk.Frame(center)
        actions.pack(fill="x", pady=(0, 8))
        self.smart_backup_button = ttk.Button(actions, text="立即智能备份", command=self.run_smart_backup, takefocus=True)
        self.smart_backup_button.pack(side=LEFT)
        refresh = ttk.Button(actions, text="刷新状态", command=self.refresh_backup_center, takefocus=True)
        refresh.pack(side=LEFT, padx=(8, 0))
        ttk.Label(actions, text="系统自动判断核心 / 证据 / 取证档位", style="Hint.TLabel").pack(side=LEFT, padx=(12, 0))
        self.buttons.extend([choose_smart, self.smart_backup_button, refresh])
        self.backup_text = _scrolled_text(center, wrap="word", height=14)

        privacy = ttk.Labelframe(expert, text="当前会话隐私检查")
        privacy.pack(fill="x", pady=(0, 8))
        ttk.Label(privacy, textvariable=self.selected_session_label).pack(side=LEFT, fill="x", expand=True)
        scan = ttk.Button(privacy, text="扫描当前会话", command=self.show_warnings, takefocus=True)
        scan.pack(side=RIGHT)

        manual = ttk.Labelframe(expert, text="高级：手动单库备份")
        manual.pack(fill="x", pady=(0, 8))
        ttk.Entry(manual, textvariable=self.backup_out, takefocus=True).pack(side=LEFT, fill="x", expand=True)
        choose_manual = ttk.Button(manual, text="选择目录…", command=self.choose_manual_backup_directory, takefocus=True)
        choose_manual.pack(side=LEFT, padx=(8, 0))
        manual_button = ttk.Button(manual, text="创建手动备份", command=self.create_backup, takefocus=True)
        manual_button.pack(side=LEFT, padx=(8, 0))

        restore = ttk.Labelframe(expert, text="恢复到新的数据库")
        restore.pack(fill="x", pady=(0, 8))
        file_row = ttk.Frame(restore)
        file_row.pack(fill="x", pady=(0, 6))
        ttk.Label(file_row, text="备份文件").pack(side=LEFT)
        ttk.Entry(file_row, textvariable=self.backup_file, takefocus=True).pack(side=LEFT, fill="x", expand=True, padx=(6, 8))
        choose_file = ttk.Button(file_row, text="选择文件…", command=self.choose_backup_file, takefocus=True)
        choose_file.pack(side=LEFT)
        target_row = ttk.Frame(restore)
        target_row.pack(fill="x", pady=(0, 6))
        ttk.Label(target_row, text="新数据库").pack(side=LEFT)
        ttk.Entry(target_row, textvariable=self.restore_target, takefocus=True).pack(side=LEFT, fill="x", expand=True, padx=(6, 8))
        choose_target = ttk.Button(target_row, text="选择位置…", command=self.choose_restore_target, takefocus=True)
        choose_target.pack(side=LEFT)
        restore_actions = ttk.Frame(restore)
        restore_actions.pack(fill="x")
        verify = ttk.Button(restore_actions, text="验证备份", command=self.verify_backup, takefocus=True)
        verify.pack(side=LEFT)
        plan = ttk.Button(restore_actions, text="恢复预检", command=self.plan_restore, takefocus=True)
        plan.pack(side=LEFT, padx=(8, 0))
        apply_button = ttk.Button(restore_actions, text="确认恢复", command=self.apply_restore, takefocus=True)
        apply_button.pack(side=LEFT, padx=(8, 0))
        self.buttons.extend([scan, choose_manual, manual_button, choose_file, choose_target, verify, plan, apply_button])
        self.safety_text = _scrolled_text(expert, wrap="word", height=8)

    def _build_integration_tab(self) -> None:
        self.integration_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.integration_tab, text="Codex 联动")
        header = ttk.Frame(self.integration_tab)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="Codex 联动状态", style="Heading.TLabel").pack(side=LEFT)
        refresh = ttk.Button(header, text="重新检查", command=self.show_integrations, takefocus=True)
        refresh.pack(side=RIGHT)
        self.buttons.append(refresh)
        self.integration_text = _scrolled_text(self.integration_tab, wrap="word", height=20)

    def _build_health_tab(self) -> None:
        self.health_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.health_tab, text="健康")
        ttk.Label(self.health_tab, textvariable=self.health_headline, style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        diagnosis = ttk.Frame(self.health_tab)
        diagnosis.pack(fill="x", pady=(0, 8))
        diagnose = ttk.Button(diagnosis, text="重新诊断", command=self.show_health, takefocus=True)
        diagnose.pack(side=LEFT)
        ttk.Label(diagnosis, text="诊断不会修改数据库", style="Hint.TLabel").pack(side=LEFT, padx=(10, 0))
        maintenance = ttk.Labelframe(self.health_tab, text="维护（仅在诊断建议时使用）")
        maintenance.pack(fill="x", pady=(0, 8))
        reindex = ttk.Button(maintenance, text="重建搜索索引", command=self.reindex_search, takefocus=True)
        reindex.pack(side=LEFT)
        vacuum = ttk.Button(maintenance, text="压缩数据库", command=self.vacuum_database, takefocus=True)
        vacuum.pack(side=LEFT, padx=(8, 0))
        self.buttons.extend([diagnose, reindex, vacuum])
        self.health_text = _scrolled_text(self.health_tab, wrap="word", height=18)

    def _build_advanced_tab(self) -> None:
        self.advanced_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.advanced_tab, text="高级")
        controls = ttk.Frame(self.advanced_tab)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(controls, text="结构定义名称").pack(side=LEFT)
        ttk.Entry(controls, textvariable=self.schema_name, width=24, takefocus=True).pack(side=LEFT, padx=(6, 8))
        schema = ttk.Button(controls, text="查看结构定义", command=self.show_schema, takefocus=True)
        schema.pack(side=LEFT)
        robot = ttk.Button(controls, text="查看机器人说明", command=self.show_robot_docs, takefocus=True)
        robot.pack(side=LEFT, padx=(8, 0))
        write_row = ttk.Frame(self.advanced_tab)
        write_row.pack(fill="x", pady=(0, 8))
        ttk.Label(write_row, text="输出目录").pack(side=LEFT)
        ttk.Entry(write_row, textvariable=self.schema_out, takefocus=True).pack(side=LEFT, fill="x", expand=True, padx=(6, 8))
        choose = ttk.Button(write_row, text="选择目录…", command=self.choose_schema_directory, takefocus=True)
        choose.pack(side=LEFT)
        write = ttk.Button(write_row, text="导出全部结构定义", command=self.write_schemas, takefocus=True)
        write.pack(side=LEFT, padx=(8, 0))
        self.buttons.extend([schema, robot, choose, write])
        self.advanced_text = _scrolled_text(self.advanced_tab, wrap="word", height=18)

    def _bind_shortcuts(self) -> None:
        self.root.bind_all("<Control-f>", lambda _event: self.search_entry.focus_set())
        self.root.bind_all("<F5>", lambda _event: self.refresh())
        self.root.bind_all("<Control-b>", lambda _event: self.notebook.select(self.backup_tab))
        self.root.bind_all("<Control-e>", lambda _event: self.notebook.select(self.export_tab))

    def _bind_export_invalidation(self) -> None:
        for variable in (self.selected_session, self.export_out, self.export_profile, self.privacy_mode):
            variable.trace_add("write", self._invalidate_export_preview)


def _scrolled_text(parent: object, *, wrap: str, height: int) -> Text:
    frame = ttk.Frame(parent)
    frame.pack(fill=BOTH, expand=True)
    widget = Text(frame, height=height, wrap=wrap, takefocus=True)
    vertical = ttk.Scrollbar(frame, orient="vertical", command=widget.yview, takefocus=False)
    widget.configure(yscrollcommand=vertical.set)
    widget.pack(side=LEFT, fill=BOTH, expand=True)
    vertical.pack(side=RIGHT, fill="y")
    return widget


def _scrolled_tree(
    parent: object,
    *,
    columns: tuple[str, ...],
    headings: tuple[str, ...],
    widths: tuple[int, ...],
) -> ttk.Treeview:
    frame = ttk.Frame(parent)
    frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
    tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse", takefocus=True)
    for name, heading, width in zip(columns, headings, widths, strict=True):
        tree.heading(name, text=heading)
        tree.column(name, width=width, minwidth=50, stretch=name in {"title", "preview"})
    vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview, takefocus=False)
    horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview, takefocus=False)
    tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return tree


def _info_row(parent: ttk.Frame, row: int, label: str, variable: StringVar) -> None:
    ttk.Label(parent, text=label, width=10).grid(row=row, column=0, sticky="w", pady=2)
    ttk.Label(parent, textvariable=variable).grid(row=row, column=1, sticky="w", pady=2)


def _display_time(value: str) -> str:
    if len(value) >= 16:
        return value[:10] + " " + value[11:16]
    return value


def launch_desktop_app(config: DesktopAppConfig) -> None:
    app = ThreadVaultDesktopApp(build_desktop_gateway(config))
    app.run()

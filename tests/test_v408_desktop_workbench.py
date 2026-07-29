from __future__ import annotations

import tkinter as tk
from pathlib import Path
from time import monotonic
from tkinter import ttk

import pytest

import threadvault.desktop_app as desktop_app_module
import threadvault.desktop_data as desktop_data_module
import threadvault.desktop_theme as desktop_theme_module
from threadvault.config import default_codex_home, default_db_path
from threadvault.database import SCHEMA_VERSION, connect, init_db
from threadvault.desktop_app import ThreadVaultDesktopApp, _reconcile_tree_rows
from threadvault.desktop_data import DesktopAppConfig, DesktopDataGateway
from threadvault.desktop_theme import DesktopAppTheme, configure_desktop_theme
from threadvault.restore_history import default_restore_history_path
from threadvault.store import ArchiveStore


class _FakeTree:
    def __init__(self, rows: list[tuple[str, tuple[object, ...]]]) -> None:
        self.rows = dict(rows)
        self.order = [session_id for session_id, _values in rows]
        self.insert_count = 0
        self.item_write_count = 0
        self.move_count = 0
        self.delete_count = 0
        self._selection = ("beta",)
        self._focus = "beta"
        self._yview = (0.35, 0.75)
        self._xview = (0.1, 0.9)

    def selection(self) -> tuple[str, ...]:
        return self._selection

    def selection_set(self, *items: str) -> None:
        self._selection = tuple(items)

    def focus(self, item: str | None = None) -> str:
        if item is not None:
            self._focus = item
        return self._focus

    def yview(self) -> tuple[float, float]:
        return self._yview

    def xview(self) -> tuple[float, float]:
        return self._xview

    def yview_moveto(self, fraction: float) -> None:
        self._yview = (fraction, min(fraction + 0.4, 1.0))

    def xview_moveto(self, fraction: float) -> None:
        self._xview = (fraction, min(fraction + 0.8, 1.0))

    def get_children(self) -> tuple[str, ...]:
        return tuple(self.order)

    def delete(self, *items: str) -> None:
        self.delete_count += len(items)
        for item in items:
            self.order.remove(item)
            self.rows.pop(item)
        self._selection = tuple(item for item in self._selection if item in self.rows)
        if self._focus not in self.rows:
            self._focus = ""
        self._yview = (0.0, 0.4)
        self._xview = (0.0, 0.8)

    def insert(self, _parent: str, _index: str, *, iid: str, values: tuple[object, ...]) -> None:
        self.insert_count += 1
        self.rows[iid] = values
        self.order.append(iid)

    def item(self, item: str, option: str | None = None, **kwargs: object) -> tuple[object, ...] | None:
        if "values" in kwargs:
            self.item_write_count += 1
            self.rows[item] = tuple(kwargs["values"])
            return None
        assert option == "values"
        return self.rows[item]

    def move(self, item: str, _parent: str, index: int) -> None:
        self.move_count += 1
        self.order.remove(item)
        self.order.insert(index, item)


def test_tree_reconciliation_skips_unchanged_rows_and_preserves_operator_state() -> None:
    original = [("alpha", ("Alpha", "Project A", 4)), ("beta", ("Beta", "Project B", 9))]
    tree = _FakeTree([("alpha", ("Alpha", "Project A", "4")), ("beta", ("Beta", "Project B", "9"))])

    unchanged = _reconcile_tree_rows(tree, original)

    assert unchanged.changed == 0
    assert tree.insert_count == 0
    assert tree.item_write_count == 0
    assert tree.move_count == 0
    assert tree.selection() == ("beta",)
    assert tree.focus() == "beta"
    assert tree.yview() == (0.35, 0.75)
    assert tree.xview() == (0.1, 0.9)

    changed = _reconcile_tree_rows(
        tree,
        [("beta", ("Beta updated", "Project B", 9)), ("gamma", ("Gamma", "Project C", 3))],
    )

    assert (changed.inserted, changed.updated, changed.removed, changed.moved) == (1, 1, 1, 0)
    assert tree.get_children() == ("beta", "gamma")
    assert tree.selection() == ("beta",)
    assert tree.focus() == "beta"
    assert tree.yview() == (0.35, 0.75)
    assert tree.xview() == (0.1, 0.9)


def test_state_title_cache_invalidates_for_codex_sqlite_wal_changes(tmp_path: Path, monkeypatch) -> None:
    state_db = tmp_path / "state_5.sqlite"
    state_db.write_text("state", encoding="utf-8")
    calls: list[Path] = []

    def fake_load(codex_home: Path | None = None) -> dict[str, dict[str, str]]:
        calls.append(codex_home or Path())
        return {"session": {"title": f"title-{len(calls)}"}}

    monkeypatch.setattr(desktop_data_module, "load_state_thread_index", fake_load)
    gateway = DesktopDataGateway(object(), DesktopAppConfig(codex_home=tmp_path))

    assert gateway._state_index()["session"]["title"] == "title-1"
    assert gateway._state_index()["session"]["title"] == "title-1"
    assert len(calls) == 1

    (tmp_path / "state_5.sqlite-wal").write_text("new WAL content", encoding="utf-8")

    assert gateway._state_index()["session"]["title"] == "title-2"
    assert len(calls) == 2


def test_suite_fixture_isolates_default_local_runtime_paths(tmp_path: Path) -> None:
    assert default_db_path().is_relative_to(tmp_path)
    assert default_codex_home().is_relative_to(tmp_path)
    assert default_restore_history_path().is_relative_to(tmp_path)


def test_current_schema_initialization_skips_meta_rewrite_but_repairs_stale_version(tmp_path: Path) -> None:
    with connect(tmp_path / "threadvault.db") as conn:
        init_db(conn)
        unchanged_before = conn.total_changes

        init_db(conn)

        assert conn.total_changes == unchanged_before
        conn.execute("UPDATE meta SET value = '0' WHERE key = 'schema_version'")
        conn.commit()
        stale_before = conn.total_changes

        init_db(conn)

        assert conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0] == str(SCHEMA_VERSION)
        assert conn.total_changes == stale_before + 1


def test_workbench_theme_covers_ttk_and_native_tk_surfaces() -> None:
    palette = DesktopAppTheme().palette
    assert palette.accent != palette.canvas
    assert palette.surface != palette.surface_muted

    source = Path(desktop_theme_module.__file__).read_text(encoding="utf-8")
    for surface in (
        "TButton",
        "TMenubutton",
        "TEntry",
        "TCombobox",
        "Treeview",
        "Vertical.TScrollbar",
        "Horizontal.TScrollbar",
        "TNotebook.Tab",
        "configure_text_surface",
        "configure_popup_menu",
        "Toplevel",
    ):
        assert surface in source

    app_source = Path(desktop_app_module.__file__).read_text(encoding="utf-8")
    assert "configure_desktop_theme" in app_source
    assert "ask_themed_confirmation" in app_source
    assert "_reconcile_tree_rows" in app_source


def test_workbench_theme_runtime_states_do_not_fall_back_to_native_gray() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk display unavailable: {error}")
    root.withdraw()
    try:
        theme = DesktopAppTheme()
        palette = theme.palette
        style: ttk.Style = configure_desktop_theme(root, theme)

        assert style.lookup("TEntry", "background", ("readonly",)) == palette.surface
        assert style.lookup("TCombobox", "background", ("active",)) == palette.accent_soft
        assert style.lookup("TMenubutton", "arrowcolor", ("disabled",)) == palette.disabled_fg
        assert style.lookup("Vertical.TScrollbar", "background", ("disabled",)) == palette.disabled_bg
        assert style.lookup("TLabelframe", "background", ("disabled",)) == palette.disabled_bg
    finally:
        root.destroy()


def test_desktop_initial_refresh_does_not_treat_treeviews_as_stateful_inputs(tmp_path: Path) -> None:
    try:
        probe = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk display unavailable: {error}")
    probe.destroy()
    codex_home = Path("tests/fixtures/codex_home").resolve()
    db = tmp_path / "threadvault.db"
    store = ArchiveStore(db)
    store.import_codex(codex_home)
    app = ThreadVaultDesktopApp(
        DesktopDataGateway(store, DesktopAppConfig(db_path=db, codex_home=codex_home))
    )
    app.root.withdraw()
    try:
        deadline = monotonic() + 5
        def stop_when_loaded() -> None:
            if not app.busy and app.session_tree.get_children():
                app.root.quit()
            elif monotonic() >= deadline:
                app.root.quit()
            else:
                app.root.after(20, stop_when_loaded)

        app.root.after(20, stop_when_loaded)
        app.root.mainloop()
        assert app.busy is False
        assert app.session_tree.get_children()
        assert "操作失败" not in app.status.get()
    finally:
        app.root.destroy()

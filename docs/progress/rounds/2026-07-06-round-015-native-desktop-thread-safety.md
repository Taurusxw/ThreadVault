# 2026-07-06 Round 015 - Native Desktop Thread Safety

## 本轮目标

Perform native desktop runtime QA and harden Tkinter thread-safety before considering the desktop app a Web UI replacement.

## 背景原因

Data tests alone do not prove the native desktop app is usable. A runtime launch attempt exposed a real Tkinter threading problem: background workers were reading `StringVar` values before the Tk main loop was established.

## 修改范围

- Moved Tk variable reads onto the UI thread before dispatching background work.
- Deferred the initial desktop refresh with `root.after(0, ...)`.
- Added a clear empty-state message for the native desktop search-results list before a query is entered.
- Split Advanced-tab controls into compact rows after screenshot QA found governance controls overflowing at `860x520`.
- Added a regression test that guards against background worker lambdas reading Tk variables directly.
- Updated version metadata and documentation.

## 实施步骤

1. Started a native desktop QA window with a fixture-backed temporary database.
2. Observed `RuntimeError: main thread is not in main loop` from a background worker reading `StringVar`.
3. Captured Tk variable values on the UI thread in refresh/export/backup/restore/schema paths.
4. Scheduled initial refresh after Tk startup instead of during constructor execution.
5. Added a static regression test for the worker boundary.
6. Captured the native window by Tk hwnd and verified the compact layout renders with a clear empty search state.
7. Re-ran hwnd screenshot QA on the Advanced tab and verified controls fit after the layout fix.

## 关键决策

- Background workers receive plain values such as strings and paths.
- Tk state stays on the UI thread.
- Screenshot capture works when using the Tk-reported hwnd directly instead of searching by window title.

## 修改清单

- `src/threadvault/desktop_app.py`
- `tests/test_v407_desktop_app.py`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- `docs/CHANGELOG.md`
- `docs/DOC_INDEX.md`
- `docs/PROGRESS.md`
- `pyproject.toml`
- `src/threadvault/__init__.py`

## 测试与验证

```powershell
py -3.12 -m pytest tests\test_v401_personal_ui_readiness.py tests\test_v402_local_ui_server.py tests\test_v407_desktop_app.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py tests\test_v105_codex_skill_target.py -q
py -3.12 -m ruff check src\threadvault\desktop_data.py src\threadvault\desktop_app.py src\threadvault\cli.py src\threadvault\store.py src\threadvault\personal_ui.py src\threadvault\export_targets.py tests\test_v407_desktop_app.py tests\test_v401_personal_ui_readiness.py tests\test_v402_local_ui_server.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py tests\test_v105_codex_skill_target.py
```

Result:

- Expanded related regression: `44 passed`
- Ruff passed for the touched desktop/CLI/store/Web UI compatibility/test surface.
- Runtime QA found and drove the thread-safety fix.
- Native hwnd screenshot QA captured the compact desktop window after the fix.
- Advanced-tab hwnd screenshot QA captured a full `860x520` window after splitting controls.

## 文档更新

- Updated README current version.
- Updated architecture and Chinese usage manual with the UI-thread/background-worker rule.
- Updated changelog, progress overview, and document index.

## 风险与遗留问题

- Broader manual workflow review remains before declaring Web UI replacement complete.
- Governance/audit write operations remain command-based.
- Overwrite restore remains command-based.

## 下一步计划

- Re-run visual QA with a tool that can reliably inspect the native window.
- Continue migrating or explicitly retiring remaining governance/audit write surfaces.
- Decide whether overwrite restore belongs in the compact desktop app.

## 状态

completed

# 2026-07-06 Round 009 - Native Desktop App

## 本轮目标

Add the first minimal native desktop app slice so ThreadVault can start moving daily Web UI workflows into a local, fast, small-footprint window.

## 背景原因

The user wants to eventually abandon the browser-based UI and prefers the smallest, fastest local UI approach. For the current Python-first project, Tkinter keeps the runtime in the Python standard library and avoids Electron, React, Tauri, WebView, and frontend build dependencies.

## 修改范围

- Added a desktop-facing data module over existing `ArchiveStore` client contracts.
- Added a native Tkinter desktop shell and CLI launch command.
- Added tests for desktop data, export preview, safety, MCP discovery, and CLI/capability metadata.
- Updated version, README, architecture, Chinese usage manual, changelog, document index, and progress overview.

## 实施步骤

1. Added `threadvault desktop launch`.
2. Added `DesktopDataGateway` for browse/search/session summary, export preview, warning summary, MCP integration summary, health summary, and advanced command reference.
3. Added a compact Tkinter window with ordered tabs: browse, export, safety, MCP, health, and advanced.
4. Ran desktop actions through background worker threads to keep the Tk main loop responsive.
5. Left destructive low-frequency workflows as explicit commands until native confirmation gates are designed.

## 关键决策

- Chose Tkinter because it is already available with Python, has the smallest dependency footprint, and is fast enough for this local archive tool when long operations are moved off the UI thread.
- Kept `desktop_data.py` as the main interface so the UI does not reach into low-level database details.
- Reused `client_export_preview` and `client_warnings` instead of creating a new export/privacy path.
- Did not remove the Web UI yet; the native app is the migration path, not full parity.

## 修改清单

- `src/threadvault/desktop_data.py`
- `src/threadvault/desktop_app.py`
- `src/threadvault/cli.py`
- `src/threadvault/store.py`
- `tests/test_v407_desktop_app.py`
- `tests/test_v402_local_ui_server.py`
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
py -3.12 -m pytest tests\test_v407_desktop_app.py tests\test_v402_local_ui_server.py -q
py -3.12 -m pytest tests\test_v401_personal_ui_readiness.py tests\test_v402_local_ui_server.py tests\test_v407_desktop_app.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py tests\test_v105_codex_skill_target.py -q
py -3.12 -m ruff check src\threadvault\desktop_data.py src\threadvault\desktop_app.py src\threadvault\cli.py src\threadvault\store.py tests\test_v407_desktop_app.py tests\test_v402_local_ui_server.py
```

Result:

- Focused desktop/local UI discovery: `10 passed`
- Expanded related regression: `40 passed`
- Ruff passed for the touched desktop/CLI/store/test surface.

## 文档更新

- Updated README quick start and version table.
- Updated architecture with native desktop module and runtime flow.
- Updated Chinese usage manual with native desktop instructions.
- Updated changelog, progress overview, and document index.

## 风险与遗留问题

- The native desktop app is not yet full Web UI parity.
- Restore apply, vacuum, reindex, schema write, and some governance/audit workflows still need native confirmation gates before becoming first-class desktop buttons.
- Visual QA of the native Tkinter window was not automated in this round; coverage is currently data/CLI/lint based.

## 下一步计划

- Continue migrating low-frequency Web UI operations into native tabs.
- Add native confirmation gates before enabling destructive actions.
- Add a safe local-only export-directory opener after the preview/write workflow is settled.

## 状态

completed

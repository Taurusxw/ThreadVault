# 2026-07-06 Round 010 - Native Desktop Safety Actions

## 本轮目标

Continue replacing Web UI dependency by migrating data-safety and maintenance workflows into the native Tkinter desktop app.

## 背景原因

The first desktop slice covered browse/search/session/export-preview/safety summary/MCP/health. To move closer to abandoning the browser UI, the desktop app needs real local operations for backup, verification, restore planning, and safe maintenance.

## 修改范围

- Added desktop gateway methods for backup, backup verification, read-only restore planning, FTS reindex, and SQLite vacuum.
- Added native Tkinter controls for these actions in the Safety and Health tabs.
- Added native confirmation prompts before backup, reindex, and vacuum write-like actions.
- Updated focused desktop tests and project documentation.

## 实施步骤

1. Extended `DesktopDataGateway` with data-safety and maintenance methods.
2. Added Safety-tab fields for backup directory, backup file, and restore target.
3. Added buttons for backup, verify backup, and restore plan.
4. Added Health-tab buttons for diagnostics, reindex, and vacuum.
5. Kept restore apply out of the native UI until full target-path and overwrite confirmation gates are designed.

## 关键决策

- Reused `ArchiveStore.backup`, `verify_backup`, `restore_plan`, `reindex`, and `vacuum` instead of creating parallel desktop-only logic.
- Treated restore planning as read-only and safe for native UI.
- Required confirmation prompts for operations that write or mutate local data.
- Did not add Electron, WebView, React, Tauri, or any new dependency.

## 修改清单

- `src/threadvault/desktop_data.py`
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

- Expanded related regression: `41 passed`
- Ruff passed for the touched desktop/CLI/store/Web UI compatibility/test surface.

## 文档更新

- Updated README current version and desktop quick start details.
- Updated architecture with the expanded desktop Store interface.
- Updated Chinese usage manual with desktop backup/restore-plan/maintenance behavior.
- Updated changelog, progress overview, and document index.

## 风险与遗留问题

- Restore apply is still not exposed in the native desktop app.
- Schema writes and some governance/audit workflows still need native confirmation gates before becoming desktop buttons.
- Native visual QA is still manual; automated coverage is focused on data contracts, CLI discovery, and compatibility tests.

## 下一步计划

- Add native schema/robot-docs read surfaces, then schema-write confirmation.
- Add governance/audit read-only panels.
- Design a full restore-apply confirmation path with target path, backup verification, overwrite checks, and pre-restore backup.

## 状态

completed

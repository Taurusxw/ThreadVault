# 2026-07-06 Round 016 - Native Desktop Smoke Command

## 本轮目标

Add an automated, non-window desktop smoke command so the native app can be verified without opening the Tkinter UI.

## 背景原因

Runtime window QA is useful but not always available in automated environments. The desktop app needs a fast command that checks the desktop gateway, Tkinter availability, no-browser/no-server boundaries, and archive loading without blocking on a GUI window.

## 修改范围

- Added `desktop_smoke.v1` payload support.
- Added `threadvault desktop smoke --json`.
- Added capabilities and robot guide discovery for the smoke command.
- Added tests for smoke payload and CLI discovery.

## 实施步骤

1. Added `run_desktop_smoke()` in `desktop_data.py`.
2. Added `desktop smoke` Typer command with lazy desktop imports.
3. Registered `desktop smoke` in capabilities JSON outputs and robot guide recommended commands.
4. Added tests for payload shape, CLI help, and metadata.

## 关键决策

- Smoke does not open a window.
- Smoke checks Tkinter availability by module discovery and validates the desktop data gateway with a snapshot.
- Visual QA remains separate from non-window smoke.

## 修改清单

- `src/threadvault/desktop_data.py`
- `src/threadvault/cli.py`
- `src/threadvault/store.py`
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

Additional smoke:

```powershell
threadvault desktop smoke --db <fixture-db> --json
```

Result:

- Desktop smoke returned `ok: true`.
- Expanded related regression: `45 passed`
- Ruff passed for the touched desktop/CLI/store/Web UI compatibility/test surface.

## 文档更新

- Updated README desktop quick start.
- Updated architecture and Chinese usage manual with the smoke command.
- Updated changelog, progress overview, and document index.

## 风险与遗留问题

- Smoke does not replace hwnd screenshot QA.
- Governance/audit write operations remain command-based.
- Overwrite restore remains command-based.

## 下一步计划

- Use `threadvault desktop smoke --json` as the fast desktop verification command after future desktop edits.
- Continue deciding which remaining governance/audit write actions belong in the compact desktop UI.

## 状态

completed

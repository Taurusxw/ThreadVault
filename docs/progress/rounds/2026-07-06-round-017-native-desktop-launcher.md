# 2026-07-06 Round 017 - Native Desktop Launcher

## 本轮目标

Add a simple Windows launcher so the native desktop app can become the obvious daily entrypoint instead of the browser UI launcher.

## 背景原因

The project already had `启动ThreadVault中文界面.cmd` for the Web UI. To move daily usage away from the browser, the native desktop app needs an equally simple double-click launcher that does not start a browser or local Web UI server.

## 修改范围

- Added `启动ThreadVault桌面版.cmd`.
- Added launcher coverage in desktop tests.
- Updated README, usage manual, architecture, changelog, progress overview, and document index.

## 实施步骤

1. Created a Windows `.cmd` launcher that sets `PYTHONPATH` to `src`.
2. Checked Python launcher availability and ThreadVault importability.
3. Ran `desktop smoke --json` before launch.
4. Started `desktop launch` only after smoke passed.
5. Added tests to ensure the launcher uses desktop commands and does not start `ui serve` or a browser.

## 关键决策

- No installer, Electron, Tauri, WebView, or packaging dependency.
- The launcher stays a small script matching the project-local development flow.
- Smoke runs first so startup failures fail early with a clear message.

## 修改清单

- `启动ThreadVault桌面版.cmd`
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
threadvault desktop smoke --db <fixture-db> --json
py -3.12 -m pytest tests\test_v401_personal_ui_readiness.py tests\test_v402_local_ui_server.py tests\test_v407_desktop_app.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py tests\test_v105_codex_skill_target.py -q
py -3.12 -m ruff check src\threadvault\desktop_data.py src\threadvault\desktop_app.py src\threadvault\cli.py src\threadvault\store.py src\threadvault\personal_ui.py src\threadvault\export_targets.py tests\test_v407_desktop_app.py tests\test_v401_personal_ui_readiness.py tests\test_v402_local_ui_server.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py tests\test_v105_codex_skill_target.py
```

Result:

- Desktop smoke returned `ok: true`.
- Expanded related regression: `46 passed`
- Ruff passed for the touched desktop/CLI/store/Web UI compatibility/test surface.

## 文档更新

- Updated README and Chinese usage manual to show the desktop launcher first.
- Updated architecture with the launcher entrypoint.
- Updated changelog, progress overview, and document index.

## 风险与遗留问题

- The launcher assumes Windows with the Python launcher `py.exe`.
- Governance/audit write operations remain command-based.
- Overwrite restore remains command-based.

## 下一步计划

- Consider whether to de-emphasize or archive the Web UI launcher after final parity review.
- Continue deciding which remaining governance/audit write actions belong in the compact desktop UI.

## 状态

completed

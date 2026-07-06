# 2026-07-06 Round 018 - Desktop-First Launcher Guidance

## 本轮目标

Make the native desktop launcher the clear daily entrypoint and demote the old Web UI launcher to a legacy fallback.

## 背景原因

The native desktop app now has a Windows launcher and smoke command. The old browser launcher still existed with primary-entrypoint wording, which could keep users on the Web UI path.

## 修改范围

- Updated `启动ThreadVault中文界面.cmd` header and notes.
- Added test coverage that the Web UI launcher recommends the desktop launcher and labels itself as legacy fallback.
- Updated version metadata and documentation.

## 实施步骤

1. Changed the Web UI launcher title to `ThreadVault Legacy Chinese Web UI`.
2. Added notes recommending `启动ThreadVault桌面版.cmd`.
3. Kept the Web UI launcher functional as a fallback.
4. Added tests for desktop-first launcher guidance.

## 关键决策

- Do not delete the Web UI launcher yet.
- Keep Web UI available for fallback and debugging.
- Make the desktop launcher the recommended daily entrypoint.

## 修改清单

- `启动ThreadVault中文界面.cmd`
- `tests/test_v407_desktop_app.py`
- `README.md`
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

- Expanded related regression: `46 passed`
- Ruff passed for the touched desktop/CLI/store/Web UI compatibility/test surface.

## 文档更新

- Updated README and Chinese usage manual to call the browser launcher a legacy fallback.
- Updated changelog, progress overview, and document index.

## 风险与遗留问题

- Web UI is still present for fallback/debugging.
- Governance/audit write operations remain command-based.
- Overwrite restore remains command-based.

## 下一步计划

- Complete a final parity review before removing or archiving Web UI surfaces.
- Decide whether remaining governance/audit write actions should stay CLI-only.

## 状态

completed

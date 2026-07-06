# 2026-07-06 Round 014 - Native Desktop Governance Diagnostics

## 本轮目标

Reduce remaining Web UI dependency by moving governance diagnostic read surfaces into the native desktop app.

## 背景原因

The desktop app already covers archive/search/export, data safety, maintenance, restore apply to new targets, Schema/Robot Docs/Governance status, and Schema write. Remaining Web UI usage is mostly advanced governance/audit workflows. This round migrates read-only diagnostic aggregation without adding write-capable governance operations.

## 修改范围

- Added a desktop governance diagnostics gateway method.
- Added an Advanced-tab `治理诊断` button.
- Updated robot/capability metadata and tests.
- Updated version metadata and documentation.

## 实施步骤

1. Added `governance_diagnostics_summary()` in `DesktopDataGateway`.
2. Aggregated existing governance status, enforcement gaps, readiness, identity, central policy/backup, and v3 completion gap checks.
3. Added a compact button to render diagnostics in the Advanced tab text panel.
4. Added tests for diagnostic output and desktop metadata.

## 关键决策

- Kept this surface read-only.
- Did not add governance/audit writes or centralized policy writes.
- Aggregated many diagnostics behind one desktop button to keep the UI compact.

## 修改清单

- `src/threadvault/desktop_data.py`
- `src/threadvault/desktop_app.py`
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

Result:

- Expanded related regression: `43 passed`
- Ruff passed for the touched desktop/CLI/store/Web UI compatibility/test surface.

## 文档更新

- Updated README current version.
- Updated architecture and Chinese usage manual with the governance diagnostics panel.
- Updated changelog, progress overview, and document index.

## 风险与遗留问题

- Governance/audit write operations remain command-based.
- Overwrite restore remains command-based.
- Native visual QA remains manual; this round validated data contracts and compatibility tests.

## 下一步计划

- Decide whether governance/audit writes belong in the compact personal desktop app.
- Decide whether overwrite restore belongs in the compact personal desktop app.
- Perform native visual QA before declaring the browser UI replaceable.

## 状态

completed

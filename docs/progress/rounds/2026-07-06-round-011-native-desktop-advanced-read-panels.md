# 2026-07-06 Round 011 - Native Desktop Advanced Read Panels

## 本轮目标

Continue replacing Web UI usage by moving advanced read-only developer/audit panels into the native Tkinter desktop app.

## 背景原因

The native desktop app already covers daily archive/search/export, data safety, and maintenance. The remaining browser dependency includes developer-facing advanced views such as Schema, Robot Docs, and Governance. These are low-risk read-only surfaces, so they can be migrated before write-capable advanced actions.

## 修改范围

- Added desktop gateway methods for Schema summaries, Robot Docs, and Governance status.
- Added Advanced-tab controls for schema name lookup, robot docs, and governance status.
- Updated robot/capability metadata to include the new desktop Store interfaces.
- Updated tests, version metadata, and documentation.

## 实施步骤

1. Added `schema_summary()` over `schema_names()` and `get_schema()`.
2. Added `robot_docs_summary()` over `robot_guide()` and `robot_schemas()`.
3. Added `governance_summary()` over `ArchiveStore.governance_status()`.
4. Added compact Advanced-tab buttons that render results into the existing text panel.
5. Left schema write and governance/audit write operations out of this round.

## 关键决策

- Kept the Advanced tab read-only to avoid accidental file writes or audit changes.
- Reused existing project contracts instead of inventing desktop-specific schema/governance logic.
- Kept the UI minimal: one schema input, three buttons, one output panel.

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

- Expanded related regression: `42 passed`
- Ruff passed for the touched desktop/CLI/store/Web UI compatibility/test surface.

## 文档更新

- Updated README current version and desktop quick start wording.
- Updated architecture with the advanced desktop Store interfaces.
- Updated Chinese usage manual with advanced read-only panel behavior.
- Updated changelog, progress overview, and document index.

## 风险与遗留问题

- Schema write is still command/Web UI based.
- Governance/audit write and preflight workflows still need native confirmation gates.
- Native visual QA remains manual; this round validated data contracts and compatibility tests.

## 下一步计划

- Add native audit/governance read-only lists beyond status.
- Design schema-write confirmation if a native write path is still needed.
- Design restore-apply and governance write gates separately.

## 状态

completed

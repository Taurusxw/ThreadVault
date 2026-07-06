# 2026-07-06 Round 012 - Native Desktop Restore Apply

## 本轮目标

Move the safest restore apply workflow into the native desktop app while preserving restore safety gates.

## 背景原因

The desktop app already supports backup, backup verification, and read-only restore planning. To further reduce Web UI dependency, the next step is a conservative restore apply path that does not overwrite existing databases.

## 修改范围

- Added desktop gateway support for restore apply into a new target database.
- Added Safety-tab restore apply button with native confirmation.
- Added refusal behavior when the target database already exists.
- Updated tests, version metadata, and documentation.

## 实施步骤

1. Added `restore_to_new_target()` in `DesktopDataGateway`.
2. Reused `ArchiveStore.restore(..., apply=True, overwrite=False)`.
3. Refused target paths that already exist before calling restore.
4. Added a native confirmation prompt in the Tkinter Safety tab.
5. Added tests for successful restore apply and refused overwrite.

## 关键决策

- Desktop restore apply only supports non-overwrite targets in this round.
- Existing-target overwrite remains command-based until a full native confirmation flow is designed.
- Missing-manifest restores are not enabled from the desktop path.

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

- Updated README current version and desktop restore safety wording.
- Updated architecture with restore in the desktop Store interface.
- Updated Chinese usage manual with the non-overwrite restore apply behavior.
- Updated changelog, progress overview, and document index.

## 风险与遗留问题

- Overwrite restore is still not available from the native desktop app.
- Schema write and governance/audit write operations still need native confirmation gates.
- Native visual QA remains manual; this round validated data contracts and compatibility tests.

## 下一步计划

- Decide whether native overwrite restore is needed; if yes, require target preview, pre-restore backup, and explicit overwrite confirmation.
- Add schema-write confirmation if native schema export is still needed.
- Continue replacing remaining governance/audit write surfaces.

## 状态

completed

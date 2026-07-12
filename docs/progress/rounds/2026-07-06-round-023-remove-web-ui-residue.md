# 2026-07-06 Round 023 Remove Web UI Residue

## 本轮目标

Remove the remaining active Web UI residue after the 1.0.0 native desktop release.

## 背景原因

The native desktop app is now the primary local interface. The old browser Web UI runtime and schemas were removed in 1.0.0, but active discovery metadata, a redirecting legacy launcher, and a legacy readiness test still remained in the current tree.

## 修改范围

- Removed active launcher/test residue.
- Removed Web UI retired-interface metadata from capabilities and robot docs.
- Updated current docs to describe native desktop as the only active local UI path.
- Bumped package metadata to `1.0.1`.

## 实施步骤

1. Deleted `启动ThreadVault中文界面.cmd`.
2. Deleted `tests/test_v401_personal_ui_readiness.py`.
3. Removed `personal_web_ui`, `retired_commands`, `retired_interfaces`, and legacy fallback discovery keys from `src/threadvault/store.py`.
4. Updated desktop discovery tests to assert the Web UI residue is absent.
5. Updated README, development, API, architecture, knowledge graph, rules, usage, progress, changelog, and document index docs.

## 关键决策

- Preserved historical v4 records under `docs/progress/archive/legacy-v4/`.
- Did not delete local generated/private output directories such as `threadvault-ui-output/` or `threadvault-ui-backups/`.
- Kept the optional read-only shared server prototype because it is a governance surface, not the abandoned browser Web UI.

## 修改清单

- `src/threadvault/store.py`
- `tests/test_v407_desktop_app.py`
- `pyproject.toml`
- `src/threadvault/__init__.py`
- `README.md`
- `AGENTS.md`
- `docs/CHANGELOG.md`
- `docs/PROGRESS.md`
- `docs/DOC_INDEX.md`
- `docs/DEVELOPMENT.md`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWLEDGE_GRAPH.md`
- `docs/RULES.md`
- `docs/README.md`
- `docs/TODO.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- Deleted `启动ThreadVault中文界面.cmd`
- Deleted `tests/test_v401_personal_ui_readiness.py`

## 测试与验证

Completed validation in this round:

```powershell
py -3.12 -m py_compile src\threadvault\store.py src\threadvault\schemas.py src\threadvault\cli.py src\threadvault\desktop_data.py src\threadvault\desktop_app.py
py -3.12 -m pytest tests\test_v28_capabilities_schema_contract.py tests\test_v407_desktop_app.py tests\test_v105_codex_skill_target.py -q
py -3.12 -m ruff check src\threadvault\store.py src\threadvault\schemas.py src\threadvault\cli.py src\threadvault\desktop_data.py src\threadvault\desktop_app.py tests\test_v28_capabilities_schema_contract.py tests\test_v407_desktop_app.py tests\test_v105_codex_skill_target.py
threadvault capabilities --json
threadvault robot-docs guide --json
threadvault desktop smoke --json
py -3.12 -m pytest
py -3.12 -m ruff check .
py -3.12 -c "import importlib.metadata as m, importlib.util, threadvault; print(threadvault.__version__); print(m.version('threadvault')); print(importlib.util.find_spec('threadvault.personal_ui'))"
```

Results:

- `py_compile` passed.
- Focused pytest passed with `24 passed`.
- Full pytest passed with `396 passed in 67.12s` in the final release validation pass.
- Focused and full ruff passed.
- `threadvault capabilities --json` and `threadvault robot-docs guide --json` reported `native_desktop` without Web UI retired metadata.
- `threadvault desktop smoke --json` returned `ok: true`.
- Source and installed metadata both reported `1.0.1`; `threadvault.personal_ui` import spec was `None`.

## 文档更新

Updated current standard docs and added this round record. Historical archive and release evidence were preserved.

## 风险与遗留问题

- Historical changelog, release records, roadmap, and legacy archives still mention Web UI by design.
- Local generated directories may contain private output and were not deleted.

## 下一步计划

Commit the verified `1.0.1` release state, push `master`, and publish tag/release `v1.0.1`.

## 状态

completed

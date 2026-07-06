# 2026-07-06 Round 001 Project Local Archive DB

## 本轮目标

Move the default ThreadVault archive database from the Windows AppData location to the project-local `data/threadvault.db`, while preserving and documenting custom local archive DB overrides.
Advance the active package version because this is a substantive runtime-contract improvement.

## 背景原因

The user asked to keep the local archive database inside the project directory for easier maintenance, and then support a custom local archive DB path. The existing `--db` flag already allowed one-off overrides, but the default path still resolved to AppData and the config file did not expose a stable storage override.

## 修改范围

- `src/threadvault/config.py`
- `src/threadvault/app_config.py`
- `src/threadvault/cli.py`
- `src/threadvault/personal_ui.py`
- `src/threadvault/schemas.py`
- `src/threadvault/__init__.py`
- `pyproject.toml`
- Focused config/UI tests
- Active path documentation and progress records
- `.gitignore`

## 实施步骤

1. Changed the default data directory to project-local `data/`.
2. Added archive DB resolution order: `--db`, `THREADVAULT_DB`, `[storage].archive_db`, `data/threadvault.db`.
3. Added `[storage].archive_db` parsing and display in config summary payloads.
4. Updated UI health path reporting to show the effective archive DB path.
5. Added tests for default path, environment override, config override, and UI health reporting.
6. Bumped the package version from `0.31.0` to `0.32.0`.
7. Updated active documentation and change/progress records.

## 关键决策

- Keep `--db` as the highest-priority override for explicit per-command work.
- Add `THREADVAULT_DB` for launcher/process-level overrides without editing config.
- Add `[storage].archive_db` for persistent local customization.
- Leave export output directories separate from the archive database.
- Ignore the `data/` directory in Git because the SQLite archive can contain private transcripts.
- Treat this change as `0.32.0` because it materially improves local maintenance and path configuration.

## 修改清单

- Changed default archive DB resolution to project-local `data/threadvault.db`.
- Added `THREADVAULT_DB` and `[storage].archive_db` overrides.
- Preserved `--db` as the highest-priority explicit override.
- Updated UI health path reporting and restore target defaults.
- Added config/UI tests for new path behavior.
- Bumped package version to `0.32.0`.
- Copied the existing local AppData archive DB to `data/threadvault.db`.
- Updated active docs, schema artifact, changelog, progress, and document index.

## 测试与验证

- `python -m py_compile` with Python 3.12.13 passed for touched config, CLI, UI, schema, version, and focused test files.
- Direct path smoke passed for default `data/threadvault.db`.
- Direct path smoke passed for `THREADVAULT_DB`.
- Direct path smoke passed for `[storage].archive_db`.
- Direct SQLite verification of `data/threadvault.db` found 11 sessions, 56,680 events, 244 turns, 91 warnings, and 5 projects.
- `pytest` and `ruff` could not be run because the available local interpreters did not have project dependencies installed.

## 文档更新

- Updated README path table and config example.
- Updated database, architecture, development, API, knowledge graph, Chinese usage manual, changelog, and progress docs.
- Added this round record.
- Updated `docs/DOC_INDEX.md`.

## 风险与遗留问题

- Existing AppData archive data was copied into `data/threadvault.db`; the old AppData copy was left in place.
- Users with automation that assumed the old AppData path should either copy the database or set `THREADVAULT_DB` / `[storage].archive_db`.
- Full pytest/ruff validation remains pending until dependencies are available.

## 下一步计划

Install development dependencies in a Python 3.11+ environment and run the focused pytest/ruff suite.

## 状态

completed

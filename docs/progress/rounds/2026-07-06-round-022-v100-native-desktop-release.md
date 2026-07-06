# 2026-07-06 Round 022 - v1.0.0 Native Desktop Release

## Status

completed

## Goal

Advance ThreadVault to `1.0.0` and prepare the release around the native desktop app as the primary local interface.

## Background

The major release gate required the native desktop UI to replace the browser Web UI as the primary local interface, then retire or archive the remaining Web UI source, schemas, and tests. Round 021 retired active Web UI commands but intentionally left runtime residue for a final cleanup decision.

## Scope

- Remove active `threadvault.personal_ui` runtime code.
- Remove active `personal_ui_*` schema registrations and generated schema artifacts.
- Remove active Web UI runtime tests while preserving legacy v4 historical records.
- Bump package metadata from `0.49.0` to `1.0.0`.
- Add v1.0.0 release notes and acceptance records.
- Update current docs to describe the native desktop release state.

## Implementation Steps

1. Deleted the former Web UI runtime module from the active package.
2. Removed Web UI schema contracts from `schemas.py`, generated schema artifacts, and robot schema summaries.
3. Updated discovery metadata to keep retired Web UI commands as evidence and point to `docs/progress/archive/legacy-v4/`.
4. Updated tests to assert the old runtime and schemas are absent.
5. Bumped package and source versions to `1.0.0`.
6. Updated README, rules, development, API, architecture, knowledge graph, progress, TODO, changelog, and doc index.
7. Added release records under `docs/progress/releases/v1.0.0/`.

## Key Decisions

- Delete active Web UI runtime code rather than keep it importable as residue.
- Preserve legacy v4 documentation as historical evidence instead of rewriting old phase records.
- Keep retired command strings in capabilities/robot docs for compatibility discovery, but not as active or fallback commands.

## Change List

- `src/threadvault/personal_ui.py`
- `src/threadvault/schemas.py`
- `src/threadvault/store.py`
- `src/threadvault/__init__.py`
- `pyproject.toml`
- `tests/test_v407_desktop_app.py`
- `tests/test_v28_capabilities_schema_contract.py`
- `tests/test_v402_local_ui_server.py`
- `tests/test_v403_personal_ui_workbench.py`
- `tests/test_v404_ui_action_coverage.py`
- `tests/test_v405_v4_acceptance_smoke.py`
- `tests/test_v406_ui_chinese_localization.py`
- `AGENTS.md`
- `README.md`
- `docs/`

## Tests And Verification

Release validation:

```powershell
py -3.12 -m pytest tests\test_v28_capabilities_schema_contract.py tests\test_v401_personal_ui_readiness.py tests\test_v407_desktop_app.py tests\test_v105_codex_skill_target.py -q
py -3.12 -m ruff check src\threadvault\store.py src\threadvault\schemas.py src\threadvault\cli.py src\threadvault\desktop_data.py src\threadvault\desktop_app.py tests\test_v28_capabilities_schema_contract.py tests\test_v401_personal_ui_readiness.py tests\test_v407_desktop_app.py tests\test_v105_codex_skill_target.py
threadvault capabilities --json
threadvault robot-docs guide --json
py -3.12 -c "import importlib.metadata as m, threadvault; print(threadvault.__version__); print(m.version('threadvault'))"
git diff --check
```

Results:

- `py_compile` passed for touched runtime modules.
- Focused release tests passed: `28 passed`.
- Focused ruff passed.
- Full test suite passed: `400 passed in 58.78s`.
- Full ruff passed.
- CLI capability, robot docs, schema list, and desktop smoke checks passed.
- Version metadata reported `1.0.0`; `threadvault.personal_ui` import spec was `None`.
- CLI help confirmed there is no active `ui` command.
- `git diff --check` passed with only Windows line-ending warnings.

## Documentation Updates

- Current docs now describe the 1.0.0 native desktop release state.
- Legacy v4 records remain archived under `docs/progress/archive/legacy-v4/`.
- Release notes and acceptance records were added under `docs/progress/releases/v1.0.0/`.

## Risks And Follow-Up

- `py -3.12 -m pip check` still reports unrelated environment dependency issues for Selenium/Trio/wsproto and an invalid `~hreadvault` distribution warning.
- Historical git commits may still contain old planning artifacts; this release does not rewrite history.
- Some low-frequency write operations remain CLI-first until they have native confirmation and target-path gates.

## Next Step

Create the release commit/tag and push or publish it after reviewing the mixed worktree.

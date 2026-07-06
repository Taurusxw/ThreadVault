# 2026-07-06 Round 021 - Web UI Command Retirement

## Status

completed

## Goal

Retire the active browser Web UI entrypoints so ThreadVault moves closer to the 1.0.0 native desktop-only local app direction.

## Background

Round 020 made native desktop the primary discoverable interface but still kept `threadvault ui serve`, `threadvault ui smoke`, and the old Chinese browser launcher as active fallback paths. The user goal is to fully abandon the web UI, so the next required step is removing those active launch paths.

## Scope

- Remove the `ui` Typer command group from the active CLI.
- Retire Web UI commands in capabilities and robot docs.
- Redirect the old Chinese Web UI launcher to the desktop launcher instead of starting a browser/server.
- Keep `personal_ui.py`, its schemas, and tests as temporary migration residue pending final archival/removal.
- Update active docs and tests.

## Implementation Steps

1. Removed the active `threadvault ui serve` and `threadvault ui smoke` command implementations from `cli.py`.
2. Updated capabilities so `ui` and `ui smoke` are absent from active command/json-output discovery.
3. Changed Web UI feature flags and robot docs from fallback to retired.
4. Added retired command metadata for historical traceability.
5. Replaced `启动ThreadVault中文界面.cmd` with a desktop redirector that does not start a browser or local Web server.
6. Updated Web UI smoke internals so historical smoke checks expect CLI retirement.
7. Updated tests to prove the web commands are retired and the old launcher does not call `ui serve`.
8. Bumped package version metadata to `0.49.0` and base contract marker to `0.8`.

## Key Decisions

- Do not delete `personal_ui.py` in this round. It still carries route/action safety contracts and tests that are useful while deciding final archival or deletion.
- Keep retired command strings in metadata as evidence only; do not expose them as active or recommended commands.
- Redirect the old Web launcher to desktop instead of leaving a broken double-click path.

## Change List

- `src/threadvault/cli.py`
- `src/threadvault/store.py`
- `src/threadvault/schemas.py`
- `src/threadvault/personal_ui.py`
- `src/threadvault/__init__.py`
- `pyproject.toml`
- `启动ThreadVault中文界面.cmd`
- `tests/test_v28_capabilities_schema_contract.py`
- `tests/test_v402_local_ui_server.py`
- `tests/test_v404_ui_action_coverage.py`
- `tests/test_v405_v4_acceptance_smoke.py`
- `tests/test_v406_ui_chinese_localization.py`
- `tests/test_v407_desktop_app.py`
- `AGENTS.md`
- `README.md`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/CHANGELOG.md`
- `docs/DEVELOPMENT.md`
- `docs/DOC_INDEX.md`
- `docs/KNOWLEDGE_GRAPH.md`
- `docs/PROGRESS.md`
- `docs/README.md`
- `docs/RULES.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- `docs/TODO.md`

## Tests And Verification

Initial focused validation:

```powershell
py -3.12 -m pytest tests\test_v402_local_ui_server.py tests\test_v404_ui_action_coverage.py tests\test_v405_v4_acceptance_smoke.py tests\test_v406_ui_chinese_localization.py tests\test_v407_desktop_app.py -q
```

Result: `33 passed`.

## Documentation Updates

- README, project rules, development guide, API guide, architecture, knowledge graph, usage manual, changelog, progress overview, TODO, and document index.
- This round record.

## Risks And Follow-Up

- `personal_ui.py`, Web UI schemas, and Web UI tests still exist as migration residue.
- Some historical Web UI action behavior is still tested directly; final 1.0.0 cleanup must decide whether to delete or archive those tests and code.
- Full regression and ruff still need to run after documentation sync.

## Next Step

Archive or delete remaining Web UI source/tests/schemas after preserving any necessary safety-contract evidence.

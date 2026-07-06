# v3 Phase 03 Acceptance: Client Overview Workflow

## Status

Accepted on 2026-07-01.

## Scope

This acceptance covers:

- `threadvault client overview --json`
- `client_overview` JSON schema
- browse and optional search payload shaping for richer clients
- discovery updates for capabilities, robot docs, schema registry, and packaged schema artifacts

## Acceptance Evidence

The Phase 03 overview confirms:

- browse mode returns recent sessions.
- default session payloads omit raw local paths.
- query mode reuses agent-facing retrieval and returns evidence-backed results.
- default search results omit metadata.
- `--local-debug` explicitly includes raw session paths and search metadata.
- actions point to existing overview, agent retrieval, and export-target commands.
- no server is required.
- no external model calls are made.

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v303_client_overview.py
py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v303_client_overview.py
```

Results:

- `tests\test_v303_client_overview.py` -> passed.
- Focused ruff -> passed.

Adjacent validation:

```powershell
py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py tests\test_v302_client_manifest.py tests\test_v303_client_overview.py
```

Result:

- Adjacent interface validation -> passed.

Manual smoke:

```powershell
threadvault client overview --db TEMP_DB --json
threadvault client overview --db TEMP_DB --query pytest --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- `threadvault client overview --db TEMP_DB --json` -> passed.
- `threadvault client overview --db TEMP_DB --query pytest --json` -> passed.
- `threadvault schemas list --json` -> passed and listed `client_overview`.
- `threadvault capabilities --json` -> passed and listed `client overview`.
- `Test-Path deep-research-report.md` -> `False`.

## Result

ThreadVault now has a local client overview workflow that richer clients can use for browse/search/export first-screen
ergonomics without duplicating parser, retrieval, or export logic.

## Deferred To Later v3 Phases

- Session detail workflow.
- Export preview workflow.
- Actual desktop, IDE, Web, or TUI shell.
- Shared server read auditing.


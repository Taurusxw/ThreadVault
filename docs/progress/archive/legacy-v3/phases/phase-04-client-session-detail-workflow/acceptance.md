# v3 Phase 04 Acceptance: Client Session Detail Workflow

## Status

Accepted on 2026-07-01.

## Scope

This acceptance covers:

- `threadvault client session --session SESSION_ID --json`
- `client_session` JSON schema
- safe session detail payload shaping for richer clients
- discovery updates for capabilities, robot docs, client manifest, schema registry, and packaged schema artifacts

## Acceptance Evidence

The Phase 04 detail workflow confirms:

- session detail validates against `client_session`.
- summary includes evidence event IDs.
- event previews are bounded by `--event-limit` and `--max-chars`.
- default output omits `raw_path` and event `file_path`.
- `--local-debug` explicitly includes raw path and file path metadata.
- actions point to existing overview, agent retrieval, export-target, and export commands.
- unknown sessions fail with a controlled CLI error.
- no server or external model is required.

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v304_client_session_detail.py
py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v304_client_session_detail.py
```

Results:

- `tests\test_v304_client_session_detail.py` -> passed.
- Focused ruff -> passed.

Adjacent validation:

```powershell
py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py tests\test_v303_client_overview.py tests\test_v304_client_session_detail.py
```

Result:

- Adjacent interface validation -> passed.

Manual smoke:

```powershell
threadvault client session --db TEMP_DB --session sess-current --json
threadvault client session --db TEMP_DB --session sess-current --local-debug --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- `threadvault client session --db TEMP_DB --session sess-current --json` -> passed.
- `threadvault client session --db TEMP_DB --session sess-current --local-debug --json` -> passed.
- `threadvault schemas list --json` -> passed and listed `client_session`.
- `threadvault capabilities --json` -> passed and listed `client session`.
- `Test-Path deep-research-report.md` -> `False`.

## Result

ThreadVault now has a local session detail workflow suitable for richer clients. It lets clients move from overview to
detail/export actions without reading raw transcript files directly.

## Deferred To Later v3 Phases

- Export preview workflow.
- Warning detail workflow.
- Shared server read auditing.
- Actual GUI/IDE/TUI shell.


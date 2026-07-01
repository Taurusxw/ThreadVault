# v3 Phase 06 Acceptance: Client Warning Detail Workflow

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

The phase is accepted when validation proves:

- `threadvault client warnings --session SESSION_ID --json` emits `client_warnings`.
- Parser warnings and privacy findings are visible in a structured client payload.
- Default output omits raw local paths.
- Local debug mode is explicit and marked in `privacy.raw_paths_included`.
- `client_warnings` exists in the schema registry and packaged schema artifacts.
- Capabilities, robot docs, and client manifest discovery advertise the workflow.
- `deep-research-report.md` remains absent.

## Validation Commands

Final validation included:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v306_client_warning_detail.py
py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v306_client_warning_detail.py
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault client warnings --db TEMP_DB --session sess-privacy --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

## Validation Results

- `threadvault schemas write --out docs\schemas --json` -> passed and wrote `client_warnings.schema.json`.
- `py -3.12 -m pytest tests\test_v306_client_warning_detail.py` -> 4 passed.
- `py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v306_client_warning_detail.py` -> passed.
- Adjacent v3 client validation:
  - `py -3.12 -m pytest tests\test_v302_client_manifest.py tests\test_v303_client_overview.py tests\test_v304_client_session_detail.py tests\test_v305_client_export_preview.py tests\test_v306_client_warning_detail.py` -> 20 passed.
- Manual smoke:
  - `threadvault client warnings --db TEMP_DB --session sess-privacy --json` -> passed.
  - `threadvault client warnings --db TEMP_DB --session sess-current --local-debug --json` -> passed.
  - `threadvault schemas list --json` -> passed.
  - `threadvault capabilities --json` -> passed.
  - `Test-Path deep-research-report.md` -> `False`.
- Final validation:
  - `py -3.12 -m ruff check .` -> passed.
  - `py -3.12 -m pytest` -> 238 passed.

## Final Result

ThreadVault v3 Phase 06 is accepted. Richer clients can now inspect session parser warnings and privacy findings through
a stable, read-only, local-first client workflow without parsing raw transcripts or exposing local paths by default.

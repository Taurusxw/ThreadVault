# v3 Phase 05 Acceptance: Client Export Preview Workflow

## Status

Accepted on 2026-07-01.

## Scope

This acceptance covers:

- `threadvault client export-preview --json`
- `client_export_preview` JSON schema
- read-only export planning over existing export target profiles
- discovery updates for capabilities, robot docs, client manifest, schema registry, and packaged schema artifacts

## Acceptance Evidence

The Phase 05 export preview confirms:

- session preview returns planned files and evidence IDs.
- project preview lists selected sessions.
- `privacy_mode = fail` marks high-risk sessions as blocked/skipped.
- preview does not create the requested output directory.
- actions point to existing `export-target` file-writing commands.
- no server or external model is required.

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v305_client_export_preview.py
py -3.12 -m ruff check src\threadvault\export_targets.py src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v305_client_export_preview.py
```

Results:

- `tests\test_v305_client_export_preview.py` -> passed.
- Focused ruff -> passed.

Adjacent validation:

```powershell
py -3.12 -m pytest tests\test_v103_export_target_manifest.py tests\test_v104_obsidian_vault_target.py tests\test_v105_codex_skill_target.py tests\test_v304_client_session_detail.py tests\test_v305_client_export_preview.py
```

Result:

- Adjacent export/client validation -> passed.

Manual smoke:

```powershell
threadvault client export-preview --db TEMP_DB --session sess-current --out TEMP_OUT --json
threadvault client export-preview --db TEMP_DB --session sess-privacy --privacy-mode fail --out TEMP_OUT --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- `threadvault client export-preview --db TEMP_DB --session sess-current --out TEMP_OUT --json` -> passed.
- `threadvault client export-preview --db TEMP_DB --session sess-privacy --privacy-mode fail --out TEMP_OUT --json` -> passed and reported blocking privacy findings.
- `threadvault schemas list --json` -> passed and listed `client_export_preview`.
- `threadvault capabilities --json` -> passed and listed `client export-preview`.
- `Test-Path deep-research-report.md` -> `False`.

## Result

ThreadVault now has a read-only export preview workflow suitable for richer clients. Clients can show planned files,
privacy risk, and evidence coverage before invoking file-writing export commands.

## Deferred To Later v3 Phases

- Warning detail workflow.
- Client-side export confirmation UX.
- Shared server export audit records.


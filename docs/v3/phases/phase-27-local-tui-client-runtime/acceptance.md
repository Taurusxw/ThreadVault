# Phase 27 Acceptance - Local TUI Client Runtime

## Status

Accepted on 2026-07-01.

## Scope

This phase accepts the first concrete richer client runtime for v3:

- local TUI runtime command
- stable `client_tui_runtime` JSON contract
- Rich/text rendering for non-JSON use
- discovery/schema/gap-audit integration

## Validation

Schema generation:

```powershell
threadvault schemas write --out docs\schemas --json
```

Result:

- Passed and wrote `docs\schemas\client_tui_runtime.schema.json`.

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v327_local_tui_client_runtime.py -q
```

Result:

- 5 passed.

Adjacent validation:

```powershell
py -3.12 -m pytest tests\test_v327_local_tui_client_runtime.py tests\test_v303_client_overview.py tests\test_v305_client_export_preview.py tests\test_v321_v3_completion_gap_audit.py tests\test_v28_capabilities_schema_contract.py -q
```

Result:

- 22 passed.

Additional updated historical client/server/governance tests:

```powershell
py -3.12 -m pytest tests\test_v302_client_manifest.py tests\test_v304_client_session_detail.py tests\test_v306_client_warning_detail.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py -q
```

Result:

- 27 passed.

Manual smoke:

```powershell
threadvault import --db TEMP_DB --codex-home tests\fixtures\codex_home --json
threadvault client tui --db TEMP_DB --json
threadvault client tui --db TEMP_DB --query pytest --json
threadvault client tui --db TEMP_DB --export-preview-session sess-current --out TEMP_OUT --json
threadvault client tui --db TEMP_DB --query pytest --export-preview-session sess-current
threadvault governance v3 gap-audit --json
Test-Path deep-research-report.md
```

Results:

- `client tui --json` returned `client_tui_runtime.v1`.
- Query mode returned search rows with hybrid retrieval diagnostics from the existing client overview path.
- Export preview mode embedded `client_export_preview.v1`, planned files, and `writes_files = false`.
- Non-JSON mode rendered ThreadVault, Sessions, Search, and Export Preview sections.
- v3 gap audit returned `accepted_phase_count = 27`, `current_phase = phase-27-local-tui-client-runtime`,
  `richer_client_runtime.status = accepted_minimal_tui_runtime`, and `v3_complete = false`.
- `Test-Path deep-research-report.md` returned `False`.

Final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Results:

- Ruff passed.
- Full pytest passed: 343 passed.

## Result

Phase 27 is accepted as the minimal local TUI client runtime.

This removes the richer-client runtime blocker but does not complete v3. Remaining blockers include identity actor
binding implementation, centralized policy store implementation, centralized audit store implementation, centralized
backup/restore policy implementation, broader automatic governance instrumentation, and final v3 acceptance smoke.

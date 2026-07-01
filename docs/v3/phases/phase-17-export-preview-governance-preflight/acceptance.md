# v3 Phase 17 Acceptance: Export Preview Governance Preflight

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

Phase 17 adds an explicit export-preview preflight workflow:

- `threadvault governance preflight export-preview`
- JSON schema `governance_export_preview_preflight`
- Packaged schema artifact `docs/schemas/governance_export_preview_preflight.schema.json`

The workflow covers `threadvault client export-preview` only. It reuses the Phase 10 command inventory, Phase 09
permission logic, and Phase 11 dry-run enforcement shape. It does not execute the client export-preview command and does
not return preview payloads, manifests, privacy findings, export files, or local metadata.

The accepted payload reports:

- `business_command_executed = false`
- `preview_generated = false`
- `manifest_returned = false`
- `files_written = false`
- `local_metadata_returned = false`
- `server_required = false`
- `cloud_sync = false`

Discovery surfaces now advertise:

- capabilities JSON output `governance preflight export-preview`
- feature flag `governance_export_preview_preflight`
- robot guide schema `governance_export_preview_preflight`
- robot schema entry `governance_export_preview_preflight`

## Validation

Completed schema generation:

```powershell
threadvault schemas write --out docs\schemas --json
```

Result:

- passed and wrote `governance_export_preview_preflight.schema.json`

Completed focused validation:

```powershell
py -3.12 -m pytest tests\test_v317_export_preview_governance_preflight.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v317_export_preview_governance_preflight.py
```

Results:

- `tests\test_v317_export_preview_governance_preflight.py` -> 6 passed.
- Focused ruff -> passed.

Completed adjacent governance/discovery validation:

```powershell
py -3.12 -m pytest tests\test_v317_export_preview_governance_preflight.py tests\test_v316_summary_search_governance_preflight.py tests\test_v315_raw_read_governance_preflight.py tests\test_v313_export_backup_governance_preflight.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v310_governance_enforcement_gaps.py tests\test_v28_capabilities_schema_contract.py
```

Result:

- Adjacent governance/discovery validation -> 40 passed.

Completed manual smoke:

```powershell
threadvault governance preflight export-preview --command "threadvault client export-preview" --role reviewer --json
threadvault governance preflight export-preview --command "threadvault client export-preview" --role reader --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- Reviewer export-preview preflight returned `preflight_status = would_allow`.
- Reader export-preview preflight returned `preflight_status = would_block`.
- `threadvault schemas list --json` listed `governance_export_preview_preflight`.
- `threadvault capabilities --json` advertised `governance preflight export-preview`.
- `Test-Path deep-research-report.md` -> `False`.

Completed final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Results:

- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 298 passed.

## Deferred

- Automatic instrumentation of `threadvault client export-preview`.
- Automatic instrumentation of direct export and export-target commands.
- Server identity, centralized policy storage, centralized audit retention, and shared deployment enforcement.

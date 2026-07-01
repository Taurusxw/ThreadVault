# v3 Phase 15 Acceptance: Raw Read Governance Preflight

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

Phase 15 adds an explicit raw-read preflight workflow:

- `threadvault governance preflight raw-read`
- JSON schema `governance_raw_read_preflight`
- Packaged schema artifact `docs/schemas/governance_raw_read_preflight.schema.json`

The workflow covers `threadvault client session` only. It reuses the Phase 10 command inventory, Phase 09 permission
logic, and Phase 11 dry-run enforcement shape. It does not execute the client session command and does not return raw
transcripts, event previews, or local metadata.

The accepted payload reports:

- `business_command_executed = false`
- `raw_transcript_returned = false`
- `event_preview_returned = false`
- `local_metadata_returned = false`
- `server_required = false`
- `cloud_sync = false`

Discovery surfaces now advertise:

- capabilities JSON output `governance preflight raw-read`
- feature flag `governance_raw_read_preflight`
- robot guide schema `governance_raw_read_preflight`
- robot schema entry `governance_raw_read_preflight`

## Validation

Completed schema generation:

```powershell
threadvault schemas write --out docs\schemas --json
```

Result:

- passed and wrote `governance_raw_read_preflight.schema.json`

Completed focused validation:

```powershell
py -3.12 -m pytest tests\test_v315_raw_read_governance_preflight.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v315_raw_read_governance_preflight.py
```

Results:

- `tests\test_v315_raw_read_governance_preflight.py` -> 6 passed.
- Focused ruff -> passed.

Completed adjacent governance/discovery validation:

```powershell
py -3.12 -m pytest tests\test_v315_raw_read_governance_preflight.py tests\test_v314_restore_retention_governance_preflight.py tests\test_v313_export_backup_governance_preflight.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v310_governance_enforcement_gaps.py tests\test_v28_capabilities_schema_contract.py
```

Result:

- Adjacent governance/discovery validation -> 33 passed.

Completed manual smoke:

```powershell
threadvault governance preflight raw-read --command "threadvault client session" --role owner --json
threadvault governance preflight raw-read --command "threadvault client session" --role reader --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- Owner raw-read preflight returned `preflight_status = would_allow`.
- Reader raw-read preflight returned `preflight_status = would_block`.
- `threadvault schemas list --json` listed `governance_raw_read_preflight`.
- `threadvault capabilities --json` advertised `governance preflight raw-read`.
- `Test-Path deep-research-report.md` -> `False`.

Completed final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Results:

- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 285 passed.

## Deferred

- Automatic instrumentation of `threadvault client session`.
- Summary/search read preflight for retrieval, agent retrieval, and warning details.
- Server identity, centralized policy storage, centralized audit retention, and shared deployment enforcement.

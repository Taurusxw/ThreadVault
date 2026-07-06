# v3 Phase 16 Acceptance: Summary/Search Governance Preflight

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

Phase 16 adds an explicit summary/search preflight workflow:

- `threadvault governance preflight summary-search`
- JSON schema `governance_summary_search_preflight`
- Packaged schema artifact `docs/schemas/governance_summary_search_preflight.schema.json`

The workflow covers only Phase 10 commands mapped to `read_summary_search`:

- `threadvault client warnings`
- `threadvault agent retrieve`
- `threadvault retrieval query`
- `threadvault retrieval hybrid`

It reuses the Phase 10 command inventory, Phase 09 permission logic, and Phase 11 dry-run enforcement shape. It does not
execute retrieval or client warning commands and does not return search results, warning details, snippets, or local
metadata.

The accepted payload reports:

- `business_command_executed = false`
- `search_executed = false`
- `retrieval_results_returned = false`
- `warning_details_returned = false`
- `local_metadata_returned = false`
- `server_required = false`
- `cloud_sync = false`

Discovery surfaces now advertise:

- capabilities JSON output `governance preflight summary-search`
- feature flag `governance_summary_search_preflight`
- robot guide schema `governance_summary_search_preflight`
- robot schema entry `governance_summary_search_preflight`

## Validation

Completed schema generation:

```powershell
threadvault schemas write --out docs\schemas --json
```

Result:

- passed and wrote `governance_summary_search_preflight.schema.json`

Completed focused validation:

```powershell
py -3.12 -m pytest tests\test_v316_summary_search_governance_preflight.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v316_summary_search_governance_preflight.py
```

Results:

- `tests\test_v316_summary_search_governance_preflight.py` -> 7 passed.
- Focused ruff -> passed.

Completed adjacent governance/discovery validation:

```powershell
py -3.12 -m pytest tests\test_v316_summary_search_governance_preflight.py tests\test_v315_raw_read_governance_preflight.py tests\test_v314_restore_retention_governance_preflight.py tests\test_v313_export_backup_governance_preflight.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v310_governance_enforcement_gaps.py tests\test_v28_capabilities_schema_contract.py
```

Result:

- Adjacent governance/discovery validation -> 40 passed.

Completed manual smoke:

```powershell
threadvault governance preflight summary-search --command "threadvault retrieval query" --role reader --json
threadvault governance preflight summary-search --command "threadvault unknown" --role reader --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- Reader summary/search preflight for retrieval query returned `preflight_status = would_allow`.
- Unknown command returned structured `preflight_status = unknown_command`.
- `threadvault schemas list --json` listed `governance_summary_search_preflight`.
- `threadvault capabilities --json` advertised `governance preflight summary-search`.
- `Test-Path deep-research-report.md` -> `False`.

Completed final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Results:

- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 292 passed.

## Deferred

- Automatic instrumentation of retrieval, agent retrieval, and client warning commands.
- Export-preview governance preflight or instrumentation.
- Server identity, centralized policy storage, centralized audit retention, and shared deployment enforcement.

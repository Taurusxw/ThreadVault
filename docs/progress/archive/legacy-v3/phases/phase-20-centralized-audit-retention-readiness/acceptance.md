# v3 Phase 20 Acceptance: Centralized Audit Retention Readiness

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

Phase 20 adds an explicit centralized audit retention readiness workflow:

- `threadvault governance audit centralized-readiness`
- JSON schema `governance_centralized_audit_readiness`
- Packaged schema artifact `docs/schemas/governance_centralized_audit_readiness.schema.json`

The workflow reports the gap between local JSONL audit records and future shared/server audit retention without
implementing a centralized audit store, starting a server, migrating local logs, or changing local-first CLI defaults.

The accepted default payload reports:

- `overall_status = not_ready_for_centralized_audit`
- `server_required = false`
- `server_opt_in = true`
- `cloud_sync = false`
- `local_audit.available = true`
- `local_audit.local_only = true`
- `centralized_audit.store_implemented = false`
- `safe_to_keep_local_jsonl_audit = true`
- `safe_to_enable_centralized_audit = false`
- `safe_to_enable_shared_audit_retention = false`

Required blockers are present for centralized audit store, actor binding, append-only integrity, audit retention policy,
audit review workflow, audit backup/export policy, and automatic audit instrumentation.

Discovery surfaces now advertise:

- capabilities JSON output `governance audit centralized-readiness`
- feature flag `governance_centralized_audit_readiness`
- robot guide schema `governance_centralized_audit_readiness`
- robot schema entry `governance_centralized_audit_readiness`

## Validation

Completed schema generation:

```powershell
threadvault schemas write --out docs\schemas --json
```

Result:

- passed and wrote `governance_centralized_audit_readiness.schema.json`

Completed focused validation:

```powershell
py -3.12 -m pytest tests\test_v320_centralized_audit_readiness.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v320_centralized_audit_readiness.py
```

Results:

- `tests\test_v320_centralized_audit_readiness.py` -> 4 passed.
- Focused ruff -> passed.

Completed adjacent governance/discovery validation:

```powershell
py -3.12 -m pytest tests\test_v320_centralized_audit_readiness.py tests\test_v319_server_policy_readiness.py tests\test_v308_local_audit_log.py tests\test_v28_capabilities_schema_contract.py
```

Result:

- Adjacent governance/discovery validation -> 17 passed.

Completed manual smoke:

```powershell
threadvault governance audit centralized-readiness --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- Centralized audit readiness returned `overall_status = not_ready_for_centralized_audit`.
- `threadvault schemas list --json` listed `governance_centralized_audit_readiness`.
- `threadvault capabilities --json` advertised `governance audit centralized-readiness`.
- `Test-Path deep-research-report.md` -> `False`.

Completed final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Results:

- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 312 passed.

## Deferred

- Centralized audit store implementation.
- Identity-bound server audit records.
- Automatic business command audit instrumentation.
- Audit retention enforcement and migration from local JSONL.

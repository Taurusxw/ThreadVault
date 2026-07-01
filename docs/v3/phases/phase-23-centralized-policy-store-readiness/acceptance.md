# v3 Phase 23 Acceptance: Centralized Policy Store Readiness

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

Phase 23 adds an explicit centralized policy store readiness workflow:

- `threadvault governance policy central-readiness`
- JSON schema `governance_central_policy_readiness`
- Packaged schema artifact `docs/schemas/governance_central_policy_readiness.schema.json`

The workflow reports readiness for central policy store, policy adapter interface, policy versioning, policy provenance,
policy migration, rollback, identity dependency, and local fallback behavior without implementing a central policy store,
server runtime, policy loader, or automatic enforcement.

The accepted default payload reports:

- `overall_status = not_ready_for_central_policy_store`
- `central_policy_ready = false`
- `team_enforcement_ready = false`
- `current_permissions_enforced = false`
- `server_required = false`
- `server_opt_in = true`
- `cloud_sync = false`
- `safe_to_keep_local_cli = true`
- `safe_to_use_local_static_policy = true`
- `safe_to_enable_central_policy_store = false`
- `safe_to_enable_team_enforcement = false`

Required blockers are present for central policy store, policy adapter, policy versioning, policy provenance, policy
migration, policy rollback, identity/actor binding dependency, and automatic policy enforcement.

The accepted payload explicitly records that local governance role vocabulary and permission preflight are available, but
they are insufficient for shared enforcement without central policy and identity-bound role resolution.

Discovery surfaces now advertise:

- capabilities JSON output `governance policy central-readiness`
- feature flag `governance_central_policy_readiness`
- robot guide schema `governance_central_policy_readiness`
- robot schema entry `governance_central_policy_readiness`

## Validation

Completed schema generation:

```powershell
threadvault schemas write --out docs\schemas --json
```

Result:

- passed and wrote `governance_central_policy_readiness.schema.json`

Completed focused validation:

```powershell
py -3.12 -m pytest tests\test_v323_central_policy_store_readiness.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v323_central_policy_store_readiness.py
```

Results:

- `tests\test_v323_central_policy_store_readiness.py` -> 4 passed.
- Focused ruff -> passed.

Completed adjacent governance/discovery validation:

```powershell
py -3.12 -m pytest tests\test_v323_central_policy_store_readiness.py tests\test_v322_identity_actor_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v28_capabilities_schema_contract.py
```

Result:

- Adjacent governance/discovery validation -> 17 passed.

Completed manual smoke:

```powershell
threadvault governance policy central-readiness --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- Central policy readiness returned `overall_status = not_ready_for_central_policy_store`.
- `threadvault schemas list --json` listed `governance_central_policy_readiness`.
- `threadvault capabilities --json` advertised `governance policy central-readiness`.
- `Test-Path deep-research-report.md` -> `False`.

Completed final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Results:

- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 324 passed.

## Deferred

- Centralized policy store implementation.
- Policy adapter interface implementation.
- Policy versioning and provenance enforcement.
- Policy migration and rollback tooling.
- Identity-bound central policy enforcement.
- Automatic business command instrumentation.

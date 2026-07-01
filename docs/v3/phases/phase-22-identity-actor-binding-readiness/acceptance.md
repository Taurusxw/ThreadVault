# v3 Phase 22 Acceptance: Identity Actor Binding Readiness

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

Phase 22 adds an explicit identity and actor binding readiness workflow:

- `threadvault governance identity actor-readiness`
- JSON schema `governance_identity_actor_readiness`
- Packaged schema artifact `docs/schemas/governance_identity_actor_readiness.schema.json`

The workflow reports readiness for identity provider, actor binding, role mapping, request attribution, audit actor
provenance, and local actor fallback policy without implementing authentication, server request context, team role
directories, or automatic command instrumentation.

The accepted default payload reports:

- `overall_status = not_ready_for_identity_binding`
- `identity_binding_ready = false`
- `team_enforcement_ready = false`
- `current_permissions_enforced = false`
- `server_required = false`
- `server_opt_in = true`
- `cloud_sync = false`
- `safe_to_keep_local_cli = true`
- `safe_to_use_manual_local_actor_labels = true`
- `safe_to_enable_shared_identity_binding = false`
- `safe_to_enable_team_enforcement = false`

Required blockers are present for identity provider, actor binding, role mapping, request attribution, audit actor
provenance, and actor fallback policy.

The accepted payload explicitly records that manual local actor labels and the local audit actor field are available, but
they are insufficient for shared enforcement or authenticated actor provenance.

Discovery surfaces now advertise:

- capabilities JSON output `governance identity actor-readiness`
- feature flag `governance_identity_actor_readiness`
- robot guide schema `governance_identity_actor_readiness`
- robot schema entry `governance_identity_actor_readiness`

## Validation

Completed schema generation:

```powershell
threadvault schemas write --out docs\schemas --json
```

Result:

- passed and wrote `governance_identity_actor_readiness.schema.json`

Completed focused validation:

```powershell
py -3.12 -m pytest tests\test_v322_identity_actor_readiness.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v322_identity_actor_readiness.py
```

Results:

- `tests\test_v322_identity_actor_readiness.py` -> 4 passed.
- Focused ruff -> passed.

Completed adjacent governance/discovery validation:

```powershell
py -3.12 -m pytest tests\test_v322_identity_actor_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v28_capabilities_schema_contract.py
```

Result:

- Adjacent governance/discovery validation -> 17 passed.

Completed manual smoke:

```powershell
threadvault governance identity actor-readiness --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- Identity actor readiness returned `overall_status = not_ready_for_identity_binding`.
- `threadvault schemas list --json` listed `governance_identity_actor_readiness`.
- `threadvault capabilities --json` advertised `governance identity actor-readiness`.
- `Test-Path deep-research-report.md` -> `False`.

Completed final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Results:

- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 320 passed.

## Deferred

- Identity provider implementation.
- Actor binding middleware or server request context.
- Team role mapping directory.
- Automatic actor-bound audit instrumentation.
- Shared/server enforcement.

# v3 Phase 19 Acceptance: Server Policy Readiness

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

Phase 19 adds an explicit server/team policy readiness workflow:

- `threadvault governance server policy-readiness`
- JSON schema `governance_server_policy_readiness`
- Packaged schema artifact `docs/schemas/governance_server_policy_readiness.schema.json`

The workflow reports readiness for optional server and shared team enforcement without starting a server, implementing
identity providers, loading centralized policy, or changing local-first CLI defaults.

The accepted default payload reports:

- `overall_status = not_ready_for_shared_enforcement`
- `server_required = false`
- `server_available = false`
- `server_opt_in = true`
- `cloud_sync = false`
- `safe_to_keep_local_cli = true`
- `safe_to_enable_server_mode = false`
- `safe_to_enable_team_enforcement = false`

Required blockers are present for identity provider, actor binding, role mapping, central policy storage, policy
versioning, automatic command instrumentation, centralized audit retention, centralized backup/restore policy, and
outbound external model policy.

Discovery surfaces now advertise:

- capabilities JSON output `governance server policy-readiness`
- feature flag `governance_server_policy_readiness`
- robot guide schema `governance_server_policy_readiness`
- robot schema entry `governance_server_policy_readiness`

## Validation

Completed schema generation:

```powershell
threadvault schemas write --out docs\schemas --json
```

Result:

- passed and wrote `governance_server_policy_readiness.schema.json`

Completed focused validation:

```powershell
py -3.12 -m pytest tests\test_v319_server_policy_readiness.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v319_server_policy_readiness.py
```

Results:

- `tests\test_v319_server_policy_readiness.py` -> 4 passed.
- Focused ruff -> passed.

Completed adjacent governance/discovery validation:

```powershell
py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v318_external_model_governance_preflight.py tests\test_v312_governance_policy_readiness.py tests\test_v28_capabilities_schema_contract.py
```

Result:

- Adjacent governance/discovery validation -> 20 passed.

Completed manual smoke:

```powershell
threadvault governance server policy-readiness --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- Server policy readiness returned `overall_status = not_ready_for_shared_enforcement`.
- `threadvault schemas list --json` listed `governance_server_policy_readiness`.
- `threadvault capabilities --json` advertised `governance server policy-readiness`.
- `Test-Path deep-research-report.md` -> `False`.

Completed final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Results:

- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 308 passed.

## Deferred

- Server runtime.
- Identity providers and actor binding.
- Centralized policy storage and versioned policy loading.
- Centralized audit retention.
- Automatic business command instrumentation.

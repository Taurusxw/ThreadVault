# v3 Phase 18 Acceptance: External Model Governance Preflight

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

Phase 18 adds an explicit external-model preflight workflow:

- `threadvault governance preflight external-model`
- JSON schema `governance_external_model_preflight`
- Packaged schema artifact `docs/schemas/governance_external_model_preflight.schema.json`

The workflow covers `external model adapters` only. It reuses the Phase 10 command inventory, Phase 09 permission logic,
and Phase 11 dry-run enforcement shape. It does not implement adapters, execute network calls, send outbound payloads, or
return provider/model responses.

The accepted payload reports:

- `business_command_executed = false`
- `external_call_executed = false`
- `payload_sent = false`
- `model_response_returned = false`
- `provider_metadata_returned = false`
- `server_required = false`
- `cloud_sync = false`

The `outbound_policy` block reports that future execution requires explicit opt-in, outbound data policy, privacy scan,
redaction or fail policy, evidence validation, shared-mode human consent, and shared-mode provider allowlisting.

Discovery surfaces now advertise:

- capabilities JSON output `governance preflight external-model`
- feature flag `governance_external_model_preflight`
- robot guide schema `governance_external_model_preflight`
- robot schema entry `governance_external_model_preflight`

## Validation

Completed schema generation:

```powershell
threadvault schemas write --out docs\schemas --json
```

Result:

- passed and wrote `governance_external_model_preflight.schema.json`

Completed focused validation:

```powershell
py -3.12 -m pytest tests\test_v318_external_model_governance_preflight.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v318_external_model_governance_preflight.py
```

Results:

- `tests\test_v318_external_model_governance_preflight.py` -> 6 passed.
- Focused ruff -> passed after organizing `src\threadvault\store.py` imports.

Completed adjacent governance/discovery validation:

```powershell
py -3.12 -m pytest tests\test_v318_external_model_governance_preflight.py tests\test_v317_export_preview_governance_preflight.py tests\test_v316_summary_search_governance_preflight.py tests\test_v313_export_backup_governance_preflight.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v310_governance_enforcement_gaps.py tests\test_v28_capabilities_schema_contract.py
```

Result:

- Adjacent governance/discovery validation -> 40 passed.

Completed manual smoke:

```powershell
threadvault governance preflight external-model --command "external model adapters" --role reviewer --json
threadvault governance preflight external-model --command "external model adapters" --role reader --json
threadvault schemas list --json
Test-Path deep-research-report.md
```

Results:

- Reviewer external-model preflight returned `preflight_status = would_allow`.
- Reader external-model preflight returned `preflight_status = would_block`.
- `threadvault schemas list --json` listed `governance_external_model_preflight`.
- `Test-Path deep-research-report.md` -> `False`.

Completed final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Results:

- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 304 passed.

## Deferred

- Implementing external model adapters.
- Automatic instrumentation of business commands before outbound policy exists.
- Server identity, centralized policy storage, centralized audit retention, and shared deployment enforcement.

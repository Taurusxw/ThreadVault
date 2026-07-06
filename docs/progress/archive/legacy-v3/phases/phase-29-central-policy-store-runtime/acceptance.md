# Phase 29 Acceptance - Central Policy Store Runtime

## Status

Accepted on 2026-07-01.

## Scope

This phase accepts a minimal opt-in local central policy store runtime.

Accepted behavior:

- `[governance.policy] central_store = "path/to/policy.json"` can point at a local central policy document.
- `threadvault governance policy central-store --json` validates and summarizes a local policy document.
- The policy document uses contract `threadvault_central_policy.v1`.
- The runtime validates policy id, version, provenance, role definitions, access levels, and actor role bindings.
- The runtime resolves actor roles, allowed access levels, and requested operations.
- Discovery, robot guide, robot schemas, generated schemas, readiness reports, and v3 gap audit expose the accepted
  runtime.

Explicit non-goals:

- No remote/server-backed policy store is accepted.
- No database-backed policy persistence is accepted.
- No automatic business command enforcement is accepted beyond already accepted instrumentation slices.
- No centralized audit store or centralized backup/restore policy is accepted.
- Server, cloud, and team behavior remains opt-in; local-first and privacy-first defaults remain unchanged.

## Validation

- Schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_central_policy_store.schema.json`
- Focused and adjacent validation:
  - `py -3.12 -m pytest tests\test_v329_central_policy_store_runtime.py tests\test_v323_central_policy_store_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v324_central_backup_readiness.py -q` -> 22 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v329_central_policy_store_runtime.py tests\test_v323_central_policy_store_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v324_central_backup_readiness.py` -> passed
- Wider v3 validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v322_identity_actor_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v28_capabilities_schema_contract.py tests\test_v12_app_config.py tests\test_v13_config_cli.py -q` -> 72 passed
- Manual smoke:
  - `threadvault governance policy central-store --config CONFIG --actor reviewer@example --operation export_archive --json` -> passed with `policy.valid = true`, `store.available = true`, `operation_resolution.allowed = true`, and `enforcement.shared_enforcement_ready = false`
  - `threadvault governance policy central-readiness --config CONFIG --json` -> passed with `central_policy_ready = true` and `safe_to_enable_team_enforcement = false`
  - `threadvault governance server policy-readiness --config CONFIG --json` -> passed with `central_store_implemented = true` and shared enforcement still not ready
  - `threadvault governance backup central-readiness --config CONFIG --json` -> passed with central policy dependency ready and centralized backup still not ready
  - `threadvault governance v3 gap-audit --json` -> passed with `accepted_phase_count = 29`,
    `current_phase = phase-29-central-policy-store-runtime`, `blocking_count = 4`, and `v3_complete = false`
  - `Test-Path deep-research-report.md` -> `False`
- Full verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 357 passed

## Result

Phase 29 is accepted as the local central policy store runtime for v3 team governance.

The following v3 blockers remain:

- `centralized_audit_store_missing`
- `centralized_backup_restore_policy_missing`
- `automatic_governance_instrumentation_incomplete`
- `v3_acceptance_smoke_missing`

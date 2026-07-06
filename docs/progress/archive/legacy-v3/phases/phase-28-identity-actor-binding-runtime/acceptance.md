# Phase 28 Acceptance - Identity Actor Binding Runtime

## Status

Accepted on 2026-07-01.

## Scope

This phase accepts a minimal opt-in local static actor binding runtime for v3 governance.

Accepted behavior:

- `threadvault governance identity bind --actor ACTOR --json` resolves locally configured governance identity actors.
- The binding payload reports actor id, display name, source, role mapping, request metadata, and whether the actor is
  bound.
- Local static actor records are configured through `[governance.identity] actors = []`.
- Binding can optionally write a local audit record with operation `identity_actor_binding`.
- Discovery, robot guide, robot schemas, generated JSON schemas, readiness reports, and the v3 completion gap audit
  expose the accepted runtime.

Explicit non-goals:

- No authenticated identity provider is accepted in this phase.
- No centralized actor provenance store is accepted in this phase.
- No shared request context or central policy enforcement is accepted in this phase.
- Server, cloud, and team behavior remains opt-in; local-first and privacy-first defaults remain unchanged.

## Validation

- Schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_identity_actor_binding.schema.json`
- Focused validation:
  - `py -3.12 -m pytest tests\test_v328_identity_actor_binding_runtime.py -q` -> 6 passed
- Adjacent validation:
  - `py -3.12 -m pytest tests\test_v328_identity_actor_binding_runtime.py tests\test_v322_identity_actor_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v12_app_config.py tests\test_v13_config_cli.py tests\test_v28_capabilities_schema_contract.py -q` -> 51 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v322_identity_actor_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v12_app_config.py tests\test_v13_config_cli.py` -> passed
- Manual smoke:
  - `threadvault governance identity bind --config CONFIG --actor reviewer@example --command "threadvault client export-preview" --operation export_archive --target-type session --target-id sess-current --client-id threadvault-local-tui --audit-log AUDIT --json` -> passed with `binding.bound = true`, `role_mapping.roles = ["reviewer"]`, and `audit.written = true`
  - `threadvault governance audit list --log AUDIT --json` -> passed and listed operation `identity_actor_binding`
  - `threadvault governance identity actor-readiness --config CONFIG --json` -> passed with
    `identity_binding_ready = true` while preserving shared governance blockers
  - `threadvault governance v3 gap-audit --json` -> passed with `accepted_phase_count = 28`,
    `current_phase = phase-28-identity-actor-binding-runtime`, `blocking_count = 5`, and `v3_complete = false`
  - `Test-Path deep-research-report.md` -> `False`
- Full verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 351 passed

## Result

Phase 28 is accepted as the local identity actor binding prerequisite for team governance.

The following v3 blockers remain:

- `central_policy_store_missing`
- `centralized_audit_store_missing`
- `centralized_backup_restore_policy_missing`
- `automatic_governance_instrumentation_incomplete`
- `v3_acceptance_smoke_missing`

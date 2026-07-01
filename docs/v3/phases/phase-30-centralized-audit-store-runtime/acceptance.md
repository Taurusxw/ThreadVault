# Phase 30 Acceptance - Centralized Audit Store Runtime

## Status

Accepted on 2026-07-01.

## Scope

This phase accepts a minimal opt-in local centralized audit store runtime.

Accepted behavior:

- `[governance.audit] central_store = "path/to/audit.jsonl"` can point at a local centralized audit store.
- `threadvault governance audit centralized-store --action append --json` appends identity-bound audit records.
- `threadvault governance audit centralized-store --action list --json` lists centralized audit records with optional
  actor and operation filters.
- `threadvault governance audit centralized-store --action verify --json` verifies JSONL parseability, record shape,
  previous-hash continuity, and record hash correctness.
- Centralized audit records use contract `governance_centralized_audit_record.v1`.
- Discovery, robot guide, robot schemas, generated schemas, readiness reports, and v3 gap audit expose the accepted
  runtime.

Explicit non-goals:

- No remote/server-backed audit store is accepted.
- No database-backed shared audit persistence is accepted.
- No external signatures or key management are accepted.
- No retention/legal-hold/prune approval enforcement is accepted.
- No centralized audit backup/export policy is accepted.
- No broad automatic audit instrumentation is accepted.
- Server, cloud, and team behavior remains opt-in; local-first and privacy-first defaults remain unchanged.

## Validation

- Schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_centralized_audit_store.schema.json`
- Focused and adjacent validation:
  - `py -3.12 -m pytest tests\test_v330_centralized_audit_store_runtime.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v324_central_backup_readiness.py -q` -> 21 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v324_central_backup_readiness.py` -> passed
- Wider v3 validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v322_identity_actor_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v308_local_audit_log.py tests\test_v28_capabilities_schema_contract.py tests\test_v12_app_config.py tests\test_v13_config_cli.py -q` -> 81 passed
- Manual smoke:
  - `threadvault governance audit centralized-store --config CONFIG --action append --operation export_archive --actor reviewer@example --status ok --target-type session --target-id sess-current --metadata client=threadvault-local-tui --json` -> passed with `append.written = true`, `store.available = true`, and hash-chain verification ok
  - `threadvault governance audit centralized-store --config CONFIG --action list --actor reviewer@example --json` -> passed with `query.returned_count = 1`
  - `threadvault governance audit centralized-store --config CONFIG --action verify --json` -> passed with
    `verification.ok = true` and `hash_chain_valid = true`
  - `threadvault governance audit centralized-readiness --config CONFIG --json` -> passed with
    `centralized_audit_ready = true`, `store_implemented = true`, and retention/backup/instrumentation still not ready
  - `threadvault governance server policy-readiness --config CONFIG --json` -> passed with
    `audit.centralized_store_implemented = true` and shared enforcement still not ready
  - `threadvault governance backup central-readiness --config CONFIG --json` -> passed with centralized audit store
    runtime available and centralized backup still not ready
  - `threadvault governance v3 gap-audit --json` -> passed with `accepted_phase_count = 30`,
    `current_phase = phase-30-centralized-audit-store-runtime`, `blocking_count = 3`, and `v3_complete = false`
  - `Test-Path deep-research-report.md` -> `False`
- Full verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 362 passed

## Result

Phase 30 is accepted as the local centralized audit store runtime for v3 team governance.

The following v3 blockers remain:

- `centralized_backup_restore_policy_missing`
- `automatic_governance_instrumentation_incomplete`
- `v3_acceptance_smoke_missing`

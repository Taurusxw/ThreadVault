# v3 Phase 31 Acceptance: Centralized Backup/Restore Policy Runtime

## Status

Accepted on 2026-07-01.

## Scope

This phase accepts a minimal opt-in local centralized backup/restore policy runtime:

- `[governance.backup] policy = "path/to/policy.json"`
- `threadvault governance backup policy --json`
- JSON schema `governance_central_backup_policy`

Accepted behavior:

- The runtime validates local policy documents with contract `threadvault_central_backup_policy.v1`.
- The policy document covers repository shape, backup scope and cadence, restore approval, retention, legal hold,
  recovery testing, migration, and provenance.
- The command can preview allow/block decisions for:
  - `backup_archive`
  - `restore_backup`
  - `delete_or_prune`
  - `recovery_test`
  - `migrate_local_history`
- `governance backup central-readiness` recognizes the policy runtime and reports valid local policy configuration.
- `governance v3 gap-audit` removes `centralized_backup_restore_policy_missing`.
- Discovery, robot guide, robot schemas, generated schemas, readiness reports, and v3 gap audit expose the accepted
  runtime.

Explicit non-goals:

- No remote object store, cloud sync, or replication worker is accepted.
- No backup, restore, prune, legal-hold, or migration command is executed by the policy command.
- No broad automatic governance instrumentation is accepted in this phase.
- No production shared restore execution is accepted; `shared_restore_ready`, shared execution, and final v3 completion
  remain false.
- Server, cloud, and team behavior remains opt-in; local-first and privacy-first defaults remain unchanged.

## Validation

- Schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_central_backup_policy.schema.json`
- Focused validation:
  - `py -3.12 -m pytest tests\test_v331_centralized_backup_restore_policy_runtime.py -q` -> 5 passed
- Adjacent validation:
  - `py -3.12 -m pytest tests\test_v331_centralized_backup_restore_policy_runtime.py tests\test_v324_central_backup_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v327_local_tui_client_runtime.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v12_app_config.py tests\test_v13_config_cli.py tests\test_v28_capabilities_schema_contract.py -q` -> 74 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v331_centralized_backup_restore_policy_runtime.py tests\test_v324_central_backup_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v327_local_tui_client_runtime.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v325_read_only_shared_server_prototype.py` -> passed
- Wider v3 validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v322_identity_actor_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v331_centralized_backup_restore_policy_runtime.py tests\test_v308_local_audit_log.py tests\test_v28_capabilities_schema_contract.py tests\test_v12_app_config.py tests\test_v13_config_cli.py -q` -> 86 passed
- Manual smoke:
  - `threadvault governance backup policy --config CONFIG --operation restore_backup --actor maintainer@example --json`
    -> passed with `enforcement.status = would_allow`, `operation_resolution.allowed = true`, and
    `shared_execution_ready = false`
  - `threadvault governance backup policy --config CONFIG --operation restore_backup --actor reader@example --json`
    -> passed with `enforcement.status = would_block` and `operation_resolution.allowed = false`
  - `threadvault governance backup central-readiness --config CONFIG --json` -> passed with
    `central_backup_ready = true`, `shared_restore_ready = false`, `safe_to_enable_shared_restore = false`, and
    `blocking_count = 0`
  - `threadvault governance v3 gap-audit --json` -> passed with `accepted_phase_count = 31`,
    `current_phase = phase-31-centralized-backup-restore-policy-runtime`, `blocking_count = 2`, and
    `v3_complete = false`
  - `Test-Path deep-research-report.md` -> `False`
- Final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 367 passed

## Result

Phase 31 is accepted as the local centralized backup/restore policy runtime.

The following v3 blockers remain:

- `automatic_governance_instrumentation_incomplete`
- `v3_acceptance_smoke_missing`

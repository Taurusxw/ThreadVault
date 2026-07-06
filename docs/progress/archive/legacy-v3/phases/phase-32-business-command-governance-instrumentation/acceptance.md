# v3 Phase 32 Acceptance: Business Command Governance Instrumentation

## Status

Accepted on 2026-07-01.

## Scope

Phase 32 accepts broad explicit governance instrumentation across sensitive local business command families.

The accepted runtime is:

- `governance_business_command_instrumentation`
- CLI diagnostic command:
  - `threadvault governance instrumentation business-command`
- JSON schema:
  - `governance_business_command_instrumentation`

The runtime routes business commands to the existing operation-specific governance preflights and returns normalized
instrumentation evidence. When governance is enabled and the requested role is denied, instrumented command paths can
block before the business operation runs.

## Accepted Command Families

Phase 32 accepts instrumentation coverage for:

- `threadvault export`
- `threadvault export-target markdown`
- `threadvault export-target obsidian`
- `threadvault export-target skill`
- `threadvault backup`
- `threadvault restore`
- `threadvault backup-history prune`
- `threadvault restore-history prune`
- `threadvault audit-history prune`
- `threadvault client session`
- `threadvault client warnings`
- `threadvault retrieval query`
- `threadvault retrieval hybrid`
- `threadvault agent retrieve`
- existing `threadvault client export-preview`
- the external-model adapter boundary via preflight diagnostics only

Governance remains explicit through:

- `--governance-role`
- `--governance-config`
- `--governance-audit-log`
- `--governance-actor`

When those options are omitted, default local CLI behavior remains backward-compatible.

## Acceptance Evidence

- Added shared CLI helpers that call `ArchiveStore.governance_business_command_instrumentation()` instead of
  duplicating permission logic in each command.
- Added `threadvault governance instrumentation business-command` for direct diagnostic use.
- Wired explicit instrumentation into read, export, backup, restore, and retention command paths.
- Side-effecting commands run instrumentation before writing files, restoring, or pruning.
- JSON outputs include `governance_instrumentation` when explicit governance options are used.
- Blocked command paths return structured `governance_preflight_blocked` JSON and exit before side effects.
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot guide, robot schemas, readiness outputs, and v3 gap audit.
- Added `tests/test_v332_business_command_governance_instrumentation.py`.
- Updated older v3 tests that intentionally track the current phase count, blocker state, readiness diagnostics, and
  instrumentation inventory.

## Validation

- Schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_business_command_instrumentation.schema.json`
- Focused validation:
  - `py -3.12 -m pytest tests\test_v332_business_command_governance_instrumentation.py -q` -> 6 passed
  - `py -3.12 -m ruff check src\threadvault\cli.py src\threadvault\governance.py tests\test_v332_business_command_governance_instrumentation.py` -> passed
- Adjacent v3 validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v331_centralized_backup_restore_policy_runtime.py tests\test_v332_business_command_governance_instrumentation.py -q` -> 63 passed
- Final validation:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 373 passed
- Gap audit:
  - `threadvault governance v3 gap-audit --json` -> passed with `accepted_phase_count = 32`,
    `current_phase = phase-32-business-command-governance-instrumentation`, `blocking_count = 1`, and
    `v3_complete = false`

## Non-Goals Preserved

- No mandatory server or cloud behavior.
- No external model adapter execution.
- No production shared enforcement claim.
- No changes to accepted v2 retrieval, hybrid retrieval, vector indexing, or agent-facing retrieval internals.

## Remaining Work

Phase 32 leaves one v3 blocker:

- `v3_acceptance_smoke_missing`

The next phase should run the final v3 acceptance smoke across local CLI, richer client, optional read-only shared
server, governance instrumentation, audit, backup/restore policy, discovery, schemas, and local-first/privacy-first
invariants.

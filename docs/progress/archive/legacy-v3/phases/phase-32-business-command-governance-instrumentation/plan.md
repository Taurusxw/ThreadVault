# v3 Phase 32 Plan: Business Command Governance Instrumentation

## Status

Planned on 2026-07-01.

## Goal

Close the `automatic_governance_instrumentation_incomplete` v3 blocker by adding a shared business-command
instrumentation runtime and wiring it into existing sensitive CLI command families.

Phase 26 proved the pattern for `threadvault client export-preview`. Phase 32 generalizes that pattern so commands can
invoke the correct governance preflight before doing sensitive work, return structured instrumentation evidence, and
avoid side effects when governance is enabled and a role is denied.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-21-v3-completion-gap-audit/gap-audit.md`
- `docs/v3/phases/phase-26-client-export-preview-governance-instrumentation/plan.md`
- `docs/v3/phases/phase-26-client-export-preview-governance-instrumentation/acceptance.md`
- `docs/v3/phases/phase-31-centralized-backup-restore-policy-runtime/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a generic governance runtime:
  - `governance_business_command_instrumentation`
- Add JSON schema:
  - `governance_business_command_instrumentation`
- Add a diagnostic CLI entrypoint:
  - `threadvault governance instrumentation business-command`
- Route commands to existing operation-specific preflights:
  - export/backup -> `governance_export_backup_preflight`
  - restore/retention -> `governance_restore_retention_preflight`
  - raw read -> `governance_raw_read_preflight`
  - summary/search -> `governance_summary_search_preflight`
  - export preview -> existing Phase 26 export-preview preflight
  - external model adapter boundary -> `governance_external_model_preflight`
- Wire explicit governance options into sensitive business command families:
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
  - Preserve and count existing `threadvault client export-preview`
- Preserve local-first defaults:
  - omitted governance options do not change behavior
  - governance remains disabled by default
  - no server, cloud sync, or external model call is required
- Update readiness and v3 gap audit so broad business-command instrumentation is accepted while final v3 smoke remains
  pending.

## Out Of Scope

- Implementing authenticated external identity providers.
- Implementing production shared server enforcement.
- Implementing an external model summarization adapter.
- Rewriting v2 retrieval, hybrid retrieval, vector indexing, or agent-facing retrieval.
- Making governance, server, or cloud behavior mandatory for local CLI use.

## Interface Shape

Common explicit command options:

```powershell
--governance-role ROLE
--governance-config CONFIG
--governance-audit-log LOG
--governance-actor ACTOR
```

Diagnostic command:

```powershell
threadvault governance instrumentation business-command `
  --command "threadvault backup" `
  --role maintainer `
  --json
```

Expected runtime payload includes:

- `contract_version`
- `request`
- `governance`
- `command_policy`
- `instrumentation`
- `preflight`
- `audit`
- `execution`
- `diagnostics`

## Acceptance Criteria

- Default command behavior remains backward-compatible when governance options are omitted.
- Instrumented commands call the correct existing preflight before side effects.
- When governance is enabled and the role is denied, side-effecting commands return blocked instrumentation and do not
  execute the business operation.
- Read commands can return structured instrumentation evidence without changing v2 retrieval core behavior.
- Optional local audit logging records preflight evidence when `--governance-audit-log` is provided.
- Discovery, robot guide, robot schemas, generated schemas, server/audit/policy readiness, and v3 gap audit expose the
  accepted instrumentation runtime.
- `governance v3 gap-audit --json` removes `automatic_governance_instrumentation_incomplete`, increments accepted phase
  count, and keeps v3 incomplete until final acceptance smoke is implemented.
- `deep-research-report.md` remains absent.

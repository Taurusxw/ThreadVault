# v3 Phase 21 Plan: v3 Completion Gap Audit

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance v3 gap-audit --json` as a machine-readable v3 completion gap audit that maps the current
implementation to the v3 roadmap acceptance criteria.

This phase turns the remaining path to v3 completion into an explicit checklist before implementing optional shared
server/runtime slices. The audit must preserve local-first and privacy-first defaults, acknowledge accepted v2 retrieval
contracts, and identify which v3 roadmap outcomes remain incomplete.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-19-server-policy-readiness/acceptance.md`
- `docs/v3/phases/phase-20-centralized-audit-retention-readiness/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a v3 completion gap audit command:
  - `threadvault governance v3 gap-audit`
- Add JSON schema:
  - `governance_v3_completion_gap_audit`
- Report roadmap acceptance criteria status for:
  - CLI remains usable without server
  - richer client browse/search/export workflows
  - shared deployment access separation
  - audit records for sensitive operations
  - explicit external model/cloud diagnostics
- Report milestone status for `v3.0` through `v3.6`.
- Report blockers that should be resolved before v3 final acceptance.
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for completion status, blockers, discovery/schema/docs, and local-first invariants.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Implementing a server runtime.
- Implementing identity providers, actor binding, centralized policy stores, or centralized audit storage.
- Implementing automatic governance instrumentation for business commands.
- Implementing a desktop shell, VS Code/Cursor extension, Web UI, or TUI runtime.
- Changing retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval behavior.
- Marking v3 complete.

## Interface Shape

`governance_v3_completion_gap_audit` includes:

- `contract_version`
- `governance`
- `completion`
- `milestones`
- `acceptance_criteria`
- `implemented_capabilities`
- `remaining_gaps`
- `blockers`
- `recommended_next_phases`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance v3 gap-audit --json
```

## Acceptance Criteria

- The command validates against `governance_v3_completion_gap_audit`.
- Default output reports `overall_status = incomplete`.
- Default output reports `v3_complete = false`.
- Default output preserves `local_first = true`, `privacy_first = true`, `server_opt_in = true`, and `cloud_sync = false`.
- The audit marks accepted local CLI and richer client interface work as implemented.
- The audit marks optional shared deployment, identity/actor binding, centralized policy store, centralized audit store,
  centralized backup/restore policy, automatic business command instrumentation, and final v3 acceptance smoke as incomplete.
- Discovery surfaces advertise `governance_v3_completion_gap_audit`.
- `deep-research-report.md` remains absent.

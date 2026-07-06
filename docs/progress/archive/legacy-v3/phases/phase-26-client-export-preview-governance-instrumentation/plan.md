# v3 Phase 26 Plan: Client Export Preview Governance Instrumentation

## Status

Planned on 2026-07-01 before implementation.

## Source Documents Read

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/development-progress.md`

## Context

Phase 21 identified missing automatic governance instrumentation as a blocker before v3 final acceptance. Phases 13
through 18 added operation-specific governance preflight contracts, and Phase 25 added an opt-in read-only shared/server
prototype. Phase 26 connects one existing business command to its governance preflight path.

The selected command is `threadvault client export-preview`. It is a narrow read-only workflow, already has
`governance preflight export-preview`, and is safer to instrument first than write operations such as export, backup,
restore, or retention pruning.

## Scope

Add explicit opt-in governance instrumentation to `client export-preview`:

- call export-preview governance preflight from the business command path
- embed preflight and audit evidence in the client export preview payload
- optionally write a preflight audit record when an audit log is provided
- block preview generation when governance is enabled and the preflight decision denies the role

## Planned CLI Shape

Add options to `threadvault client export-preview`:

- `--governance-role ROLE`
- `--governance-config PATH`
- `--governance-audit-log PATH`
- `--governance-actor ACTOR`

The command remains backward-compatible when these options are omitted.

## Acceptance Criteria

- Default `client export-preview` output and read-only behavior remain compatible.
- Explicit governance instrumentation returns a `governance_instrumentation` object in the client payload.
- Explicit governance instrumentation reuses `governance_export_preview_preflight`.
- Optional audit logging writes a local preflight record and never marks the business command as a write.
- When governance is enabled and the role would be denied, preview generation is blocked before files are planned.
- No export files are written by preview instrumentation.
- Discovery, schemas, v3 gap audit, and docs reflect that one narrow business command slice is instrumented.
- v3 still remains incomplete until broader instrumentation and final acceptance smoke are complete.

## Out Of Scope

- Automatic instrumentation for `threadvault export`, backup, restore, retention, raw read, or external model commands.
- Central policy enforcement.
- Central audit storage.
- Identity provider or actor binding.
- Changing accepted v2 retrieval, hybrid retrieval, vector indexing, or agent retrieval.

## Validation Plan

- Focused tests for Phase 26 instrumentation.
- Adjacent tests for client export preview, export-preview preflight, v3 gap audit, and discovery contracts.
- Schema generation with `threadvault schemas write --out docs\schemas --json`.
- Manual smoke for default preview, instrumented preview, denied preview, audit listing, gap audit, schemas, and
  `deep-research-report.md` absence.
- Full `ruff` and `pytest` before acceptance.

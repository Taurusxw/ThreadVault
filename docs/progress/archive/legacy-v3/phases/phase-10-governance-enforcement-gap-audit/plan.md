# v3 Phase 10 Plan: Governance Enforcement Gap Audit

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance enforcement gaps --json` to report which existing ThreadVault commands should later call
permission preflight and audit append, without changing local command behavior in this phase.

This phase turns the governance roadmap into an actionable command-by-command gap audit.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-07-governance-baseline/design-notes.md`
- `docs/v3/phases/phase-08-local-audit-log-workflow/design-notes.md`
- `docs/v3/phases/phase-09-permission-preflight-workflow/design-notes.md`
- `docs/development-progress.md`

## In Scope

- Add a machine-readable governance enforcement gap inventory.
- Add CLI command:
  - `threadvault governance enforcement gaps`
- Add JSON schema:
  - `governance_enforcement_gaps`
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for gap coverage, default-off enforcement, discovery, and docs.
- Add a human-readable `gap-audit.md` beside the phase plan.
- Update `docs/v3/README.md` and `docs/development-progress.md`.

## Out Of Scope

- Enforcing permissions in existing commands.
- Automatically writing audit records from existing commands.
- Server runtime, team identity, or cloud sync.
- Rewriting v2 retrieval, vector, hybrid, or agent-facing interfaces.

## Interface Shape

`governance_enforcement_gaps` includes:

- `contract_version`
- `governance`
- `commands`
- `summary`
- `recommendations`
- `diagnostics`

Each command gap record includes:

- `command`
- `operation`
- `access_level`
- `audit_required`
- `current_state`
- `future_phase`
- `notes`

## Acceptance Criteria

- Gap audit covers raw read/search, export, delete/retention, restore, external-model-call readiness, and governance commands.
- Existing command enforcement remains disabled by default.
- Discovery surfaces advertise `governance_enforcement_gaps`.
- `gap-audit.md` records the command-by-command conclusion.
- `deep-research-report.md` remains absent.

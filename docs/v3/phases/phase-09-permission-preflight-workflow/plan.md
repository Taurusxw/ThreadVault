# v3 Phase 09 Plan: Permission Preflight Workflow

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance permission check --json` so clients and future server layers can preflight sensitive operations
against the governance role/access vocabulary before enforcement is wired into existing commands.

This phase expresses allow/deny decisions and optional audit records without changing local CLI behavior by default.

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
- `docs/development-progress.md`

## In Scope

- Add a permission preflight function to the governance module.
- Reuse existing role, access level, and sensitive operation vocabulary.
- Add optional audit logging of permission checks.
- Add CLI command:
  - `threadvault governance permission check`
- Add JSON schema:
  - `governance_permission_check`
- Regenerate packaged schema artifacts.
- Update capabilities, robot docs, and governance discovery.
- Add focused tests for default-off behavior, config-enabled allow/deny, optional audit, discovery, and docs.
- Update `docs/v3/README.md` and `docs/development-progress.md`.

## Out Of Scope

- Enforcing permissions in existing local commands.
- Server runtime.
- User identity, invitations, or external identity providers.
- Cloud sync.
- Rewriting retrieval, vector, hybrid, or agent-facing interfaces.

## Interface Shape

`governance_permission_check` includes:

- `contract_version`
- `request`
- `governance`
- `decision`
- `audit`
- `diagnostics`

The decision includes both `allowed` and `enforced`. When governance is disabled, `enforced` is false and local commands
remain usable, but `would_allow` still lets clients preview the future team-mode decision.

## Acceptance Criteria

- Default governance-disabled checks do not enforce denial.
- Config-enabled checks deny roles that lack the required access level.
- Config-enabled checks allow roles that include the required access level.
- Optional audit logging appends a local audit record for the check result.
- Discovery surfaces advertise `governance_permission_check`.
- `deep-research-report.md` remains absent.

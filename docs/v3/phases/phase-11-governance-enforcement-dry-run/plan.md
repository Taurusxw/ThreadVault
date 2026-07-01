# v3 Phase 11 Plan: Governance Enforcement Dry Run

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance enforcement check --json` as a dry-run interface that evaluates how a current
ThreadVault command would be treated by future governance enforcement.

This phase converts the Phase 10 command gap inventory into an operator/client-facing preflight view without changing
any existing archive, retrieval, export, backup, restore, or retention command behavior.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-08-local-audit-log-workflow/design-notes.md`
- `docs/v3/phases/phase-09-permission-preflight-workflow/design-notes.md`
- `docs/v3/phases/phase-10-governance-enforcement-gap-audit/gap-audit.md`
- `docs/development-progress.md`

## In Scope

- Add a dry-run enforcement check for one command and role.
- Reuse the Phase 10 inventory to resolve:
  - command
  - operation
  - access level
  - audit requirement
  - future enforcement phase
- Reuse Phase 09 permission logic for `would_allow`.
- Support optional explicit audit logging for the dry-run check itself.
- Add CLI command:
  - `threadvault governance enforcement check`
- Add JSON schema:
  - `governance_enforcement_check`
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for allowed, blocked, unknown-command, optional audit, and discovery behavior.
- Add acceptance documentation and update `docs/development-progress.md`.

## Out Of Scope

- Enforcing permissions inside existing business commands.
- Automatically writing audit records from export, backup, restore, retrieval, or client commands.
- Adding server runtime, identity providers, centralized policy storage, or cloud sync.
- Rewriting v2 retrieval, hybrid retrieval, vector, or agent-facing interfaces.

## Interface Shape

`governance_enforcement_check` includes:

- `contract_version`
- `request`
- `command_policy`
- `permission`
- `enforcement`
- `audit`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance enforcement check --command "threadvault export" --role reviewer --json
```

Optional audit logging:

```powershell
threadvault governance enforcement check --command "threadvault export" --role reader --audit-log audit.jsonl --json
```

## Acceptance Criteria

- The dry-run command validates against `governance_enforcement_check`.
- Known commands resolve to the Phase 10 inventory.
- Unknown commands return structured diagnostics without crashing.
- Dry-run output distinguishes:
  - governance config enabled or disabled.
  - current enforcement state.
  - future enforcement recommendation.
  - role-level `would_allow`.
  - whether the command would block if enforcement is later enabled.
- Optional audit logging records the dry-run check without enabling automatic command audit.
- Discovery surfaces advertise `governance_enforcement_check`.
- Existing business commands remain unmodified and unenforced.
- `deep-research-report.md` remains absent.

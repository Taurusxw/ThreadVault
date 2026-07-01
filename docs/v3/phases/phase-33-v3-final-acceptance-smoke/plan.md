# v3 Phase 33 Plan: v3 Final Acceptance Smoke

## Status

Planned on 2026-07-01.

## Goal

Close the final `v3_acceptance_smoke_missing` blocker by adding and running a final v3 acceptance smoke that proves the
accepted v3 scope is complete and still respects ThreadVault's local-first/privacy-first boundaries.

Phase 33 is a verification and acceptance phase. It should not broaden v3 into mandatory server, cloud, or production
shared-enforcement work.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-21-v3-completion-gap-audit/gap-audit.md`
- `docs/v3/phases/phase-32-business-command-governance-instrumentation/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a final smoke runtime:
  - `governance_v3_acceptance_smoke`
- Add a CLI entrypoint:
  - `threadvault governance v3 acceptance-smoke`
- Add JSON schema:
  - `governance_v3_acceptance_smoke`
- Verify accepted v3 roadmap criteria:
  - local CLI remains usable without server
  - richer client can browse/search/export-preview through existing interfaces
  - v2 retrieval, hybrid retrieval, vector defaults, and agent retrieval remain accepted
  - optional read-only server prototype is opt-in and read-only
  - governance distinguishes raw transcript access from summary/search access
  - sensitive command instrumentation can block before side effects
  - audit evidence can be written locally
  - centralized audit, policy, and backup/restore policy runtimes are discoverable
  - external model behavior remains explicit and disabled by default
  - schemas, robot guide, capabilities, and phase docs are present
  - `deep-research-report.md` remains absent
- Update v3 gap audit to mark v3 complete after this acceptance smoke is accepted.
- Update `docs/v3/README.md`, this phase acceptance document, and `docs/development-progress.md`.

## Out Of Scope

- Mandatory cloud sync.
- Mandatory server use for local CLI workflows.
- Production shared server enforcement.
- Authenticated external identity providers.
- External model execution.
- Rewriting v2 retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval.

## Interface Shape

Diagnostic command:

```powershell
threadvault governance v3 acceptance-smoke --db TEMP_DB --config TEMP_CONFIG --json
```

The smoke payload should include:

- `contract_version`
- `status`
- `governance`
- `checks`
- `summary`
- `criteria`
- `gap_audit`
- `diagnostics`

The smoke should return a structured failure list instead of hiding partial failures.

## Acceptance Criteria

- Focused Phase 33 tests prove the final smoke can pass on fixture data.
- The final smoke covers the v3 roadmap acceptance criteria and accepted Phase 01-32 capabilities.
- `threadvault governance v3 gap-audit --json` reports:
  - `v3_complete = true`
  - `accepted_phase_count = 33`
  - `current_phase = phase-33-v3-final-acceptance-smoke`
  - `blocking_count = 0`
- `py -3.12 -m ruff check .` passes.
- `py -3.12 -m pytest` passes.
- `deep-research-report.md` remains absent.

# v3 Phase 25 Plan: Read-Only Shared Server Prototype

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
- `docs/v3/phases/phase-21-v3-completion-gap-audit/gap-audit.md`

## Context

Phase 21 identified the missing optional shared/server runtime as a blocker before final v3 acceptance. Phases 22 through
24 made identity, central policy, and central backup/restore readiness explicit, but they did not add a runtime. Phase 25
adds the first narrow shared/server prototype without changing the local-first default or claiming team enforcement is
ready.

## Scope

Build an opt-in, read-only, loopback-friendly server prototype over existing ThreadVault interfaces:

- client manifest
- client overview
- agent retrieval
- governance status
- server policy readiness

The prototype must reuse accepted v2 retrieval and v3 client/governance modules. It must not parse Codex transcript
files directly and must not add write routes.

## Planned Interface

- Add a small `threadvault.shared_server` module.
- Expose a manifest command:
  - `threadvault governance server read-only-manifest --json`
- Expose a smoke command:
  - `threadvault governance server read-only-smoke --json`
- Expose a start command:
  - `threadvault governance server serve-read-only --enable --host 127.0.0.1 --port 8765`

The start command must require explicit `--enable`. Without that flag it must fail before binding a socket.

## Acceptance Criteria

- Local CLI remains usable without any server.
- No new mandatory dependency is introduced.
- Server startup is opt-in and defaults to loopback host guidance.
- The prototype exposes only GET-style, read-only routes.
- The route manifest maps every route to an existing ArchiveStore/client/agent/governance interface.
- The smoke workflow exercises the route handler in process and returns JSON.
- JSON schemas and discovery surfaces include the new manifest and smoke contracts.
- Phase documentation and development progress are updated.
- `deep-research-report.md` remains absent.

## Out Of Scope

- Authenticated identity provider.
- Team role mapping.
- Centralized policy storage.
- Centralized audit storage or tamper evidence.
- Centralized backup/restore repository.
- Write routes, export execution, restore execution, or retention mutation.
- Public network exposure defaults.

## Validation Plan

- Focused tests for the new shared server prototype.
- Adjacent tests for server policy readiness, v3 gap audit, client overview, and discovery contracts.
- Schema generation with `threadvault schemas write --out docs\schemas --json`.
- Manual smoke for `read-only-manifest`, `read-only-smoke`, capabilities, and schemas list.
- Full `ruff` and `pytest` before acceptance.

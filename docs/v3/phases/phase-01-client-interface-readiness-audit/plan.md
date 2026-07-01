# v3 Phase 01 Plan: Client Interface Readiness Audit

## Status

Planned and executed on 2026-07-01.

## Goal

Establish the v3 documentation entrypoint and audit whether existing ThreadVault interfaces are ready to support the
first richer client without reworking the accepted v2 retrieval core.

This phase maps the current interface surface for desktop, IDE, local Web/TUI, and optional server clients. It is a
readiness phase, not a GUI implementation phase.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/development-progress.md`

## In Scope

- Create `docs/v3/README.md` as the v3 index and development-rule entrypoint.
- Create Phase 01 planning, design notes, and acceptance documents.
- Audit the existing interfaces that clients should reuse:
  - `threadvault capabilities --json`
  - `threadvault robot-docs guide`
  - `threadvault agent manifest`
  - `threadvault agent retrieve`
  - `threadvault retrieval query`
  - `threadvault retrieval hybrid`
  - `threadvault summary-pipeline chunks`
  - `threadvault vector status`
  - `threadvault export-target ...`
- Confirm v3 keeps these defaults:
  - local-first by default.
  - vector retrieval disabled unless explicitly configured.
  - no cloud sync by default.
  - no external model calls by default.
  - no raw local paths in agent retrieval default output.
- Add a focused readiness test that fails if v3 docs disappear, if the v2 interface discovery surface regresses, or if
  local-first defaults are accidentally weakened.
- Update `docs/development-progress.md` after implementation.

## Out Of Scope

- Desktop shell implementation.
- VS Code/Cursor extension scaffolding.
- Web UI or TUI implementation.
- Server runtime implementation.
- Team permission model implementation.
- Centralized backup/restore implementation.
- Rewriting or replacing v2 retrieval, hybrid retrieval, vector adapter, or agent-facing retrieval internals.

## Interface Readiness Questions

1. Can a richer client discover supported commands and contracts without reading source code?
2. Can a client retrieve results through one stable agent-facing interface?
3. Can a client tell whether vector search is enabled without enabling it?
4. Can a client keep raw path metadata hidden unless local debugging is explicitly requested?
5. Can a future server or shared deployment distinguish read-only retrieval from export, delete, restore, and raw
   transcript access?

## Expected Deliverables

- `docs/v3/README.md`
- `docs/v3/phases/phase-01-client-interface-readiness-audit/plan.md`
- `docs/v3/phases/phase-01-client-interface-readiness-audit/design-notes.md`
- `docs/v3/phases/phase-01-client-interface-readiness-audit/acceptance.md`
- `tests/test_v301_client_interface_readiness.py`
- Updated `docs/README.md`
- Updated `docs/development-progress.md`

## Validation Plan

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v301_client_interface_readiness.py
py -3.12 -m ruff check tests\test_v301_client_interface_readiness.py
```

Adjacent interface validation:

```powershell
py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py tests\test_v301_client_interface_readiness.py
```

Manual smoke:

```powershell
threadvault capabilities --json
threadvault agent manifest --json
Test-Path deep-research-report.md
```

## Acceptance Criteria

- v3 documentation exists and names the richer-client/team-governance boundary.
- Phase 01 documents explicitly state that v3 clients must reuse existing archive/export/summary/retrieval/agent
  interfaces.
- The readiness test proves existing discovery surfaces advertise retrieval, hybrid retrieval, summary chunks, vector
  status, export targets, and agent-facing retrieval.
- The readiness test proves local-first defaults remain true and server/cloud/external model behavior remains opt-in or
  absent by default.
- `deep-research-report.md` remains absent.


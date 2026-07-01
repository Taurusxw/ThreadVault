# v3 Phase 02 Plan: Client Manifest Entrypoint

## Status

Planned and executed on 2026-07-01.

## Goal

Add the first v3 client-facing entrypoint: `threadvault client manifest --json`.

The manifest gives desktop, IDE, Web, TUI, and optional server clients one stable discovery payload for ThreadVault
client integration. It summarizes existing archive/export/summary/retrieval/vector/hybrid/agent-facing interfaces
without duplicating their implementation.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-01-client-interface-readiness-audit/design-notes.md`
- `docs/development-progress.md`

## In Scope

- Add `threadvault.client_interface` with a focused client manifest builder.
- Add `ArchiveStore.client_manifest(...)`.
- Add CLI command group:
  - `threadvault client manifest`
- Add JSON schema:
  - `client_interface_manifest`
- Add packaged schema artifact under `docs/schemas/`.
- Update capabilities and robot docs discovery.
- Add a focused Phase 02 test covering manifest contract, CLI output, schema registry, local-first defaults, and v3 docs.
- Update `docs/v3/README.md` and `docs/development-progress.md`.

## Out Of Scope

- Desktop shell implementation.
- VS Code/Cursor extension implementation.
- Web UI or TUI implementation.
- Server runtime implementation.
- Team permission enforcement.
- Centralized audit event log.
- Rewriting retrieval, hybrid retrieval, vector indexing, agent retrieval, export target, or privacy scanning.

## Interface Shape

`client_interface_manifest` should include:

- `contract_version`
- `interface`
- `client_families`
- `entrypoints`
- `schemas`
- `defaults`
- `integration_policy`
- `governance`

The manifest is a discovery payload, not a database operation. It should not open, inspect, or mutate a ThreadVault
SQLite database.

## Acceptance Criteria

- `threadvault client manifest --json` validates against `client_interface_manifest`.
- The manifest lists `desktop`, `ide`, `web`, `tui`, and `server` client families.
- Server mode is described as optional and not required by default.
- The manifest points clients to existing discovery, retrieval, export, vector, and schema entrypoints.
- Defaults preserve:
  - local-first behavior.
  - no required server.
  - no cloud sync.
  - no external model calls.
  - no raw paths in default output.
  - vector disabled by default.
- `capabilities()`, `robot_guide()`, `robot_schemas()`, and packaged schema files include the client manifest.
- `deep-research-report.md` remains absent.

## Validation Plan

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v302_client_manifest.py
py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v302_client_manifest.py
```

Adjacent validation:

```powershell
py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py tests\test_v301_client_interface_readiness.py tests\test_v302_client_manifest.py
```

Manual smoke:

```powershell
threadvault client manifest --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```


# Phase 02 / v2.1: Retrieval JSON Contracts And Diagnostics

## Summary

This phase turns the v2 `Retrieval` module from an internal FTS wrapper into a stable machine-facing retrieval contract. Phase 01 preserved the existing `threadvault search` behavior. Phase 02 adds a v2 JSON object response with diagnostics, index status, and explicit retrieval mode metadata, while keeping the older `search --json` array outputs unchanged.

The main architecture move is to make diagnostics a behavior of the `Retrieval` module, not a CLI-only decoration. CLI commands, future MCP entrypoints, and later GUI clients should all be able to consume the same response shape.

## Source Of Truth Read Before This Phase

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v2-retrieval-and-interfaces.md`
- `docs/v2/README.md`
- `docs/v1/README.md`
- `docs/v0/README.md`
- `docs/development-progress.md`

The active v2 roadmap is `docs/roadmap/v2-retrieval-and-interfaces.md`. The older goal text mentioned `docs/roadmap/v2-personal-knowledge-layer.md` and `docs/v0-v1/`; those paths do not exist in the current repository and are not used for this phase.

## Current Baseline

- `threadvault.retrieval` exposes `RetrievalQuery` and `retrieve`.
- `retrieve` currently returns `list[SearchResult]`.
- `ArchiveStore.search()` already routes through the retrieval module.
- Existing CLI search schemas remain:
  - `search_minimal`
  - `search_standard`
  - `search_full`
- Capabilities already advertise:
  - `retrieval_module: true`
  - `retrieval_modes: ["fts"]`

## Goals

- Add a stable v2 retrieval JSON object contract for agents and future clients.
- Preserve the existing `threadvault search --json` array contract.
- Expose retrieval diagnostics that explain what engine and fallback behavior were used.
- Expose FTS index status so agents can tell whether search is operating on a healthy local index.
- Keep FTS5 as the only supported mode in this phase.
- Keep vector, semantic, hybrid, MCP, REST, and GUI work out of scope.

## Non-Goals

- Do not add embeddings or vector storage.
- Do not implement semantic or hybrid ranking.
- Do not change the database schema.
- Do not change package version, JSON contract version, backup manifests, restore records, or schema version.
- Do not remove or reshape `threadvault search --json`.
- Do not expose raw transcript paths or raw payload content in diagnostics.

## Public Interface Plan

### Retrieval Module

Add a deeper retrieval response interface:

- `RetrievalDiagnostics`
  - mode requested by the caller.
  - mode actually used.
  - engine name.
  - fields profile.
  - limit.
  - filter summary.
  - fallback status.
  - rank strategy.
  - result count.
  - FTS index status.
  - warnings.
- `RetrievalResponse`
  - contract version marker for the retrieval response.
  - query summary.
  - diagnostics.
  - result list.

Keep `retrieve(conn, query)` as a compatibility helper returning `list[SearchResult]`. Add a richer function, tentatively:

```python
retrieve_response(conn, query) -> RetrievalResponse
```

The `Retrieval` module owns fallback detection and index status so the CLI does not duplicate this logic.

### Store Layer

Add a store method for the v2 object response:

```python
ArchiveStore.retrieve(...)
```

Keep `ArchiveStore.search(...)` as the v0/v1 compatibility method.

Add a diagnostics-only method:

```python
ArchiveStore.retrieval_diagnostics()
```

This gives a small seam future MCP/client code can reuse.

### CLI

Add a new `retrieval` command group:

```powershell
threadvault retrieval query QUERY --json
threadvault retrieval diagnose --json
```

The new command group is the v2 machine-facing interface. Existing search remains the human/legacy-compatible path:

```powershell
threadvault search QUERY --json --fields minimal
```

### JSON Schemas

Add two schema names:

- `retrieval_query`
- `retrieval_diagnostics`

The schemas should be strict enough to require top-level objects and key fields, but still append-only through `additionalProperties: true`.

### Capabilities And Robot Docs

Update discovery output to include:

- command: `retrieval`
- JSON outputs:
  - `retrieval query`
  - `retrieval diagnose`
- feature flag:
  - `retrieval_diagnostics: true`
- retrieval metadata:
  - default mode: `fts`
  - supported modes: `["fts"]`
  - contract schemas: `retrieval_query`, `retrieval_diagnostics`

## Implementation Steps

1. Add the phase documents before code changes:
   - `plan.md`
   - `design-notes.md`
2. Extend `threadvault.retrieval` with response and diagnostics dataclasses.
3. Keep old `retrieve` behavior by delegating to the new response function.
4. Add store methods for v2 retrieval query and diagnostics.
5. Add `threadvault retrieval query` and `threadvault retrieval diagnose`.
6. Add JSON schemas and generated schema artifacts.
7. Update `docs/THREADVAULT_USAGE_MANUAL.md` with the v2 retrieval commands.
8. Update `docs/v2/README.md` phase index.
9. Add focused tests for:
   - stable v2 retrieval query JSON object.
   - diagnostics-only command.
   - fallback metadata for awkward FTS input.
   - old `search --json` contracts staying valid.
   - capabilities and schema registry discovery.
10. Run validation and write acceptance evidence.
11. Update `docs/development-progress.md`.

## Acceptance Criteria

- `threadvault retrieval query pytest --json` emits an object, not a raw array.
- The retrieval query object includes:
  - `contract_version`
  - `query`
  - `diagnostics`
  - `results`
- Diagnostics include:
  - requested mode.
  - used mode.
  - engine.
  - result count.
  - index status.
  - fallback status.
- `threadvault retrieval diagnose --json` emits the same diagnostics shape without requiring a search query.
- `threadvault search pytest --json --fields minimal` still validates against `search_minimal`.
- `retrieval_query` and `retrieval_diagnostics` appear in schema discovery and generated files.
- Capabilities and robot docs advertise the new retrieval interface.
- Full regression tests pass.

## Validation Plan

```powershell
py -3.12 -m pytest tests\test_v202_retrieval_contracts_diagnostics.py
threadvault schemas write --out docs\schemas --json
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault retrieval query pytest --json
threadvault retrieval diagnose --json
threadvault search pytest --json --fields minimal
threadvault capabilities --json
threadvault schemas list --json
Test-Path deep-research-report.md
```

## Risks

- If diagnostics are assembled in the CLI, future MCP/client code would need to duplicate it. This phase avoids that by putting diagnostics inside `threadvault.retrieval`.
- If `search --json` is changed directly, existing v0/v1 machine consumers could break. This phase adds a new v2 object contract instead.
- If index status includes raw paths, it could expose local details to agents. This phase reports counts and health, not raw source paths.

## Next Phase

After this phase, v2 can move to summary/evidence chunk selection for optional embeddings. That should still run without embeddings and should not vectorize all raw events by default.

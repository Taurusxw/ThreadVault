# Phase 01 / v2.0 Foundation: Retrieval Module FTS Wrapper

## Goal

Create the first v2 `Retrieval` module by wrapping the existing SQLite FTS5 search path behind a small retrieval interface while preserving current `threadvault search` behavior and JSON contracts.

This phase starts v2 with a seam, not a new search product. The only active retrieval adapter is the current local SQLite FTS5 implementation. Vector and hybrid retrieval remain future phases.

## Source Context

Required context read before this plan:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v2-retrieval-and-interfaces.md`
- `docs/v1/README.md`
- `docs/v1/phases/phase-06-v1-acceptance-smoke/v1-acceptance.md`
- `docs/v0/README.md`
- `docs/development-progress.md`
- `src/threadvault/database.py`
- `src/threadvault/store.py`
- `src/threadvault/cli.py`
- `src/threadvault/schemas.py`
- `src/threadvault/models.py`
- `codebase-design` skill guidance for deep modules

## Path Correction

The v2 goal text mentioned:

- `docs/roadmap/v2-personal-knowledge-layer.md`
- `docs/v0-v1/README.md`
- `docs/v0-v1/research/codex-session-archive-research.md`

Those paths do not exist in the current repository. The authoritative current equivalents are:

- `docs/roadmap/v2-retrieval-and-interfaces.md`
- `docs/v0/README.md`
- `docs/v1/README.md`
- `docs/v0/research/codex-session-archive-research.md`

This phase uses the actual current Markdown source of truth and does not create compatibility stubs for the incorrect paths.

## Product Boundary

In scope:

- Add a new `threadvault.retrieval` module.
- Add a small retrieval interface around:
  - query string;
  - limit;
  - session/project/time/type/tool filters;
  - output field profile;
  - local FTS search mode.
- Route `ArchiveStore.search()` through the retrieval module.
- Preserve existing `threadvault search` behavior and JSON output shapes:
  - `search_minimal`
  - `search_standard`
  - `search_full`
- Preserve current fallback behavior for awkward FTS input by retrying with a quoted query.
- Advertise the new retrieval module through capabilities and robot docs.
- Add focused tests proving the retrieval module is used and CLI search contracts still pass.
- Add v2 archive/index docs and phase acceptance docs.

Out of scope:

- New user-facing retrieval CLI commands.
- Semantic/vector search.
- Hybrid ranking.
- Embedding configuration.
- MCP, REST, desktop, or IDE interfaces.
- Database schema changes.
- Search result schema changes.
- Package version changes.

## Architecture Decision

### Module

Add `threadvault.retrieval`.

External interface:

- `RetrievalQuery`
- `retrieve(conn, query: RetrievalQuery) -> list[SearchResult]`

The interface should hide:

- current `database.search_events()` details;
- FTS query retry behavior;
- the fact that only FTS5 exists in v2.0;
- future adapter room for semantic/hybrid search.

### Seam

The seam lives between `ArchiveStore.search()` and lower-level search implementation.

Callers should provide retrieval intent. They should not know whether the current adapter uses FTS5, LIKE fallback, quoted retry, vector similarity, or hybrid ranking. In v2.0 only the FTS adapter exists, but the seam is still useful because the next phases need one shared retrieval interface.

### Interface Shape

`RetrievalQuery` fields:

- `text`
- `limit`
- `session_id`
- `cwd`
- `since`
- `until`
- `top_type`
- `tool`
- `fields`
- `mode`

`mode` initially supports only `fts`. Future modes can include `semantic` and `hybrid`.

Validation rules:

- `fields` must be `minimal`, `standard`, or `full`.
- `mode` must be `fts`.
- `limit` should be clamped or rejected consistently with the CLI.

## Capabilities And Agent Discovery

Update `capabilities()`:

- add `retrieval_module: true`;
- add a `retrieval_modes` list with `["fts"]`.

Update `robot_guide()`:

- keep recommending `threadvault search QUERY --json --fields minimal`;
- mention that search is served through the retrieval module.

Update `robot_schemas()` only if useful to expose retrieval modes; do not change existing search schema contracts.

## Documentation Updates

Create/update:

- `docs/v2/README.md`
- `docs/v2/phases/phase-01-retrieval-module-fts-wrapper/plan.md`
- `docs/v2/phases/phase-01-retrieval-module-fts-wrapper/acceptance.md`
- `docs/README.md`
- `docs/development-progress.md`

Do not recreate or update `deep-research-report.md`. Do not modify the root DOCX. Keep root `README.md` short unless a compact v2 pointer becomes clearly necessary.

## Test Plan

Add focused tests, likely in `tests/test_v201_retrieval_module.py`:

- `RetrievalQuery` with `mode="fts"` returns current fixture search results.
- `ArchiveStore.search()` preserves `search_minimal`, `search_standard`, and `search_full` CLI-compatible outputs.
- filters still work through the retrieval module:
  - session id;
  - project cwd;
  - type;
  - tool.
- awkward FTS input still falls back safely through the retrieval module.
- invalid retrieval mode raises `ValueError`.
- capabilities advertise `retrieval_module: true` and `retrieval_modes: ["fts"]`.
- docs exist for the v2 phase.

Regression checks:

```powershell
py -3.12 -m pytest tests\test_v201_retrieval_module.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault search pytest --json --fields minimal
threadvault capabilities --json
threadvault schemas list --json
Test-Path deep-research-report.md
```

## Acceptance Criteria

- `threadvault.retrieval` exists and owns the retrieval interface.
- `ArchiveStore.search()` goes through the retrieval module.
- Existing `threadvault search` CLI behavior and JSON contracts remain compatible.
- The retrieval module exposes only FTS mode in v2.0.
- Capabilities advertise retrieval module availability.
- No vector, MCP, REST, GUI, server, or team features are introduced.
- Documentation makes the phase recoverable from `docs/README.md`, `docs/roadmap/`, `docs/v2/`, and `docs/development-progress.md`.

## Open Assumptions

- The current FTS5 ranking and snippet behavior remain acceptable for v2.0.
- Search output schemas remain the v0/v1 contracts for this phase.
- Retrieval diagnostics are deferred to v2.1.

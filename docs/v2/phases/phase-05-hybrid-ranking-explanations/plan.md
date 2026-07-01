# Phase 05 / v2.4: Hybrid Ranking And Search Explanations

## Summary

This phase adds hybrid retrieval ranking and explanation fields. Phase 01 gave ThreadVault an FTS retrieval module. Phase 02 added retrieval diagnostics. Phase 03 created embedding-ready summary/evidence chunks. Phase 04 added a config-gated local vector adapter. Phase 05 combines the available FTS and vector signals into one ranked response while clearly reporting which capabilities were used.

Hybrid retrieval must remain local-first and resilient. If vector search is disabled, unconfigured, or empty, hybrid retrieval should still return FTS results and explain that it ran in FTS-only degraded mode. When vector is enabled and indexed, the response should include both FTS event matches and vector chunk matches with score breakdowns.

## Source Of Truth Read Before This Phase

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v2-retrieval-and-interfaces.md`
- `docs/v2/README.md`
- `docs/development-progress.md`
- Existing code:
  - `src/threadvault/retrieval.py`
  - `src/threadvault/vector_adapter.py`
  - `src/threadvault/summary_pipeline.py`
  - `src/threadvault/store.py`
  - `src/threadvault/cli.py`
  - `src/threadvault/schemas.py`

The active v2 roadmap is `docs/roadmap/v2-retrieval-and-interfaces.md`. The older goal text mentions `docs/roadmap/v2-personal-knowledge-layer.md` and `docs/v0-v1/`; those paths do not exist in the current repository. Phase 05 continues to use the current `docs/v0/`, `docs/v1/`, and `docs/v2/` structure.

## Current Baseline

- `threadvault retrieval query` returns FTS-only retrieval objects.
- `threadvault vector query` can query config-gated local vector chunks.
- `vector query` requires enabled config.
- There is no single hybrid response that combines FTS and vector scores.
- There is no explanation field describing per-result ranking factors.

## Goals

- Add a hybrid retrieval module/interface.
- Combine FTS event matches and vector chunk matches.
- Preserve FTS-only behavior when vector is absent, disabled, or empty.
- Add per-result explanation fields:
  - source.
  - matched_by.
  - score breakdown.
  - rank factors.
  - evidence event IDs.
- Add diagnostics that report capabilities used:
  - `fts`
  - `vector`
  - `hybrid`
- Add CLI access through the retrieval command group.
- Add JSON schema and generated schema artifact.
- Keep existing `search`, `retrieval query`, `vector query`, and schema contracts compatible.

## Non-Goals

- Do not add external embedding providers.
- Do not change the local vector adapter algorithm.
- Do not auto-build vector indexes.
- Do not make vector enabled by default.
- Do not add MCP/REST in this phase.
- Do not change database schema, package version, backup manifest version, restore record version, or global JSON contract version.

## Public Interface Plan

### Hybrid Retrieval Module

Add a module:

```python
threadvault.hybrid_retrieval
```

Tentative interface:

```python
HybridRetrievalRequest(...)
hybrid_retrieve(conn, request, config) -> dict
```

The module owns:

- fetching FTS retrieval results.
- optionally querying vector index.
- normalizing scores.
- merging and sorting candidates.
- generating explanations.
- reporting capability usage.

### CLI

Add:

```powershell
threadvault retrieval hybrid QUERY --json
threadvault retrieval hybrid QUERY --config threadvault.toml --json
```

Options:

- `--limit`
- `--session`
- `--cwd`
- `--since`
- `--until`
- `--type`
- `--tool`
- `--config`
- `--vector-limit`
- `--json`

Vector is optional:

- no enabled config -> FTS-only response with `vector_status: disabled_by_config`.
- enabled config with index -> hybrid response with vector results.

### JSON Schema

Add:

- `hybrid_retrieval`

Top-level payload:

- `contract_version`
- `query`
- `results`
- `diagnostics`

Each result:

- `hybrid_id`
- `source`
- `score`
- `scores`
- `session_id`
- `event_id`
- `chunk_id`
- `chunk_type`
- `text`
- `evidence_event_ids`
- `explanation`

### Ranking Strategy

Start with deterministic, transparent weights:

- FTS result base score: `0.65 * normalized_fts_score`
- Vector result base score: `0.35 * vector_score`
- Same project boost: `+0.05`
- Exact path/text hint boost: `+0.05`

Cap at `1.0`.

This is intentionally simple. The goal is explanation and stable behavior, not perfect relevance.

### Capabilities And Robot Docs

Advertise:

- JSON output: `retrieval hybrid`
- schema: `hybrid_retrieval`
- feature flag: `hybrid_retrieval: true`
- retrieval metadata:
  - supported modes include `hybrid`
  - hybrid can run FTS-only if vector is unavailable.

## Acceptance Criteria

- `threadvault retrieval hybrid pytest --json` works without vector config and reports FTS-only degraded mode.
- `threadvault retrieval hybrid "parser failure" --config TEMP_CONFIG --json` combines FTS and vector results after local vector index build.
- Each result includes `score`, `scores`, `source`, `evidence_event_ids`, and `explanation`.
- Diagnostics report whether FTS and vector were used.
- `hybrid_retrieval` appears in schema discovery and generated schema artifacts.
- Capabilities and robot docs advertise the hybrid retrieval interface.
- Existing `retrieval query`, `vector query`, and legacy `search --json` contracts still pass.
- Full regression tests pass.

## Validation Plan

```powershell
py -3.12 -m pytest tests\test_v205_hybrid_retrieval.py
threadvault schemas write --out docs\schemas --json
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault retrieval hybrid pytest --json
threadvault retrieval hybrid "parser failure" --db TEMP_DB --config TEMP_CONFIG --json
threadvault capabilities --json
threadvault schemas list --json
threadvault retrieval hybrid --help
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

## Risks

- If hybrid silently requires vector config, it violates the roadmap requirement that FTS remain strong without semantic/vector setup. Hybrid must degrade cleanly.
- If explanations are assembled only in CLI, future MCP clients will duplicate logic. Explanations belong in the hybrid retrieval module.
- If ranking weights are hidden, users cannot understand results. Each result must expose score breakdown and factors.
- If vector results expose too much derived text, users may misunderstand privacy impact. This phase should continue to use Summary Pipeline chunks and report evidence IDs.

## Next Phase

After this phase, v2 can add an MCP or agent-facing retrieval interface on top of the same retrieval/hybrid contracts.

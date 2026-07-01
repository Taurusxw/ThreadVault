# Phase 04 / v2.3: Local Vector Adapter Behind Config Gate

## Summary

This phase adds the first real vector adapter seam for v2. It consumes the `summary_chunks` output created in Phase 03, writes a local SQLite-backed vector index, and exposes config-gated vector indexing/query commands.

The adapter is intentionally local and deterministic. It uses a small built-in feature-hashing vectorizer so ThreadVault can validate the vector adapter shape without adding an external model dependency or sending content outside the machine. This is not presented as external LLM semantic embedding. Provider/model-based semantic embeddings remain a later optional adapter.

## Source Of Truth Read Before This Phase

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v2-retrieval-and-interfaces.md`
- `docs/v2/README.md`
- `docs/development-progress.md`
- Existing code:
  - `src/threadvault/app_config.py`
  - `src/threadvault/database.py`
  - `src/threadvault/summary_pipeline.py`
  - `src/threadvault/retrieval.py`
  - `src/threadvault/store.py`
  - `src/threadvault/cli.py`

The active v2 roadmap is `docs/roadmap/v2-retrieval-and-interfaces.md`. The older goal text mentions `docs/roadmap/v2-personal-knowledge-layer.md` and `docs/v0-v1/`; those paths do not exist in the current repository. Phase 04 continues to use the current `docs/v0/`, `docs/v1/`, and `docs/v2/` structure.

## Current Baseline

- `Retrieval` module supports FTS mode and diagnostics.
- `Summary Pipeline` can produce deterministic `summary_chunks`.
- No vector index tables exist.
- No vector commands exist.
- `AppConfig` does not yet have a retrieval/vector section.

## Goals

- Add a local vector adapter module.
- Add explicit config gate:
  - vector commands refuse to index/query unless local vector is enabled in `threadvault.toml`.
- Add SQLite vector index tables through a schema migration.
- Build vector index rows from `summary_chunks`, not from all raw events.
- Query vector index locally and return ranked chunks with evidence event IDs.
- Add JSON contracts and generated schema artifacts for:
  - vector index build result.
  - vector query result.
  - vector diagnostics/status.
- Preserve FTS as the default retrieval path.
- Keep semantic/external embeddings optional and deferred.

## Non-Goals

- Do not call external LLM or embedding APIs.
- Do not add a cloud dependency.
- Do not add semantic mode to `threadvault retrieval query` yet.
- Do not add hybrid ranking yet.
- Do not vectorize raw events directly.
- Do not make vector search enabled by default.
- Do not change package version, backup manifest version, restore record versions, or global JSON contract version.

## Public Interface Plan

### Config

Extend `threadvault.toml` with:

```toml
[retrieval.vector]
enabled = false
adapter = "local-hash"
dimensions = 64
```

Rules:

- Missing config means disabled.
- `enabled = true` is required for vector commands that build or query the index.
- Adapter must be `local-hash` in this phase.
- Dimensions must be a positive integer. The default is 64.

### Database

Add schema version `4` and tables:

- `vector_index_meta`
  - adapter
  - dimensions
  - chunk_count
  - built_at
- `vector_chunks`
  - chunk_id
  - chunk_type
  - session_id
  - turn_index
  - text
  - text_hash
  - vector_json
  - evidence_event_ids_json
  - metadata_json
  - indexed_at

This is a local derived index. It can be rebuilt from the archive plus Summary Pipeline chunks.

### Local Vector Adapter

Add:

```python
threadvault.vector_adapter
```

Tentative interface:

```python
VectorIndexRequest(...)
build_vector_index(conn, request, config) -> dict
query_vector_index(conn, query, config, limit) -> dict
vector_index_status(conn) -> dict
```

Implementation:

- tokenization with a simple Unicode-aware regex.
- signed feature hashing into fixed dimensions.
- L2 normalization.
- cosine similarity.
- deterministic ranking.

### CLI

Add:

```powershell
threadvault vector index --session SESSION_ID --config path\threadvault.toml --json
threadvault vector index --project E:\Codex\ThreadVault --config path\threadvault.toml --json
threadvault vector query "parser failure" --config path\threadvault.toml --json
threadvault vector status --json
```

Index/query commands require config enabled. Status can run without the gate so users can inspect whether the index exists.

### JSON Schemas

Add:

- `vector_index`
- `vector_query`
- `vector_status`

### Capabilities And Robot Docs

Advertise:

- command: `vector`
- JSON outputs:
  - `vector index`
  - `vector query`
  - `vector status`
- feature flags:
  - `local_vector_adapter: true`
  - `local_vector_enabled_by_default: false`
- vector metadata:
  - adapter: `local-hash`
  - default dimensions: 64
  - source schema: `summary_chunks`
  - generated embeddings: local deterministic vectors only.

## Acceptance Criteria

- Missing or disabled config makes `vector index` and `vector query` fail clearly.
- Enabled config allows indexing fixture summary chunks.
- Indexing fixture data writes vector rows to SQLite and reports chunk count.
- `vector status --json` reports adapter, dimensions, chunk count, and freshness metadata.
- `vector query "parser failure" --json` returns ranked chunks with scores and evidence event IDs.
- Vector index rows come from `summary_chunks`, not all raw events.
- Capabilities and robot docs advertise the adapter as local/config-gated.
- `summary_chunks`, retrieval, and legacy search contracts still pass.
- Full regression tests pass.

## Validation Plan

```powershell
py -3.12 -m pytest tests\test_v204_local_vector_adapter.py
threadvault schemas write --out docs\schemas --json
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault vector status --json
threadvault vector index --db TEMP_DB --session sess-current --config TEMP_CONFIG --json
threadvault vector query "parser failure" --db TEMP_DB --config TEMP_CONFIG --json
threadvault capabilities --json
threadvault schemas list --json
threadvault vector --help
threadvault vector index --help
threadvault vector query --help
threadvault vector status --help
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

## Risks

- A local hashing vector is not equivalent to a neural semantic embedding. Documentation and diagnostics must say this clearly.
- Adding vector tables changes the database schema. The migration must be explicit and covered by doctor/self-test/full tests.
- If vector commands scan raw events directly, they would violate the v2 roadmap. They must consume Summary Pipeline chunks.
- If vector commands are enabled by default, they would weaken the explicit opt-in boundary. They must require config.

## Next Phase

After this phase, v2 can add hybrid ranking and explanation fields that combine FTS and vector results while reporting exactly which retrieval capabilities were used.

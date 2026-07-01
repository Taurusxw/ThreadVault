# Phase 04 Design Notes: Local Vector Adapter

## Decision: Config-Gated By Default

Vector indexing is derived data and can duplicate sensitive local text. Phase 04 therefore requires an explicit config opt-in:

```toml
[retrieval.vector]
enabled = true
adapter = "local-hash"
dimensions = 64
```

Missing config or `enabled = false` keeps indexing/querying disabled. `vector status` remains available without the gate because status does not create or query derived text.

## Decision: Local Hash Adapter First

This phase uses a deterministic local feature-hashing vectorizer:

- no network.
- no model download.
- no external provider.
- no new package dependency.
- reproducible vectors across runs.

This proves the vector adapter seam, index lifecycle, JSON contracts, and opt-in behavior. It is not described as a neural semantic embedding model. Future provider adapters can satisfy the same higher-level shape after the local adapter is stable.

## Decision: Consume Summary Pipeline Chunks

The vector index consumes `summary_chunks` from Phase 03. It does not scan all raw events directly.

This keeps the roadmap boundary intact:

- prefer session summaries.
- prefer turn summaries.
- prefer high-value evidence chunks.
- avoid vectorizing every raw event by default.

## Decision: SQLite Derived Index

The vector index is stored in SQLite tables in the existing archive database. This keeps backup/restore local and simple. The index is derived and rebuildable, but it should still be visible to doctor/status tooling.

This requires schema version `4`:

- `vector_index_meta`
- `vector_chunks`

The version bump is a database compatibility change, not a package version bump.

## Decision: Separate Vector Commands Before Hybrid Retrieval

Phase 04 adds:

```powershell
threadvault vector index
threadvault vector query
threadvault vector status
```

It does not add `--mode vector` to `threadvault retrieval query` yet. The roadmap's next milestone is hybrid ranking and explanation fields. Keeping vector commands separate in this phase makes the adapter testable before combining it with FTS.

## Deferred Scope

- external embedding providers.
- local neural embedding model downloads.
- vector extension dependencies.
- ANN indexes.
- hybrid FTS/vector ranking.
- MCP interface over vector query.
- automatic indexing from ingestion hooks.

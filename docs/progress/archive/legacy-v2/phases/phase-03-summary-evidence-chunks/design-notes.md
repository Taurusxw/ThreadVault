# Phase 03 Design Notes: Summary Evidence Chunks

## Decision: Add A Summary Pipeline Module

The roadmap names `Summary Pipeline` as a module that owns evidence-backed summary bundles. v1 already has deterministic summaries and export targets, but those implementations are shaped for files. Future retrieval adapters need a reusable selection interface, not Markdown-specific export logic.

Phase 03 therefore adds a module-level interface for chunk selection:

```python
build_summary_chunks(conn, request)
```

This keeps the seam small while hiding:

- session and project selection.
- summary construction.
- turn grouping.
- high-value evidence selection.
- chunk ID generation.
- text trimming.

## Decision: Chunk Selection Before Embeddings

The v2 roadmap says not to vectorize every raw event by default. The correct next step is a stable chunk contract, not a vector store. Once chunks exist, a later adapter can embed exactly those chunks.

This phase does not:

- call embedding models.
- write vector indexes.
- add semantic mode.
- rank by vector similarity.

## Decision: Provider-Neutral Chunk Shape

The chunk contract does not contain provider-specific fields such as embedding dimensions, model names, vector IDs, or token counts. Those belong to the future vector adapter. This phase only records durable local evidence:

- `chunk_id`
- `chunk_type`
- `session_id`
- `turn_index`
- `text`
- `evidence_event_ids`
- `metadata`

## Decision: Deterministic IDs

Chunk IDs should be reproducible across repeated runs when the same archive state and options are used. The ID format is human-readable:

```text
session_id:session-summary
session_id:turn-N
session_id:evidence-EVENT_ID
```

This is enough for future embedding manifests to map vectors back to source chunks.

## Decision: Evidence Traceability Is Mandatory

Every emitted chunk must include at least one evidence event ID. A summary chunk can use the summary's evidence set. Turn chunks use event IDs from the grouped turn. Evidence chunks use their source event ID.

This preserves the ThreadVault convention that generated claims can be traced back to stored events.

## Deferred Scope

- semantic retrieval.
- vector indexes.
- embedding provider configuration.
- hybrid ranking.
- MCP interface over chunks.
- project-level cross-session summary generation.

The module should leave those future phases easier, but it should not pretend they have been implemented.

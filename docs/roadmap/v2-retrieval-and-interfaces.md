# ThreadVault v2: Retrieval And Interfaces

## Summary

`v2` makes ThreadVault easier for agents and future clients to query. The core work is a stable `Retrieval` module plus optional semantic and hybrid search. MCP and other machine interfaces should sit on top of the same retrieval interface rather than inventing separate query logic.

The center of gravity is `semantic retrieval + stable query interface`, not desktop UI or team governance.

## Key Outcomes

- CLI, MCP, agents, and later GUI clients can share one retrieval interface.
- FTS5 remains the default local search engine.
- Semantic search is optional and can be disabled without weakening the core archive.
- Hybrid ranking can combine FTS score, vector similarity, recency, exact file-path matches, and same-project boosts.
- JSON contracts describe retrieval outputs well enough for external agents to validate them.

## Architecture Changes

### Retrieval Module

Create a `Retrieval` module with a small interface around:

- Stable search query input.
- Project/session/time/type/tool filters.
- Ranked result output.
- Evidence event references.
- Retrieval diagnostics and index status.

In early `v2`, the only adapter can wrap current SQLite FTS5 behavior. The vector seam becomes real when a second adapter is added.

### Vector Adapter

Add vector retrieval as optional capability:

- Do not vectorize every raw event by default.
- Prefer turn summaries, session summaries, project summary blocks, and high-value evidence chunks.
- Keep model/provider configuration explicit.
- Keep local embedding and external embedding as separate adapters when both exist.

### Interface Layer

Add MCP or agent-facing query entrypoints only after the `Retrieval` module can serve them. These entrypoints should expose retrieval capabilities and schema contracts, not raw database internals.

## Out Of Scope For v2

- Heavy desktop or Web UI.
- Team permission systems.
- Cloud sync and centralized server deployment as the default.
- Rewriting the archive database around vectors.
- Replacing FTS5 as the default search path.

## Suggested Milestones

1. `v2.0`: Retrieval module wraps current FTS5 search and preserves CLI behavior.
2. `v2.1`: Retrieval JSON contracts and diagnostics.
3. `v2.2`: Summary/evidence chunk selection for optional embeddings.
4. `v2.3`: Local vector adapter behind an explicit config gate.
5. `v2.4`: Hybrid ranking and search explanation fields.
6. `v2.5`: MCP or agent-facing retrieval interface.
7. `v2.6`: v2 acceptance smoke covering FTS-only and semantic-enabled modes.

## Acceptance Criteria

- Existing search commands continue to work through the retrieval module.
- Retrieval results always include enough evidence references to trace back to stored events.
- Semantic search can be absent, disabled, or unconfigured while FTS search still passes.
- Hybrid search clearly reports which retrieval capabilities were used.
- Agent-facing interfaces do not expose private raw paths or transcript content unless the user explicitly requests a local debug mode.


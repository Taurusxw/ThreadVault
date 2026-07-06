# Phase 05 Design Notes: Hybrid Ranking And Explanations

## Decision: Hybrid Degrades To FTS-Only

Hybrid retrieval should not make vector setup mandatory. The v2 roadmap requires semantic/vector search to be optional while FTS remains useful. Therefore:

- missing config -> FTS-only hybrid response.
- disabled vector config -> FTS-only hybrid response.
- enabled config but empty index -> FTS-only hybrid response with an explanation.
- enabled config and populated index -> combined FTS/vector response.

This lets agents call one hybrid interface without first knowing the user's local vector setup.

## Decision: Add A New Hybrid Contract

The existing `retrieval_query` schema is event-oriented. Vector results are chunk-oriented. A hybrid result can be either an event or a chunk, so Phase 05 adds:

```text
hybrid_retrieval
```

This avoids weakening the existing retrieval contract while giving future MCP/client layers a clear mixed-result shape.

## Decision: Explanations Belong In The Module

CLI commands should not infer ranking internals. The hybrid module owns:

- FTS score normalization.
- vector score handling.
- same-project boosts.
- exact path/text hint boosts.
- result ordering.
- explanation fields.

Keeping this logic inside `threadvault.hybrid_retrieval` lets future MCP and GUI layers reuse it.

## Decision: Deterministic Transparent Ranking

This phase uses simple fixed weights:

- FTS score contributes up to `0.65`.
- vector score contributes up to `0.35`.
- same-project boost contributes `0.05`.
- exact path/text hint boost contributes `0.05`.

Scores are capped at `1.0`. This is intentionally not a perfect relevance model. It is a stable, inspectable baseline that can be tuned later.

## Decision: Keep Vector Config Explicit

Hybrid retrieval accepts `--config`, but does not auto-enable or auto-build the vector index. This preserves the Phase 04 opt-in boundary and prevents surprising derived-data creation.

## Deferred Scope

- automatic vector indexing during ingestion.
- neural semantic embeddings.
- learned ranking.
- MCP/REST interface.
- GUI controls for score explanations.

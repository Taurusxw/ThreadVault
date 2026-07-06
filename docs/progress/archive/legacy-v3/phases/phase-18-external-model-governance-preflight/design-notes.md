# v3 Phase 18 Design Notes: External Model Governance Preflight

## External Model Calls Stay Opt-In

The roadmap explicitly keeps external model behavior opt-in. This phase does not add an adapter; it only documents and
exposes the governance gate that future adapters must pass.

## Export Access Is The Current Permission Fit

Phase 10 maps `external model adapters` to `external_model_call`, which currently requires `export` access. That keeps
outbound data sharing grouped with high-sensitivity export behavior until a later phase has enough evidence to justify a
more specific access level.

## No Network Or Payload Side Effects

The preflight must not send prompts, transcript text, embeddings, summaries, local metadata, paths, or provider requests.
Optional audit logging records only that the preflight check happened.

## Outbound Policy Before Adapter Work

Future adapter implementation should require an explicit outbound policy, privacy scan/redaction decision, evidence
validation, and audit behavior before model calls are allowed in shared deployments.

## v2 Boundary

The preflight does not alter retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval.

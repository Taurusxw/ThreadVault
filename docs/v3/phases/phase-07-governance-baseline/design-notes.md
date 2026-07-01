# v3 Phase 07 Design Notes: Governance Baseline

## Baseline Before Enforcement

This phase intentionally defines governance status before enforcing governance. Future phases can attach permission checks
and audit writes to the vocabulary established here, but this phase should not change behavior for existing local CLI
commands.

## Opt-In Boundary

Governance is disabled by default. Enabling `[governance] enabled = true` makes governance intent visible to commands and
clients, but it does not enable cloud sync, require a server, or call external models.

## Access Vocabulary

The first governance vocabulary mirrors the roadmap:

- `raw_transcript`
- `summary_search`
- `export`
- `delete_retention`
- `restore`

This vocabulary is intentionally coarse. It is enough for clients and future server work to distinguish sensitive raw
access from lower-risk summary/search workflows without over-designing identity before ThreadVault has a server runtime.

## Deferred Enforcement

Permission enforcement, audit persistence, shared server identity, and centralized backup policy are deferred. This keeps
the local-first product stable while making the future governance work traceable and testable.

## v2 Retrieval Boundary

This phase does not touch FTS retrieval, hybrid retrieval, vector indexing, or agent-facing retrieval.

# v3 Phase 22 Design Notes: Identity Actor Binding Readiness

## Actor Labels Are Not Identity

Existing local audit commands accept manual actor strings. That is useful for local evidence, but it is not an
authenticated identity provider, server request actor, or team role mapping. This phase records that distinction.

## Readiness Before Authentication

This phase does not implement authentication or a server request context. It defines the requirements that future
shared/server modules must satisfy before they can claim reliable actor-bound policy enforcement or audit evidence.

## Shared Enforcement Depends On Actor Binding

Centralized policy, centralized audit retention, and automatic instrumentation all need a trustworthy actor identity.
Without actor binding, shared enforcement cannot distinguish who requested raw transcript, summary/search, export,
restore, retention, or external model operations.

## Local-First Boundary

Local CLI workflows remain usable without identity providers. The readiness report must keep `server_required = false`,
`server_opt_in = true`, and `cloud_sync = false`.

## v2 Boundary

The readiness report does not touch retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing
retrieval.

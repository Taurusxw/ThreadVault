# v3 Phase 23 Design Notes: Centralized Policy Store Readiness

## Local Policy Vocabulary Is Not Central Policy

ThreadVault already has a local governance role and access vocabulary. That is enough for local preflight and readiness
reports, but it is not a centralized policy store, policy adapter, versioned policy document, or team role resolution
source.

## Readiness Before Store

This phase does not introduce a database, service, file format migration, or remote policy loader. It defines the
requirements future shared/server policy modules must satisfy before shared enforcement can be claimed.

## Identity Comes First

Centralized policy enforcement depends on trusted actor identity and role mapping. Phase 22 makes that dependency
explicit; this phase records it as a central policy blocker rather than hiding it behind a future server implementation.

## Local-First Boundary

Local CLI workflows remain usable without centralized policy. The readiness report must keep `server_required = false`,
`server_opt_in = true`, and `cloud_sync = false`.

## v2 Boundary

The readiness report does not touch retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing
retrieval.

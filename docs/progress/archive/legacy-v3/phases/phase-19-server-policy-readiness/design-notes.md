# v3 Phase 19 Design Notes: Server Policy Readiness

## Readiness Before Runtime

Server/team mode should not appear ready merely because preflight commands exist. Identity, policy storage, audit, and
backup/restore policy need their own readiness report before any shared enforcement mode is implemented.

## Opt-In Server Boundary

The readiness payload must keep `server_required = false` and `server_opt_in = true`. Local CLI workflows remain useful
without a server.

## Central Policy Is A Future Module

This phase does not introduce a policy database or adapter. It records the future module requirements and leaves
implementation to a later phase after the shared-mode invariants are explicit.

## Instrumentation Still Deferred

Preflight commands exist for sensitive surfaces, but business commands still do not automatically call them. The
readiness report should make that blocker visible rather than pretending shared enforcement is complete.

## v2 Boundary

The readiness report does not touch retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing
retrieval.

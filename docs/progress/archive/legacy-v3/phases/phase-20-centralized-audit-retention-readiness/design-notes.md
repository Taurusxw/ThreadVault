# v3 Phase 20 Design Notes: Centralized Audit Retention Readiness

## Local Audit Is Not Shared Audit

Phase 08 implemented local JSONL audit append/list workflows. That is useful evidence for local work, but shared
deployments need identity-bound, retention-controlled, queryable audit evidence.

## Readiness Before Storage

This phase does not introduce a central audit database or adapter. It records the future module requirements and leaves
implementation to a later phase after the shared-mode invariants are explicit.

## Append-Only Integrity Is A Requirement

Future centralized audit storage must preserve append-only integrity, provenance, retention policy, and review/export
workflow expectations. The readiness report makes those requirements visible before implementation.

## Local-First Boundary

The readiness command must keep `server_required = false`, `server_opt_in = true`, and local JSONL audit available.
Centralized audit is a shared-mode requirement, not a local CLI prerequisite.

## v2 Boundary

The readiness report does not touch retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing
retrieval.

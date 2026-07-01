# v3 Phase 24 Design Notes: Centralized Backup/Restore Policy Readiness

## Local Backup Is Not Shared Backup Policy

ThreadVault has local backup, restore, manifest, history, and retention workflows. Those are necessary but not sufficient
for shared/team deployments, where backup and restore need policy, approval, audit provenance, and recovery testing.

## Readiness Before Repository

This phase does not add remote storage, replication, or a shared repository. It records what a future centralized backup
module must satisfy before v3 can claim centralized backup/restore and retention policy.

## Restore Is Governance Sensitive

Restore can reintroduce raw transcript data, overwrite local state, and affect shared archives. Future shared restores
need actor identity, policy authorization, review/approval, and audit provenance before execution.

## Local-First Boundary

The local CLI remains usable without centralized backup policy. The readiness report must keep `server_required = false`,
`server_opt_in = true`, and `cloud_sync = false`.

## v2 Boundary

The readiness report does not touch retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing
retrieval.

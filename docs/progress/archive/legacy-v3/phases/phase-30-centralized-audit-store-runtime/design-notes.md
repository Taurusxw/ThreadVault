# v3 Phase 30 Design Notes: Centralized Audit Store Runtime

## Local Store First

The first accepted centralized audit store is a local JSONL file. It is centralized in the sense that team-mode audit
evidence has one explicit store contract and verification workflow, not because it requires a network service.

## Hash Chain As Tamper Evidence

Each record stores `previous_hash` and `record_hash`. Verification recomputes the chain from the stored payload. This is
not a cryptographic signing system, but it is enough to detect local tampering, truncation continuity issues, and record
mutation.

## Local Audit Remains Available

The existing `governance audit append/list` commands remain local-only and unchanged. Phase 30 adds a separate runtime
for shared-mode audit evidence instead of silently changing local audit semantics.

## Runtime Is Not Retention Policy

The runtime can append, list, and verify records. Retention, legal hold, backup/export policy, and review approval are
still separate v3 work.

## Deep Module Seam

CLI, store methods, readiness reports, tests, and future optional server paths should use a single governance runtime
interface for centralized audit store actions. Parsing, hash-chain validation, and filter behavior should stay inside
that module.

# v3 Phase 12 Design Notes: Governance Policy Readiness

## Readiness Before Instrumentation

This phase documents and exposes the conditions required before ThreadVault can safely enforce governance policy in
business commands. It avoids changing command behavior until the product boundary is explicit and testable.

## Manifest As Gate

The readiness manifest is a gate for future phases. A later phase that instruments export, backup, restore, retrieval,
or retention commands should reference this manifest and update it when prerequisites change.

## Local-First Boundary

The manifest must keep local-first and privacy-first defaults visible. A personal CLI install remains usable without
server mode, cloud sync, centralized audit, or external model calls.

## Known Missing Pieces

The first readiness version should deliberately mark these as incomplete:

- server identity model.
- centralized policy store.
- automatic business command permission preflight.
- automatic business command audit writes.
- centralized audit storage.
- shared backup/restore policy.

## v2 Boundary

Readiness reporting must not change v2 retrieval, hybrid retrieval, vector indexing, or agent-facing retrieval behavior.

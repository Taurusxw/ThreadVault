# v3 Phase 31 Design Notes: Centralized Backup/Restore Policy Runtime

## Runtime, Not Repository

This phase accepts a local policy runtime, not a remote backup service. The policy can describe repository, retention,
restore approval, legal hold, recovery-test, and migration expectations, but the command only validates and previews
decisions. Actual backup/restore command instrumentation remains separate.

## Deep Module Shape

The governance module owns policy parsing, validation, and operation resolution behind one small interface:

```python
governance_central_backup_policy(config, policy_path=None, operation=None, actor=None)
```

Callers should not need to know the policy file shape beyond passing a path and optional operation context.

## Dependency Relationship

The runtime depends on previously accepted v3 pieces:

- Phase 28 local static actor binding is sufficient for local previews, but not authenticated shared provenance.
- Phase 29 central policy store remains the team permission policy runtime.
- Phase 30 centralized audit store provides a local hash-chain audit store, but broad automatic audit instrumentation
  remains pending.

## Local-First Boundary

The policy file is optional. Without it, local CLI backup and restore commands remain usable. Server, cloud, and team
capabilities stay opt-in.

## Non-Claim

This phase should not claim production shared backup readiness. It only removes the v3 blocker that no centralized
backup/restore policy exists. Automatic command instrumentation and final v3 acceptance smoke remain blockers.

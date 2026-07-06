# v3 Phase 14 Design Notes: Restore/Retention Governance Preflight

## Restore And Retention Are High Risk

Restore and retention commands can replace archive state, rewrite history files, or delete evidence. They should have
their own preflight contract before any automatic enforcement is added to the actual business commands.

## Explicit Preflight Before Instrumentation

The preflight interface composes existing governance decisions without executing restore or pruning behavior. This keeps
local-first defaults stable while giving clients and future server mode a safe planning surface.

## Narrow Command Family

This phase covers only restore and retention commands. Export/backup preflight is already covered by Phase 13, and raw
transcript read preflight remains a later phase.

## No Side Effects

The preflight must not restore a database, rewrite history files, delete backups, delete audit reports, or apply
retention. Optional audit logging records only that the preflight check happened.

## v2 Boundary

The preflight does not touch retrieval, hybrid retrieval, vector indexing, or agent-facing retrieval.

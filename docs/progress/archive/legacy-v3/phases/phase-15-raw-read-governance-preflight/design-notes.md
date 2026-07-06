# v3 Phase 15 Design Notes: Raw Read Governance Preflight

## Raw Reads Are High Sensitivity

Raw transcript reads can expose prompt text, tool output, local paths, and other local-only context. They should have a
dedicated preflight contract before team mode or richer clients start invoking raw-read paths on behalf of multiple
actors.

## Explicit Preflight Before Instrumentation

The preflight interface composes existing governance decisions without executing `threadvault client session`. This
keeps local-first defaults stable while giving clients and future server mode a safe planning surface.

## Narrow Command Family

This phase covers only `threadvault client session`. Search/retrieval commands and warning detail commands use
summary/search access and remain later phases.

## No Data Return Side Effects

The preflight must not return raw transcript text, event previews, local debug metadata, raw paths, or session detail
payloads. Optional audit logging records only that the preflight check happened.

## v2 Boundary

The preflight does not touch retrieval, hybrid retrieval, vector indexing, or agent-facing retrieval.

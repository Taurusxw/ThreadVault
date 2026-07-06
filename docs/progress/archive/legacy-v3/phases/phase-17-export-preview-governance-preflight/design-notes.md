# v3 Phase 17 Design Notes: Export Preview Governance Preflight

## Export Preview Uses Export Access

`threadvault client export-preview` is read-only, but it exposes export intent, selected archive scope, destination shape,
privacy posture, and future sharing boundaries. It should therefore use `export` access rather than summary/search
access.

## Explicit Preflight Before Instrumentation

The preflight interface composes existing governance decisions without executing export-preview behavior. This keeps
local-first defaults stable while giving clients and future server mode a safe planning surface.

## Narrow Command Family

This phase covers only `threadvault client export-preview`. Direct export and backup commands are covered by Phase 13,
summary/search reads by Phase 16, and raw transcript reads by Phase 15.

## No Preview Or Export Side Effects

The preflight must not generate export previews, return manifests, scan content, write files, expose local paths, or
return raw metadata. Optional audit logging records only that the preflight check happened.

## v2 Boundary

The preflight does not touch retrieval, hybrid retrieval, vector indexing, or agent-facing retrieval.

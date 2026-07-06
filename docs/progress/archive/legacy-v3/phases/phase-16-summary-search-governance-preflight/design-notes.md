# v3 Phase 16 Design Notes: Summary/Search Governance Preflight

## Summary/Search Reads Are A Separate Access Level

Summary/search commands are less sensitive than raw transcript reads, but they can still disclose archive-derived text,
snippets, evidence IDs, warning details, and project context. They should use the existing `summary_search` access level
instead of inheriting the raw transcript path from Phase 15.

## Explicit Preflight Before Instrumentation

The preflight interface composes existing governance decisions without executing retrieval or warning detail behavior.
This keeps v2 retrieval stable while giving clients and future server mode a safe planning surface.

## Narrow Command Family

This phase covers only Phase 10 commands mapped to `read_summary_search`:

- `threadvault client warnings`
- `threadvault agent retrieve`
- `threadvault retrieval query`
- `threadvault retrieval hybrid`

`threadvault client export-preview` stays outside this phase because it maps to export access, not summary/search
access.

## No Data Return Side Effects

The preflight must not return search results, snippets, warning details, evidence chunks, raw paths, local debug
metadata, or session payloads. Optional audit logging records only that the preflight check happened.

## v2 Boundary

The preflight does not alter retrieval, hybrid retrieval, vector indexing, or agent-facing retrieval. It only adds a
governance planning surface around those existing interfaces.

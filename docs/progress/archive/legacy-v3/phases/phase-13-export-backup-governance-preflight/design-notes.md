# v3 Phase 13 Design Notes: Export/Backup Governance Preflight

## Explicit Preflight Before Instrumentation

This phase adds a preflight interface instead of instrumenting existing export or backup commands. That keeps personal
local CLI behavior stable while giving clients and future server mode a stable governance check.

## Narrow Command Family

The first business-oriented preflight only covers export and backup commands because those create durable artifacts that
can leave a personal machine or be shared with a team. Restore, retention, raw transcript reads, and search remain later
phases.

## No Side Effects

The preflight must not run the checked command. It does not create files, backups, manifests, vault entries, or skill
artifacts. Optional audit logging records the preflight check itself.

## Privacy Expectations

Export and backup workflows should surface privacy expectations even when the preflight does not scan content itself.
The payload should tell callers that future execution must respect privacy mode, redaction/fail policy, and outbound data
policy.

## v2 Boundary

The preflight does not touch retrieval, hybrid retrieval, vector indexing, or agent-facing retrieval. It only composes
governance interfaces that already exist.

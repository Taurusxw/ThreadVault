# v3 Phase 06 Design Notes: Client Warning Detail Workflow

## Read-Only Remediation

This phase provides remediation context, not remediation execution. `client warnings` returns structured warning and
privacy detail so a client can render a useful panel, but it does not rewrite transcripts, mutate config, or perform an
export.

## Existing Module Reuse

The warning side comes from the existing archive warning records. The privacy side comes from the existing privacy scan
path used by export and privacy CLI workflows. The client interface is responsible for shaping a stable client payload,
not for inventing new warning or privacy semantics.

## Local Metadata Boundary

Default output must stay safe for richer clients and agent consumers:

- no raw local file paths by default.
- no raw transcript file paths by default.
- explicit local debug mode may include local metadata.
- any local metadata opt-in must be reflected in the payload.

## Deferred Governance

Team permissions, shared audit records, and server-mediated approvals are deliberately deferred. This phase still helps
future governance because it defines a stable client-facing warning/privacy payload that later server or team layers can
authorize and audit.

## v2 Retrieval Boundary

This phase does not touch FTS retrieval, hybrid retrieval, vector indexing, or agent-facing retrieval. It only adds a
client workflow beside existing v3 client workflows.

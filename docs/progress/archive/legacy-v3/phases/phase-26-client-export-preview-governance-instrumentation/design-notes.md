# v3 Phase 26 Design Notes: Client Export Preview Governance Instrumentation

## Interface Placement

The instrumentation seam is `ArchiveStore.client_export_preview`. This keeps the business command interface small for
callers while placing the governance wiring beside the existing preview implementation.

The implementation should reuse `governance_export_preview_preflight` instead of duplicating permission, audit, or
command inventory logic.

## Command Selection

`client export-preview` is intentionally selected before write commands. It is:

- user-facing
- already a client workflow
- read-only by design
- already covered by an operation-specific governance preflight
- able to demonstrate automatic preflight and optional audit without creating export artifacts

## Opt-In Boundary

Instrumentation is explicit. Existing callers that omit governance options keep the same payload shape, aside from the
append-only `governance_instrumentation` field.

Governance enforcement is only blocking when governance is enabled through config and the preflight decision denies the
role.

## Deferred Items

- More business commands still need instrumentation.
- Central policy and central audit remain readiness-only.
- Actor identity remains caller-provided metadata, not authenticated identity binding.
- Final v3 acceptance smoke remains a later phase.

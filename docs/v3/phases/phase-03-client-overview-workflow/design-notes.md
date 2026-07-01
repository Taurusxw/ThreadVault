# v3 Phase 03 Design Notes: Client Overview Workflow

## Summary

`client overview` is a local read-only workflow for richer client first screens. It is deliberately smaller than a UI
application but more useful than a manifest: clients can show recent sessions, run a query, and expose safe next actions.

## Module Boundary

The implementation stays in `threadvault.client_interface` because this is client orchestration, not a new retrieval
module. It calls:

- `list_sessions(...)` through `ArchiveStore.client_overview(...)` for browse data.
- `agent_retrieve(...)` for search data.

This keeps v2 retrieval as the owner of search behavior and keeps client code focused on payload shaping.

## Default Payload

The default overview hides `raw_path`. It includes:

- session id.
- project cwd.
- source kind.
- timestamps.
- event count.
- warning count.

Search results use the same default privacy shaping as `agent retrieve`: no local metadata unless `--local-debug` is
explicit.

## Deferred Decisions

- Whether the next client workflow should add detail views for one session.
- Whether export actions should gain a dry-run preview payload before a UI triggers export.
- Whether UI clients should call CLI JSON or embed `ArchiveStore`.
- How shared server deployments should audit overview reads.


# Phase 27 Design Notes - Local TUI Client Runtime

## Decision

Accept a local TUI runtime as the first concrete richer client runtime for v3.

The roadmap lists desktop, Web, TUI, and IDE clients as acceptable v3 client families. A TUI is the narrowest runtime
that can be accepted without introducing heavyweight packaging or a server dependency. It still gives users a richer
client surface than independent JSON commands because it composes browse, search, and export preview into one local
screen.

## Module Interface

The implementation should add a dedicated runtime module with a small interface:

- Build one runtime payload from existing client workflows.
- Render that payload as Rich text/table output.

This keeps the CLI command shallow and keeps future desktop, IDE, or Web clients free to reuse the same payload contract.

## Reused Interfaces

The runtime must reuse:

- `ArchiveStore.client_overview` for browse/search.
- `ArchiveStore.client_export_preview` for read-only export planning.
- v2 agent retrieval indirectly through query mode in `client_overview`.

It must not:

- parse Codex JSONL files;
- bypass privacy scan behavior for export planning;
- change v2 retrieval, hybrid retrieval, vector adapter, or agent-facing retrieval semantics.

## Privacy And Governance Boundary

The runtime remains local-only by default:

- `server_required = false`
- `cloud_sync = false`
- `external_model_calls = false`
- raw paths are hidden unless `--local-debug` is explicitly passed

This phase removes only the richer-client runtime blocker. It does not claim shared deployment readiness. Team identity,
central policy, centralized audit, centralized backup/restore, broad governance instrumentation, and final v3 smoke remain
separate blockers.

## Why Not Desktop Or Web Now

A desktop shell or Web UI would be valid v3 client work, but it would add packaging, browser, or server decisions before
the remaining governance blockers are closed. The TUI runtime gives v3 an accepted concrete client while preserving the
roadmap's local-first default and keeping the remaining phases focused on team governance.

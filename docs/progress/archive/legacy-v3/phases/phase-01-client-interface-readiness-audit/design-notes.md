# v3 Phase 01 Design Notes: Client Interface Readiness Audit

## Summary

v3 should start by treating richer clients as adapters over existing ThreadVault modules, not as alternate
implementations of parsing, retrieval, export, or privacy behavior.

The useful seam for the first client is the existing public interface surface:

- CLI JSON commands for user-facing and smoke-test workflows.
- `ArchiveStore` for local Python clients.
- `threadvault.agent_interface` for agent-facing retrieval.
- JSON Schema artifacts under `docs/schemas/` for stable payload validation.

## Interface Map

| Client Need | Current Interface | Readiness |
|---|---|---|
| Discover supported commands and contracts | `capabilities()`, `robot_guide()`, `robot_schemas()` | Ready for read-only clients. |
| Search sessions | `retrieval query`, `retrieval hybrid`, `agent retrieve` | Ready; v3 should prefer the agent interface for client search. |
| Explain results | `hybrid_retrieval` and `agent_retrieval` explanation fields | Ready for client display. |
| Preserve evidence traceability | `evidence_event_ids` in retrieval, hybrid, chunks, and agent results | Ready for client display. |
| Check semantic/vector availability | `vector status` and agent manifest vector flags | Ready; vector remains disabled by default. |
| Export durable artifacts | `export`, `export-target markdown/obsidian/skill` | Ready for local client actions, with privacy mode controls. |
| Hide raw local metadata | `agent retrieve` default output plus `--local-debug` opt-in | Ready for default client search views. |
| Govern sensitive shared actions | Existing audit, backup, restore, privacy, and retention commands | Partially ready; v3 must add an explicit policy seam before team features. |

## Chosen Boundary

Phase 01 does not introduce a new client interface module. The existing `threadvault.agent_interface` module is deep
enough for retrieval clients, and `ArchiveStore` already concentrates local archive/export/retrieval operations behind a
small Python interface.

Adding a second facade now would be shallow: it would mostly rename existing methods while hiding no new complexity. The
better next step is to design a focused client readiness or client session interface only when the first concrete client
shows repeated call patterns that deserve a deeper module.

## Local-First Defaults

The first client must preserve these defaults:

- No server is required.
- No cloud sync is enabled.
- No external model calls are made.
- Vector retrieval is disabled unless a local config enables it.
- Agent retrieval hides raw path metadata by default.

This keeps v3 aligned with the roadmap: optional clients and governance without making shared infrastructure mandatory.

## Deferred Decisions

- Whether the first richer client should be a desktop shell or VS Code/Cursor extension.
- Whether optional server mode should wrap `ArchiveStore` directly or introduce a narrower server-facing interface.
- How team permissions should represent raw transcript, summary/search, export, retention, restore, and delete rights.
- Whether centralized audit should extend existing history commands or use a new append-only event log.


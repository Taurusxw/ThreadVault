# TODO

## Current Follow-Up Items

| Priority | Item | Notes |
|---|---|---|
| Medium | Add safe "open export directory" UX | Users need a clearer bridge from "导出已写入" to the actual folder. Design as local-only and avoid unsafe arbitrary path opening. |
| Low | Run an NVDA screen-reader acceptance pass | Tk controls now have visible labels, native keyboard focus, and tab/shortcut navigation, but Windows UI Automation still exposes the Tk child-control tree incompletely. |
| Low | Add official MCP Inspector smoke to release gates | Protocol/unit tests cover lifecycle and tools; an Inspector run would add external-client interoperability evidence for a future release. |
| Low | Expand visual QA checklist into standard release artifact | Keep under `docs/progress/releases/` only when preparing a release. |

## Completed In Current Rounds

- Added source freshness inspection and targeted catch-up for missing, changed, stale-parser, and newly touched Codex transcripts.
- Made smart backup catch up sources first and block on catch-up failure, so automatic backups cannot silently preserve a known-stale archive.
- Added dry-run-first `threadvault codex status/install` for exact Stop hook and read-only MCP setup, plus desktop one-click integration.
- Added Windows CI with Python 3.11/3.12, ruff, 70% branch-coverage gate, isolated desktop smoke, and MCP manifest validation.
- Fixed the rendered desktop startup Treeview state regression and Windows SQLite backup-retention file locks.
- Reworked the native desktop into friendly session tables, a foolproof Backup Center, confirmed export, safe restore defaults, automatic health summaries, directory pickers, scrollbars, focusable controls, and Chinese labels.
- Added one-command smart backup selection, verification, disk guard, last-run status, and bounded automatic retention.
- Added schema v8 hot/cold storage with content-addressed immutable evidence.
- Added exact duplicate conversation-body removal and stopped repeated turn-body persistence.
- Added copy-on-write rebuild, deep cold verification, reference-aware garbage collection, and Core/Evidence/Forensic backup profiles.
- Migrated and activated the real archive with verified counts/conversation digest, then produced verified Core and Evidence backups.
- Connected user-level Codex `Stop` hooks to targeted single-transcript imports with queue history.
- Added a dry-run-first, idempotent Codex hook installer that preserves unrelated hooks.
- Registered the read-only ThreadVault MCP server with the local Codex installation.
- Added compatibility for current `world_state`, `inter_agent_communication_metadata`, and repeated collaborative session metadata.
- Session detail preview mapping.
- Export preview state gate.
- Chinese UI localization hardening.
- JavaScript asset syntax checks.
- Local export and backup write verification.
- Completed-state spinner fix.
- Basic/pro mode documentation.
- Archive database vs export directory explanation.
- Full knowledge graph expansion.
- Standard documentation completeness pass.
- Legacy documentation migration to `docs/progress/archive/` after user confirmation.
- Retired active Web UI runtime, schemas, and tests for the 1.0.0 native desktop release.
- Removed the remaining active Web UI launcher, readiness test, and retired discovery metadata for the 1.0.1 cleanup.
- Removed active team/governance/shared-server code and contracts for the personal-only 2.0.0 baseline.
- Split and hardened the read-only MCP implementation.
- Added compacted-event compatibility and schema v6 repair for stale parser warnings.
- Established a project `.venv` with a clean dependency check and removed stale ThreadVault distribution metadata.
- Prepared the v1.0.0 release documentation and acceptance gate.
- Generated output policy: `.gitignore` excludes `threadvault-ui-output/`, `threadvault-ui-backups/`, `exports/`, `backups/`, `data/`, local database files, and `.env` files.

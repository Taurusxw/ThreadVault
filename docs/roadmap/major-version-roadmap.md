# ThreadVault Major Version Roadmap

## Summary

ThreadVault is at `v0.31.0`: the local CLI and data-layer MVP are complete. The remaining product work should no longer live in one vague future bucket. This roadmap splits it into three major lines:

- `v1`: personal knowledge layer.
- `v2`: retrieval and interfaces.
- `v3`: richer clients and team governance.

The roadmap keeps the original local-first and privacy-first posture. Raw Codex transcripts stay local by default, external model calls remain opt-in, and heavier client or server layers build on top of the existing archive instead of replacing it.

## Current Baseline: v0.31.0

`v0.31.0` is the completed CLI/data-layer baseline:

- Import local Codex `sessions` and `archived_sessions`.
- Normalize current and legacy JSONL records into SQLite.
- Search with SQLite FTS5.
- Export Markdown, JSON, JSONL, and CSV.
- Generate local rule summaries with evidence event IDs.
- Scan and redact sensitive content.
- Diagnose, audit, backup, restore, and validate JSON schema contracts.

This baseline should remain stable while later versions add new modules around it.

## Version Boundaries

| Version | Theme | Primary Outcome | Explicitly Not The Center |
|---|---|---|---|
| `v1` | Personal knowledge layer | Codex sessions are automatically archived and exported into durable Markdown/Obsidian/Skill knowledge assets. | Vector search, desktop UI, server, team permissions. |
| `v2` | Retrieval and interfaces | CLI, MCP, agents, and later clients query one stable retrieval interface with optional semantic search. | Heavy GUI and team governance. |
| `v3` | Clients and team governance | ThreadVault becomes usable through richer clients or optional shared infrastructure. | Replacing local-first defaults with mandatory cloud/server use. |

Deferred scope is therefore reclassified:

- Web UI, TUI, desktop app, VS Code/Cursor extension -> `v3` client work.
- MCP server and REST API -> `v2` interface work first, `v3` deployment hardening later.
- Vector database and embedding index -> `v2` retrieval work.
- Cloud sync, team permissions, centralized audit -> `v3` governance work.
- External LLM summaries -> optional adapter after evidence contracts are stable, not a default path.

## Architecture Direction

Future work should deepen four modules before adding many more command branches:

- `Ingestion Automation` module: owns Hook events, scan requests, queue/process behavior, and safe import scheduling.
- `Export Target` module: owns archive selections, target profiles, export manifests, and target-specific writers.
- `Summary Pipeline` module: owns evidence-backed summary bundles and validation.
- `Retrieval` module: owns stable search queries and ranked results across FTS5, semantic, and hybrid retrieval.

These names are roadmap-level public interface names. The final function signatures, schemas, and CLI options should be designed in the implementation phase for each major version.

## Acceptance Shape

Each major version should include:

- A phase plan under `docs/progress/archive/legacy-v0/phases/` for v0 archives, and a version-specific equivalent for future active development.
- An external or architecture review note beside the relevant phase plan or under the active version archive.
- Development progress updates in `docs/PROGRESS.md` and round records under `docs/progress/rounds/`.
- Focused tests for new module behavior and public JSON contracts.
- End-to-end smoke validation with fixture data before marking the version complete.

DOCX synchronization is intentionally separate from this roadmap. Markdown remains the planning source of truth until a formal document-sync phase is requested.




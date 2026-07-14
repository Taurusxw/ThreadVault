# ThreadVault AGENTS.md

This project follows the global Codex rules in `<user-home>\.codex\AGENTS.md`.

## Project Name

ThreadVault.

## Project Goal

ThreadVault is a local-first, privacy-first archive and retrieval tool for local Codex sessions.

## Technical Stack

- Python CLI and stdlib Tkinter native desktop app.
- SQLite storage with FTS-backed search.
- Read-only MCP stdio integration for local agents.
- Personal-only 2.x runtime: no team mode, central governance runtime, shared HTTP server, or browser-first workflow. Historical records remain under `docs/progress/archive/legacy-v3` and `legacy-v4`.
- Pytest and ruff for validation.

## Project Rules

- Treat the native desktop app as the primary local interface for the personal-only 2.x line.
- Do not reintroduce Web UI launch commands or browser-first workflows.
- Do not reintroduce team mode, central governance contracts, or a shared HTTP server unless explicitly requested as a new product direction.
- Do not introduce a separate frontend build pipeline unless explicitly requested.
- Reuse `ArchiveStore` and existing ThreadVault CLI/runtime contracts.
- Keep canonical human conversation and the clean index in the hot database; route bulky reversible evidence through the content-addressed cold store.
- Do not silently delete unique conversation content. Destructive cold pruning must be reference-aware, dry-run-first, and explicitly applied.
- Storage migrations must be copy-on-write and validate counts, conversation digest, database health, and cold references before activation.
- Do not bypass privacy scanning, export preview gates, or confirmation gates.
- Treat `docs/progress/archive/legacy-v0` through `docs/progress/archive/legacy-v4` and
  `docs/progress/archive/legacy-development-progress.md` as migrated legacy historical records.
- Do not recreate `docs/v0` through `docs/v4` or `docs/development-progress.md`.

## Completion Standard

Every development round must update the relevant code, tests, and documentation, and must leave a trace under
`docs/progress/rounds/`.

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
- Retired stdlib local HTTP server, static Web UI runtime, launcher, tests, and discovery metadata removed from the 1.0.x active package; historical records live under `docs/progress/archive/legacy-v4`.
- Pytest and ruff for validation.

## Project Rules

- Treat the native desktop app as the primary local interface for the 1.0.x line.
- Do not reintroduce Web UI launch commands or browser-first workflows.
- Do not introduce a separate frontend build pipeline unless explicitly requested.
- Reuse `ArchiveStore` and existing ThreadVault CLI/runtime contracts.
- Do not bypass privacy scanning, export preview gates, or confirmation gates.
- Treat `docs/progress/archive/legacy-v0` through `docs/progress/archive/legacy-v4` and
  `docs/progress/archive/legacy-development-progress.md` as migrated legacy historical records.
- Do not recreate `docs/v0` through `docs/v4` or `docs/development-progress.md`.

## Completion Standard

Every development round must update the relevant code, tests, and documentation, and must leave a trace under
`docs/progress/rounds/`.

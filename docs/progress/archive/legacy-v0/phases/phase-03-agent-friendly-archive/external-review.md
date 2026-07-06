# Phase 03 / v0.3 External Review: Agent-Friendly Archive

## Reuse Principles

ThreadVault borrows proven interface shapes and workflow ideas, not source code. This keeps the project license-clean and avoids depending on unstable internals of unrelated tools.

## Projects

### MeXenon/codex-session-export

- Useful ideas: session/project view, section filters, Markdown export, last-turn focused reading.
- ThreadVault adaptation: `--last-turns`, `--include`, `--exclude`, project Markdown index.
- Risk: exporter-focused design does not replace ThreadVault's SQLite fact layer.

### ezyyeah/codex-export

- Useful ideas: multi-format output and template-oriented export.
- ThreadVault adaptation: `export --format md|json|jsonl|csv`.
- Risk: do not copy implementation; use Python standard library for JSONL/CSV.

### jinghan23/codex-export

- Useful ideas: cover both Codex CLI and Desktop histories, session-id based operations.
- ThreadVault adaptation: read-only `state_5.sqlite` enrichment via `threads.rollout_path`.
- Risk: Codex Desktop state schema can change; enrichment remains best effort.

### ccusage

- Useful ideas: clear warning that Codex data source parsing is experimental, local multi-source discovery.
- ThreadVault adaptation: `doctor`, parse warnings, no assumption that token counts always exist.
- Risk: ThreadVault is not a usage-cost tool, so cost estimation remains out of scope.

### CASS

- Useful ideas: robot-friendly CLI, JSON output, minimal result fields, health/guide commands.
- ThreadVault adaptation: `capabilities --json`, `robot-docs guide`, `robot-docs schemas`, `search --fields minimal`.
- Risk: ThreadVault remains Codex-focused for now, not a multi-agent universal index.

### OpenAI Codex Docs

- Useful ideas: `sessions`, `archived_sessions`, local app-server archive behavior, and hooks metadata.
- ThreadVault adaptation: local-first discovery and transcript parser adapter.
- Risk: transcript format is not a stable public API, so raw JSON shapes stay behind normalizers.


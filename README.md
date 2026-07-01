# ThreadVault

ThreadVault is a local-first, privacy-first CLI for archiving local Codex session JSONL files into a searchable SQLite knowledge base.

It discovers Codex transcripts from local `sessions` and `archived_sessions` directories, normalizes current and legacy event shapes, indexes content with SQLite FTS5, and provides command-line tools for listing, searching, exporting, summarizing, auditing, backing up, and restoring the archive.

Current package version: `0.31.0`.

## Current Status

ThreadVault has completed its CLI/data-layer MVP. The stable baseline includes:

- Local Codex transcript discovery with `--codex-home` overrides.
- Streaming JSONL import into SQLite.
- Normalized `sessions`, `turns`, `events`, `import_logs`, and `parse_warnings` tables.
- FTS5 search over normalized event text.
- Markdown, JSON, JSONL, and CSV export.
- Local rule-based summaries with evidence event IDs.
- Privacy scanning with warn, redact, and fail modes.
- JSON output contracts, packaged JSON Schemas, and validation helpers.
- Corpus audit reports, audit history, and diff utilities.
- Local config, retention policies, database backup, restore preflight, safe restore, and restore history.

Not included in the current baseline: automatic ingestion hooks, Obsidian/Markdown vault export, semantic/vector retrieval, MCP or REST interfaces, desktop/IDE clients, cloud sync, team permissions, and external LLM summaries.

## Install

Use Python 3.11 or newer. On Windows with the Python launcher:

```powershell
py -3.12 -m pip install -e ".[dev]"
```

Verify the CLI:

```powershell
threadvault --help
```

## Quick Start

Initialize the local archive database:

```powershell
threadvault init
```

Import Codex sessions from the default local Codex home:

```powershell
threadvault import
```

Import from a custom Codex home:

```powershell
threadvault import --codex-home C:\Users\you\.codex
```

List imported sessions:

```powershell
threadvault list
```

Search the archive:

```powershell
threadvault search pytest
```

Export a session:

```powershell
threadvault export --session SESSION_ID --out out
```

Generate a local evidence-backed summary:

```powershell
threadvault summarize --session SESSION_ID --format markdown
```

Run diagnostics:

```powershell
threadvault stats
threadvault doctor
threadvault warnings
```

## JSON And Agent Workflows

Most read-oriented and maintenance commands support `--json`. When `--json` is provided, commands write machine-readable JSON to stdout.

Useful discovery and contract commands:

```powershell
threadvault capabilities --json
threadvault robot-docs guide --json
threadvault robot-docs schemas --json
threadvault schemas list --json
```

Validate a saved payload against a packaged schema:

```powershell
threadvault search pytest --json --fields minimal > search.json
threadvault validate-json --schema search_minimal --input search.json --json
```

Write packaged JSON Schemas to disk:

```powershell
threadvault schemas write --out docs/schemas --json
```

## Privacy And Local Data

ThreadVault does not upload raw session data. Imports, search, summaries, audits, backups, and restores operate on local files and local SQLite databases.

By default, the archive database is stored at:

- Windows: `%LOCALAPPDATA%\threadvault\threadvault.db`
- macOS/Linux: `~/.local/share/threadvault/threadvault.db`

Every command that reads or writes the archive accepts `--db PATH`.

Use privacy modes before exporting content:

```powershell
threadvault privacy-scan --session SESSION_ID --json
threadvault export --session SESSION_ID --privacy-mode warn --out out
threadvault export --session SESSION_ID --privacy-mode redact --out out
threadvault export --session SESSION_ID --privacy-mode fail --out out
```

Backups are local SQLite database files and may contain private transcript content. Treat backup files, restore history, and manifest metadata as local/private artifacts.

## Configuration

Create and inspect a local `threadvault.toml`:

```powershell
threadvault config init --json
threadvault config show --json
threadvault config doctor --json
```

Example config:

```toml
[privacy]
allowlist = [
  { kind = "email", text = "dev@example.com" },
  { kind = "windows_abs_path", pattern = '^E:\\\\Codex\\\\' },
]

[audit_history]
keep = 20

[backup_history]
keep = 10

[restore_history]
keep = 20
```

For Windows path regex patterns, TOML literal strings such as `pattern = '^E:\\\\Codex\\\\'` are easier to maintain than double-escaped basic strings.

## Backup And Restore

Create and verify a local backup:

```powershell
threadvault backup --out backups --json
threadvault backup-history latest --dir backups --json
threadvault backup-history verify-latest --dir backups --json
```

Plan a restore without writing files:

```powershell
threadvault restore-plan --backup backups\threadvault-backup-YYYYMMDDTHHMMSSZ.db --target-db restored\threadvault.db --json
```

Apply a restore only after review:

```powershell
threadvault restore --backup backups\threadvault-backup-YYYYMMDDTHHMMSSZ.db --target-db restored\threadvault.db --apply --json
```

Restore and prune operations are conservative by default. Destructive cleanup requires explicit `--apply`.

## Documentation

The root README is intentionally short. Detailed planning, usage, contracts, and historical development records live under `docs/`.

- `docs/README.md` - documentation map.
- `docs/THREADVAULT_USAGE_MANUAL.md` - full CLI usage manual.
- `docs/development-progress.md` - chronological development log.
- `docs/v1/README.md` - active v1 development archive.
- `docs/v0/README.md` - completed v0 archive and phase index.
- `docs/roadmap/major-version-roadmap.md` - major-version roadmap.
- `docs/roadmap/v1-personal-knowledge-layer.md` - next development line.
- `docs/schemas/` - packaged JSON Schema contract artifacts.

## Development

Run the normal checks:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Useful smoke checks:

```powershell
threadvault --help
threadvault capabilities --json
threadvault robot-docs schemas --json
```

Before starting new feature work, read `docs/roadmap/v1-personal-knowledge-layer.md` and `docs/v0/README.md`.

## License

ThreadVault is released under the MIT License. See `LICENSE` for details.

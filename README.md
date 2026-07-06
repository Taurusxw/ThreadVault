# ThreadVault

ThreadVault is a local-first, privacy-first archive, retrieval, export, governance, and native desktop tool for local Codex sessions.

It discovers Codex transcript JSONL files from local `sessions` and `archived_sessions` directories, normalizes current and legacy event shapes into SQLite, indexes searchable text with SQLite FTS5, and exposes the archive through CLI commands, JSON contracts, agent-facing retrieval, export targets, governance diagnostics, MCP, and a minimal native desktop app.

Current package version: `1.0.0`.

## What It Is For

ThreadVault answers a practical question: "What did I already do with Codex, where is the useful evidence, and how do I reuse it without digging through raw transcript files?"

Typical uses:

- Search old Codex work by keyword, project path, tool call, file path, or problem.
- Open a session and inspect its summary, event previews, warnings, and evidence event IDs.
- Export selected sessions or project material to Markdown, Obsidian-ready vault files, or a Codex Skill candidate folder.
- Give Codex or another local agent a compact, evidence-backed context package instead of dumping raw transcripts.
- Run local privacy scans, backups, restore plans, diagnostics, schema validation, and governance readiness checks.

## Current Status

The stable baseline now includes:

- Local Codex transcript discovery with `--codex-home` overrides.
- Streaming JSONL import into SQLite.
- Normalized `sessions`, `turns`, `events`, `import_logs`, `parse_warnings`, ingestion queue, and optional vector tables.
- FTS5 search over normalized event text.
- Retrieval, hybrid retrieval, summary chunks, optional local deterministic vector indexing, and agent-facing retrieval payloads.
- Markdown, JSON, JSONL, CSV, Obsidian, and Codex Skill candidate exports.
- Local rule-based summaries with evidence event IDs.
- Privacy scanning with `warn`, `redact`, and `fail` modes.
- JSON output contracts, packaged JSON Schemas, and validation helpers.
- Corpus audit reports, audit history, backup/restore workflows, restore history, and retention helpers.
- Optional local governance readiness, policy, audit, identity actor, preflight, and instrumentation surfaces.
- A primary minimal native Tkinter desktop app that uses background loading and does not require a browser.
- Native-first discovery metadata: capabilities and robot docs now advertise `native_desktop` as the primary local interface and the browser UI as retired.
- Retired personal Web UI runtime, active schemas, and Web UI tests have been removed from the active 1.0.0 package; v4 evidence remains in `docs/progress/archive/legacy-v4/`.
- A read-only MCP stdio server for Codex, ZCode, OpenCode, and other MCP-capable local agents.

Still intentionally not default:

- Uploading raw transcripts.
- Mandatory cloud sync or hosted server use.
- Mandatory external LLM summaries.
- Mandatory vector indexing.
- Team/shared enforcement as a requirement for personal use.

## Versioning

ThreadVault uses semantic package versions for active development. Substantive optimization or development changes should advance the package version, update `README.md`, and add a dated `docs/CHANGELOG.md` entry.

The 1.0.0 release line uses the native desktop app as the primary local interface and keeps the retired browser Web UI only as archived v4 historical evidence.

Current and historical version line:

| Version | Focus |
|---|---|
| `1.0.0` | Native desktop primary release; removed active personal Web UI runtime, schemas, and tests. |
| `0.49.0` | Retired active Web UI CLI commands and redirected the old browser launcher to the desktop app. |
| `0.48.0` | Native-first capability and robot-doc alignment for the 1.0.0 migration. |
| `0.47.0` | Desktop-first launcher guidance with the Web UI launcher marked as legacy fallback. |
| `0.46.0` | Native desktop Windows launcher script. |
| `0.45.0` | Non-window native desktop smoke command for automated verification. |
| `0.44.0` | Native desktop Tk thread-safety hardening from runtime QA. |
| `0.43.0` | Native desktop governance diagnostics aggregation. |
| `0.42.0` | Native desktop schema write with explicit confirmation. |
| `0.41.0` | Native desktop restore apply for verified backups to new non-overwrite targets. |
| `0.40.0` | Native desktop advanced read-only panels for schemas, robot docs, and governance status. |
| `0.39.0` | Native desktop data-safety and maintenance actions with confirmation gates. |
| `0.38.0` | Minimal native Tkinter desktop app over existing client/export/safety contracts. |
| `0.37.0` | Compact desktop-tool visual density for the personal UI. |
| `0.36.0` | Personal UI information architecture refresh with MCP/AI integrations surfaced as a first-class workflow. |
| `0.35.0` | Lightweight Codex Skill candidate exports with progressive references and evidence indexes. |
| `0.34.0` | MCP stdio server for cross-agent retrieval, session detail, diagnostics, and export preview. |
| `0.33.0` | Clean knowledge index that keeps raw archive data but indexes high-value content by default. |
| `0.32.0` | Project-local archive DB default and custom archive DB path support. |
| `0.31.0` | Documentation completeness and personal UI path clarification baseline. |
| v4 line | Personal local Web UI. |
| v3 line | Richer clients and governance surfaces. |
| v2 line | Retrieval, hybrid/vector interfaces, and agent-facing retrieval. |
| v1 line | Personal knowledge layer and export targets. |
| v0 line | CLI/data-layer archive baseline. |

## Important Paths

ThreadVault uses different paths for different jobs. Keeping these separate avoids most confusion.

| Path | Default / Example | Purpose |
|---|---|---|
| Archive database | `<repo-root>\data\threadvault.db` in this project checkout | The local SQLite index/store used for search, retrieval, summaries, UI, backup, and restore. Override with `--db`, `THREADVAULT_DB`, or `[storage].archive_db`. |
| Export directory | `threadvault-desktop-export/` in the desktop flow | User-facing Markdown, Obsidian, or Skill files written after preview/review. |
| Backup directory | Usually `threadvault-desktop-backups/` or a user-provided folder | Local SQLite backup copies and manifests. |
| Config file | `%APPDATA%\threadvault\threadvault.toml` on Windows | Privacy allowlist, vector settings, history retention, and optional governance config. |
| Codex home | `%USERPROFILE%\.codex` unless `CODEX_HOME` or `--codex-home` is used | Source transcript files under `sessions` and `archived_sessions`. |

The archive database is not meant to be opened as a daily document. Use search, the UI, or exports to read and reuse the knowledge.

## Install

Use Python 3.11 or newer. On Windows with the Python launcher:

```powershell
cd <repo-root>
py -3.12 -m pip install -e ".[dev]"
```

Verify the CLI:

```powershell
threadvault --help
```

Use the console script `threadvault ...`; the package does not expose `py -m threadvault`.

## Fast Start: Local UI

For the smallest native UI, launch the desktop app:

```powershell
.\启动ThreadVault桌面版.cmd
```

Or run the CLI directly:

```powershell
threadvault desktop launch
```

The desktop app uses Python stdlib Tkinter, opens without a browser, and keeps archive/search/export-preview/safety/maintenance/advanced checks on background worker threads so the window stays responsive. Backup, reindex, vacuum, restore apply, and schema write actions use native confirmation prompts before writing locally; desktop restore apply only writes to a new target database and refuses overwrite.

Run a non-window desktop smoke check:

```powershell
threadvault desktop smoke --json
```

The older local Web UI launcher no longer starts a browser or local Web server. It redirects to the desktop launcher:

```powershell
.\启动ThreadVault中文界面.cmd
```

`threadvault ui serve` and `threadvault ui smoke` are retired from the active CLI.

## Fast Start: CLI

Initialize the local archive database:

```powershell
threadvault init
```

Import Codex sessions from the default local Codex home:

```powershell
threadvault import
```

List imported sessions:

```powershell
threadvault list
```

Search the archive:

```powershell
threadvault search pytest
```

Open agent-friendly retrieval:

```powershell
threadvault agent retrieve pytest --json
```

Expose ThreadVault as a local MCP stdio server for Codex, ZCode, OpenCode, or another MCP-capable client:

```powershell
threadvault mcp manifest --json
threadvault mcp serve
```

The first MCP tool set is intentionally read-only: capabilities, stats, doctor, agent retrieval, session detail, and export preview. Export preview reports planned Markdown/Obsidian/Skill files but does not write them.

For concrete Codex/OpenCode/ZCode/Obsidian setup snippets and AI self-configuration rules, see `docs/MCP_INTEGRATION.md`.

Export a session:

```powershell
threadvault export --session SESSION_ID --out <repo-root>\exports
```

Generate a Codex Skill candidate:

```powershell
threadvault export-target skill --session SESSION_ID --out <repo-root>\threadvault-ui-output --json
```

Skill candidate exports are intentionally lightweight: `SKILL.md` routes Codex through `references/index.md`, compact session summaries, per-session reference files, and an evidence index with short snippets. Use Markdown or Obsidian targets when you want larger raw-readable transcript exports.

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
threadvault agent manifest --json
threadvault client manifest --json
threadvault mcp manifest --json
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

ThreadVault does not upload raw session data. Imports, search, summaries, audits, backups, restores, and the personal UI operate on local files and local SQLite databases.

Use privacy modes before exporting content:

```powershell
threadvault privacy-scan --session SESSION_ID --json
threadvault export --session SESSION_ID --privacy-mode warn --out out
threadvault export --session SESSION_ID --privacy-mode redact --out out
threadvault export --session SESSION_ID --privacy-mode fail --out out
```

Backups are local SQLite database files and may contain private transcript content. Treat backup files, restore history, generated exports, and manifests as local/private artifacts unless you have reviewed them.

## Configuration

Create and inspect a local `threadvault.toml`:

```powershell
threadvault config init --json
threadvault config show --json
threadvault config doctor --json
```

Example config:

```toml
[storage]
# Optional local archive database override. Leave empty to use data/threadvault.db.
archive_db = ""

[privacy]
allowlist = [
  { kind = "email", text = "dev@example.com" },
  { kind = "windows_abs_path", pattern = '^E:\\\\Codex\\\\' },
]

[retrieval.vector]
enabled = false
adapter = "local-hash"
dimensions = 64

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

Restore and prune operations are conservative by default. Destructive cleanup requires explicit `--apply` or UI confirmation.

## Documentation

Detailed planning, usage, contracts, and historical development records live under `docs/`.

- `CONTEXT.md` - canonical project vocabulary.
- `AGENTS.md` - project-specific Codex rules.
- `CONTRIBUTING.md` - contribution workflow and privacy expectations.
- `SECURITY.md` - vulnerability reporting and local data boundary.
- `docs/README.md` - documentation map.
- `docs/DOC_INDEX.md` - standard documentation index.
- `docs/ARCHITECTURE.md` - module and UI architecture overview.
- `docs/API.md` - JSON contracts, MCP, and retired interface metadata.
- `docs/DATABASE.md` - SQLite storage overview.
- `docs/MCP_INTEGRATION.md` - MCP setup guide for Codex, OpenCode, ZCode, Obsidian, and AI self-configuration.
- `docs/KNOWLEDGE_GRAPH.md` - project entity and relationship map.
- `docs/THREADVAULT_USAGE_MANUAL.md` - full CLI/UI usage manual.
- `docs/progress/archive/` - migrated historical development records.
- `docs/progress/rounds/` - current development trace records.
- `docs/progress/releases/` - release notes, acceptance, and release risk records.
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
threadvault desktop smoke --json
```

Before starting new feature work, read `AGENTS.md`, `CONTEXT.md`, the active standard docs, and the relevant archived legacy record under `docs/progress/archive/`.

## License

ThreadVault is released under the MIT License. See `LICENSE` for details.

# Database

ThreadVault stores the local archive in SQLite. The archive database is the searchable/indexed store; it is not the same thing as generated Markdown/Obsidian/Skill exports.

## Default Location

In this project checkout the default archive database is:

```text
<repo-root>\data\threadvault.db
```

ThreadVault resolves the archive database in this order:

```text
1. --db PATH
2. THREADVAULT_DB
3. [storage].archive_db in threadvault.toml
4. data/threadvault.db under the project root
```

Every command that reads or writes the archive can still accept `--db PATH` for a one-off override.

## Database vs Export Directory

| Item | Example | Purpose |
|---|---|---|
| Archive database | `<repo-root>\data\threadvault.db` | SQLite index/store for imported Codex sessions, search, retrieval, UI, backup, and restore. |
| Export directory | `<repo-root>\threadvault-ui-output` | Generated Markdown, Obsidian, or Skill files for review/reuse. |
| Backup file | `threadvault-backup-YYYYMMDDTHHMMSSZ.db` | Local copy of the archive database. |

If the UI shows a different DB path, check `--db`, `THREADVAULT_DB`, or `[storage].archive_db` in `threadvault.toml`. Generated files should appear in the export directory, not inside the archive database.

## Primary Tables And Indexes

| Area | SQLite Object | Purpose |
|---|---|---|
| Metadata | `meta` | Internal version/schema metadata. |
| Sessions | `sessions` | Imported Codex session metadata and counts. |
| Turns | `turns` | Conversation turn grouping and aggregate text. |
| Events | `events` | Normalized event records, searchable text, tool/file/type metadata, and raw JSON. |
| Clean knowledge fields | `events.indexed_text`, `events.index_policy`, `events.value_level` | High-value search text and indexing policy derived from raw event text. |
| Import logs | `import_logs` | Import provenance, source path hash/status, and messages. |
| Parse warnings | `parse_warnings` | Parser/import warning records tied to sessions. |
| FTS index | `events_fts` | SQLite FTS5 index over cleaned `indexed_text`, tool names, and file paths. |
| FTS triggers | `events_ai`, `events_ad`, `events_au` | Keep `events_fts` synchronized with `events`. |
| Ingestion queue | `ingestion_queue` | Hook/CLI ingestion requests and processing status. |
| Vector metadata | `vector_index_meta` | Optional vector index adapter/dimensions/build metadata. |
| Vector chunks | `vector_chunks` | Optional local vector data derived from summary/evidence chunks. |

## Session/Event Model

```text
sessions
  -> turns
  -> events
  -> events_fts
```

Important relationships:

- `events.session_id` references `sessions.session_id`.
- `turns.session_id` references `sessions.session_id`.
- `events.turn_id` and `events.turn_index` connect events to turn-level grouping.
- `parse_warnings.session_id` connects parser warnings to the session that produced them.
- `events_fts.rowid` corresponds to `events.event_id`.

## Import Flow

```text
Codex JSONL file
  -> parser
  -> sessions row
  -> turns rows
  -> events rows
  -> parse_warnings rows when needed
  -> import_logs row
  -> derive indexed_text / index_policy / value_level
  -> FTS triggers update events_fts
```

Import behavior:

- Already imported files can be skipped based on path/hash provenance.
- Unknown or malformed transcript shapes should become warnings rather than aborting the whole corpus import.
- `delete_session` style operations remove session-linked rows through database relationships and cleanup logic.

## Search And Retrieval Storage

ThreadVault uses SQLite FTS5 as the default search path.

The raw archive keeps `events.text_content` and `events.payload_json` for audit and evidence. Search uses `events.indexed_text` so low-value machine noise does not dominate normal retrieval.

| Retrieval Feature | Storage Used | Notes |
|---|---|---|
| `threadvault search` | `events_fts`, `events`, `sessions` | CLI-compatible search output. |
| `threadvault retrieval query` | `events_fts`, `events`, `sessions` | Stable v2 retrieval contract with diagnostics. |
| `threadvault retrieval hybrid` | FTS plus optional `vector_chunks` | Falls back to FTS-only when vector is unavailable. |
| `threadvault agent retrieve` | Retrieval/hybrid payloads | Agent-oriented wrapper. |
| `threadvault vector index` | `vector_chunks`, `vector_index_meta` | Optional, config-gated, derived from summary chunks. |

Vector indexing is disabled by default and does not replace FTS.

## Clean Knowledge Index

ThreadVault keeps the raw archive intact but indexes a cleaned knowledge view by default.

| Policy | Meaning |
|---|---|
| `full` | Index the full event text. Used for normal user/assistant messages and short useful evidence. |
| `truncated` | Index head/tail excerpts for long tool output or very large messages. |
| `metadata_only` | Index only a placeholder and metadata for inline binary/image evidence such as base64 screenshots. |
| `skip_empty` | Do not index empty text events. |
| `skip_low_value` | Do not index routine machine events such as token counts, status events, and reasoning placeholders. |

`value_level` currently classifies events as `core`, `evidence`, or `noise`. This supports normal knowledge retrieval while preserving complete local evidence for exports, warnings, audit, and debugging.

## Ingestion Queue Storage

`ingestion_queue` stores lightweight work requests from hooks or CLI commands.

Typical statuses:

- `pending`
- `processing`
- `imported`
- `failed`
- `skipped`

Hook processes should enqueue work only. The queue processor performs import work when explicitly run, usually with `--apply`.

## Operational Artifacts Outside SQLite

Some ThreadVault artifacts are intentionally not stored inside the archive database:

| Artifact | Location | Why |
|---|---|---|
| Export files | User-selected output directory | Human/Codex-readable generated knowledge assets. |
| Export manifest | Export target root | Records written files, skipped sessions, privacy counts, evidence IDs. |
| Backup DB | User-selected backup directory | Recovery copy of the archive database. |
| Backup manifest | Beside backup DB | Backup provenance and verification. |
| Restore history | Local history path | Restore auditability without hiding restore records inside a target DB. |
| Corpus audit reports | Local audit directory | Anonymous corpus diagnostics and diffs. |
| Governance audit records | Local or configured central JSONL store | Operation audit trail. |

Treat all operational artifacts as local/private unless reviewed.

## Maintenance Commands

| Command | Effect |
|---|---|
| `threadvault doctor --json` | Checks DB, FTS, and Codex discovery health. |
| `threadvault stats --json` | Reports counts for sessions/events/turns/warnings/projects/files. |
| `threadvault warnings --summary --json` | Summarizes parser warning codes. |
| `threadvault reindex --fts-only --json` | Rebuilds `events_fts` from `events`. |
| `threadvault vacuum --json` | Runs SQLite VACUUM. |
| `threadvault backup --out DIR --json` | Copies the archive DB to a local backup file. |
| `threadvault restore-plan --backup DB --target-db DB --json` | Plans a restore without writing target data. |

## Schema Changes

Schema version `5` adds the clean knowledge index fields on `events`:

- `indexed_text`
- `index_policy`
- `value_level`

It also rebuilds `events_fts` over `indexed_text` instead of raw `text_content`. Raw `text_content` and `payload_json` remain in `events` for audit and export workflows.

When a future change adds or modifies tables:

1. Update `database.py`.
2. Update this document.
3. Update `docs/KNOWLEDGE_GRAPH.md` if a logical entity or relationship changed.
4. Add focused tests for migration/initialization behavior.
5. Re-run schema and smoke checks.

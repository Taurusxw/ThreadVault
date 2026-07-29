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
| Cold evidence store | `<repo-root>\data\threadvault-cold` | Content-addressed compressed payloads and binary assets referenced by event metadata. |
| Export directory | `<repo-root>\threadvault-ui-output` | Generated Markdown, Obsidian, or Skill files for review/reuse. |
| Backup file | `threadvault-backup-YYYYMMDDTHHMMSSZ.db` | Local copy of the archive database. |

If the UI shows a different DB path, check `--db`, `THREADVAULT_DB`, or `[storage].archive_db` in `threadvault.toml`. Generated files should appear in the export directory, not inside the archive database.

## Primary Tables And Indexes

| Area | SQLite Object | Purpose |
|---|---|---|
| Metadata | `meta` | Internal version/schema metadata. |
| Sessions | `sessions` | Imported Codex session metadata and counts. |
| Turns | `turns` | Conversation turn grouping and model/runtime metadata; duplicate conversation bodies are not persisted here. |
| Events | `events` | Normalized event records, canonical text, tool/file/type metadata, compact payloads, and cold references. |
| Cold metadata | `cold_blobs` | SHA-256 blob id, relative path, codec, kind, and byte counts for immutable cold evidence. |
| Storage fields | `events.payload_ref`, `events.storage_class`, `events.content_flags_json` | Link hot events to cold evidence and explain compaction decisions. |
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
  -> apply core/evidence/noise/quarantine storage policy
  -> write large reversible payloads to content-addressed cold blobs
  -> FTS triggers update events_fts
```

Import behavior:

- Already imported files can be skipped based on path/hash provenance.
- A matching path/hash is skipped only when the stored session `parse_version` matches the current schema/parser version, so compatibility releases can safely reprocess unchanged source files.
- A same-hash skip refreshes `import_logs.imported_at`; this records that the source was observed again and lets source freshness distinguish an untouched archive from a newly touched/moved source without duplicating content.
- Unknown or malformed transcript shapes should become warnings rather than aborting the whole corpus import.
- The Codex `Stop` hook imports only the hook-provided `transcript_path`; first-time backfill and manual recovery still scan the full Codex home.
- `storage sync` compares all discoverable sources with import provenance and targets only missing, changed, stale-parser, or newly touched transcripts. `storage auto --apply` runs this catch-up before backing up.
- `world_state` and other bulky metadata payloads move to cold evidence while small scalar stubs remain in SQLite.
- Exact duplicate `event_msg/agent_message` bodies become auditable hash stubs when the canonical assistant response exists; unique agent messages remain intact.
- `delete_session` style operations remove session-linked rows through database relationships and cleanup logic.

## Search And Retrieval Storage

ThreadVault uses SQLite FTS5 as the default search path.

The hot archive keeps canonical `events.text_content`, compact `events.payload_json`, and `events.payload_ref`. Search uses `events.indexed_text`; full bulky payloads remain locally recoverable from cold evidence when their storage class requires reversibility.

| Retrieval Feature | Storage Used | Notes |
|---|---|---|
| `threadvault search` | `events_fts`, `events`, `sessions` | CLI-compatible search output. |
| `threadvault retrieval query` | `events_fts`, `events`, `sessions` | Stable v2 retrieval contract with diagnostics. |
| `threadvault retrieval hybrid` | FTS plus optional `vector_chunks` | Falls back to FTS-only when vector is unavailable. |
| `threadvault agent retrieve` | Retrieval/hybrid payloads | Agent-oriented wrapper. |
| `threadvault vector index` | `vector_chunks`, `vector_index_meta` | Optional, config-gated, derived from summary chunks. |

Vector indexing is disabled by default and does not replace FTS.

## Clean Knowledge Index

ThreadVault keeps canonical conversation intact, retains reversible bulky evidence in cold storage, and indexes a cleaned knowledge view by default.

| Policy | Meaning |
|---|---|
| `full` | Index the full event text. Used for normal user/assistant messages and short useful evidence. |
| `truncated` | Index head/tail excerpts for long tool output or very large messages. |
| `metadata_only` | Index only a placeholder and metadata for inline binary/image evidence such as base64 screenshots. |
| `skip_empty` | Do not index empty text events. |
| `skip_low_value` | Do not index routine machine events such as token counts, status events, and reasoning placeholders. |
| `skip_duplicate` | Do not index an exact duplicate of a canonical assistant body. |

`value_level` currently classifies events as `core`, `evidence`, or `noise`. This supports normal knowledge retrieval while preserving complete local evidence for exports, warnings, audit, and debugging.

## Ingestion Queue Storage

`ingestion_queue` stores lightweight work requests from hooks or CLI commands.

Typical statuses:

- `pending`
- `processing`
- `completed`
- `failed`
- `skipped`

An applied Codex hook records a request, marks it `processing`, imports only the named transcript, then marks it `completed` or `failed`. The standalone queue processor remains available for pending manual/fallback requests and requires explicit `--apply`.

## Operational Artifacts Outside SQLite

Some ThreadVault artifacts are intentionally not stored inside the archive database:

| Artifact | Location | Why |
|---|---|---|
| Export files | User-selected output directory | Human/Codex-readable generated knowledge assets. |
| Export manifest | Export target root | Records written files, skipped sessions, privacy counts, evidence IDs. |
| Backup DB | User-selected backup directory | Recovery copy of the archive database. |
| Backup manifest | Beside backup DB | Backup provenance and verification. |
| Cold blobs | Sibling `threadvault-cold` directory | Large reversible evidence kept outside the hot SQLite file. |
| Storage backup manifest | Profile backup root | Binds Core/Evidence/Forensic contents and checksums. |
| Restore history | Local history path | Restore auditability without hiding restore records inside a target DB. |
| Corpus audit reports | Local audit directory | Anonymous corpus diagnostics and diffs. |

Treat all operational artifacts as local/private unless reviewed.

## Maintenance Commands

| Command | Effect |
|---|---|
| `threadvault doctor --json` | Opens the normal store, applies pending idempotent schema migrations, then checks DB, FTS, and Codex discovery health. |
| `threadvault mcp serve` doctor tool | Checks an existing DB through a read-only connection; it never creates or migrates the DB. |
| `threadvault stats --json` | Reports counts for sessions/events/turns/warnings/projects/files. |
| `threadvault warnings --summary --json` | Summarizes parser warning codes. |
| `threadvault reindex --fts-only --json` | Rebuilds `events_fts` from `events`. |
| `threadvault vacuum --json` | Runs SQLite VACUUM. |
| `threadvault backup --out DIR --json` | Copies the archive DB to a local backup file. |
| `threadvault storage audit --json` | Reports hot/cold size, storage classes, and largest event categories. |
| `threadvault storage sync --json` | Reports source freshness without writing; add `--apply` to import only stale sources. |
| `threadvault storage rebuild --target-db DB --apply --json` | Builds a compact copy and validates it without overwriting the source. |
| `threadvault storage verify --deep --json` | Checks cold presence/size and optionally decompresses and hashes every blob. |
| `threadvault storage prune --json` | Dry-runs reference-aware cold garbage collection; add `--apply` to delete. |
| `threadvault storage auto --apply --json` | Catches up stale sources, then selects at most one due backup tier, verifies it, and retains bounded automatic generations. |
| `threadvault storage backup --profile core|evidence|forensic --out DIR --json` | Creates a minimal, recoverable, or source-complete backup profile. |
| `threadvault restore-plan --backup DB --target-db DB --json` | Plans a restore without writing target data. |

## Schema Changes

Schema version `8` adds the hot/cold lifecycle:

- `cold_blobs` stores content-addressed blob metadata;
- events gain `payload_ref`, original size counters, `storage_class`, and compaction flags;
- canonical messages remain hot, repeated turn-body columns are no longer populated, and exact duplicate assistant bodies become hash stubs;
- full payload hydration remains available to export, privacy scan, and `storage event`;
- copy-on-write rebuild validates archive counts, canonical conversation digest, doctor, FTS, and cold references before activation.

Schema version `7` repairs current Codex metadata and warning taxonomy without adding columns:

- old `unknown` rows for `world_state` and `inter_agent_communication_metadata` recover their real top-level type;
- those metadata events keep raw payloads but remain `skip_empty` / `noise` in the clean index;
- obsolete `duplicate_session_meta` warnings are removed because repeated metadata is valid collaborative provenance;
- genuine incomplete function-call warnings remain intact.

Schema version `6` recognizes Codex `compacted` records and repairs data imported before that event type was supported:

- matched legacy `unknown` events become `compacted` assistant events;
- `payload.message` becomes `text_content` and is classified into the clean index;
- only the corresponding stale `unknown_current_type` warnings are removed;
- unrelated parse warnings remain intact.

Schema version `5` added the clean knowledge index fields on `events`:

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

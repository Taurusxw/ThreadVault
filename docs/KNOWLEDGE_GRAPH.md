# Knowledge Graph

This document is the project-level knowledge graph for ThreadVault. It records the main domain entities, the modules that own them, the data flows between them, and the safety boundaries that keep the system local-first and privacy-first.

This is not a claim that ThreadVault stores a graph database. The runtime archive is SQLite. The "knowledge graph" here is a maintained map of project concepts and relationships so future UI, CLI, retrieval, export, and governance work can reuse the same model.

## Reading Guide

- Use this document when deciding where a new workflow belongs.
- Use `docs/DATABASE.md` for physical SQLite storage details.
- Use `docs/API.md` for the local personal UI HTTP surface.
- Use `docs/schemas/` and `threadvault schemas` commands for exact JSON contracts.
- Use `CONTEXT.md` for the canonical vocabulary.

## System Map

```mermaid
flowchart LR
  Codex["Local Codex transcript files"] --> Parser["Parser / Importer"]
  Parser --> Archive["SQLite Archive"]
  Hooks["Codex Hook Adapter"] --> Queue["Ingestion Queue"]
  Queue --> Parser

  Archive --> Store["ArchiveStore"]
  Store --> Search["FTS Retrieval"]
  Store --> Summary["Summary Pipeline"]
  Summary --> Vector["Optional Vector Chunks"]
  Search --> Agent["Agent Retrieval"]
  Vector --> Hybrid["Hybrid Retrieval"]
  Search --> Hybrid
  Hybrid --> Agent

  Store --> Client["Client Interface"]
  Client --> UI["Personal Web UI"]
  Store --> MCP["MCP Stdio Interface"]
  MCP --> ExternalAgents["Codex / ZCode / OpenCode"]
  Store --> ExportPreview["Export Preview"]
  ExportPreview --> ExportWrite["Export Target Writes"]
  ExportWrite --> Output["Markdown / Obsidian / Skill Output"]

  Store --> Privacy["Privacy Scan"]
  Privacy --> ExportPreview
  Privacy --> ExportWrite

  Store --> Backup["Backup / Restore"]
  Store --> Governance["Governance / Audit / Policy"]
  Governance --> UI
  Governance --> Client
```

## Layered Model

| Layer | Core Entities | Owning Modules | Notes |
|---|---|---|---|
| Source | Codex Transcript File, Codex Home, Hook Event | `codex_adapter.py`, `codex_hooks.py`, `config.py`, `parser.py` | Input is local JSONL under `sessions` or `archived_sessions`. Hooks enqueue work; they do not run heavy archive jobs. |
| Archive | Archive Database, Session, Turn, Event, Clean Knowledge Field, Import Log, Parse Warning, FTS Index | `database.py`, `importer.py`, `store.py` | SQLite is the durable local archive; default search uses cleaned knowledge text derived from raw events. |
| Knowledge | Summary, Evidence Event, Summary Chunk, Vector Chunk | `summarizer.py`, `summary_pipeline.py`, `vector_adapter.py` | Summaries remain evidence-backed. Vector chunks are optional and derived from summaries/evidence, not raw-event indexing by default. |
| Retrieval | Retrieval Query, Retrieval Result, Hybrid Result, Agent Retrieval Payload | `retrieval.py`, `hybrid_retrieval.py`, `agent_interface.py` | FTS is the default path. Hybrid can combine FTS, vector, recency, project, and path signals. |
| Client | Client Manifest, Client Overview, Client Session Detail, Client Export Preview, Client Warnings | `client_interface.py`, `client_runtime.py` | Client surfaces package archive data into stable UI/agent-friendly payloads. |
| Export | Export Selection, Export Preview, Export Target, Export Manifest, Output File | `export_targets.py`, `exporter.py` | Write actions must follow preview acceptance and privacy handling. |
| Safety | Privacy Finding, Governance Preflight, Permission Check, Audit Record, Policy Document | `privacy.py`, `governance.py`, `app_config.py` | Safety controls wrap reads, exports, raw access, external model calls, backup/restore, and future shared use. |
| Operations | Backup, Backup Manifest, Restore Plan, Restore History, Audit History | `backup_manifest.py`, `backup_history.py`, `restore_plan.py`, `restore.py`, `restore_history.py`, `audit.py` | Local operational artifacts may contain private archive data and should be treated as private. |
| Interface | CLI Command, Local HTTP Route, UI Action, MCP Tool, JSON Schema | `cli.py`, `personal_ui.py`, `mcp.py`, `schemas.py` | UI and agents should reuse existing store/client contracts instead of duplicating parser or database logic. |

## Core Entity Catalog

| Entity | Definition | Primary Producer | Primary Consumers | Persistence |
|---|---|---|---|---|
| Codex Transcript File | Local Codex JSONL source file from `sessions` or `archived_sessions`. | Codex runtime outside ThreadVault | Parser, importer, audit | Local filesystem |
| Codex Home | Root directory used to discover local Codex transcript files. | User config / CLI option | Importer, hook adapter, ingestion queue | Config / command input |
| Hook Event | Lightweight signal that ThreadVault should enqueue ingest work. | Codex hook adapter | Ingestion queue | SQLite `ingestion_queue` |
| Ingestion Request | A queued request to scan/import from a Codex home. | Hook adapter or CLI | Ingestion processor | SQLite `ingestion_queue` |
| Archive Database | Local SQLite database containing imported archive state. | `init_db`, import workflows | Store, CLI, UI, retrieval, export, backup | SQLite file |
| Session | Primary archived unit, normally one Codex conversation. | Parser/importer | Overview, session detail, summary, export, retrieval | SQLite `sessions` |
| Turn | Conversation grouping for related user/assistant/tool events. | Importer | Session detail, summary chunks, vector chunks | SQLite `turns` |
| Event | Normalized message, tool, system, or warning-related record. | Parser/importer | Search, session detail, summaries, exports | SQLite `events`, `events_fts` |
| Clean Knowledge Field | Derived searchable text plus index policy/value level for one event. | Database migration/import | FTS retrieval, diagnostics | SQLite `events.indexed_text`, `index_policy`, `value_level` |
| Import Log | Provenance and status record for a source import attempt. | Importer | Diagnostics, doctor, audit | SQLite `import_logs` |
| Parse Warning | Structured warning emitted while parsing/importing. | Parser/importer | Warning detail, client warnings, diagnostics | SQLite `parse_warnings` |
| FTS Index | SQLite full-text index over cleaned event text and selected fields. | Database triggers / rebuild | Search, retrieval, hybrid retrieval | SQLite `events_fts` |
| Summary | Local, rule-based, evidence-backed condensation of a session/project. | Summarizer | Client detail, export targets, summary chunks | Derived at read/export time |
| Evidence Event | Event ID referenced by a summary, export, chunk, or result as supporting evidence. | Summarizer / retrieval | UI, exports, agents, validation | SQLite event reference |
| Summary Chunk | Stable chunk selected from session summary, turn summary, or evidence text. | Summary pipeline | Vector index, retrieval diagnostics | JSON payload / vector indexing |
| Vector Chunk | Optional embedded summary/evidence chunk. | Vector adapter | Vector query, hybrid retrieval | SQLite `vector_chunks` |
| Retrieval Query | Stable query object with text, filters, mode, and limits. | CLI, agent, UI | Retrieval module | Request payload |
| Retrieval Result | Ranked match with session/event references and snippet. | Retrieval module | CLI, UI, agent interface | Response payload |
| Hybrid Result | Ranked match with explanation across FTS, vector, recency, project, and path signals. | Hybrid retrieval | Agent interface, UI | Response payload |
| Agent Retrieval Payload | Agent-oriented retrieval response that hides raw local details unless debug is enabled. | Agent interface | Agents, UI `/api/retrieve` | JSON contract |
| Client Overview | UI/client summary of recent sessions and optional search results. | Client interface | Personal UI, future clients | JSON contract |
| Client Session Detail | UI/client payload for one session with summary, event previews, and evidence IDs. | Client interface | Personal UI, future clients | JSON contract |
| Client Export Preview | Client-facing export plan with files, privacy summary, and write readiness. | Client interface / export targets | Personal UI, export write gate | JSON contract |
| Client Warnings | Warning-focused session detail plus privacy scan summary. | Client interface | Personal UI | JSON contract |
| Export Selection | Session/project/range-style choice of archive material. | Export target request | Preview and export writers | Request payload |
| Export Preview | Read-only plan for files that would be written. | Export targets / client interface | UI gate, users, governance | JSON contract |
| Export Target | Concrete output profile: Markdown, Obsidian, or Codex Skill. | Export target module | Export writers | Filesystem output |
| Export Manifest | Machine-readable record of written files, skipped items, privacy counts, and evidence. | Export target writer | Users, future tools, validation | Output folder file |
| Output File | User-facing Markdown/Obsidian/Skill artifact. | Export writers | User, Codex, editors | Local filesystem |
| Privacy Finding | Sensitive-content finding with warn/redact/fail behavior. | Privacy scanner | Export, client warnings, UI | Response payload; sometimes manifest metadata |
| Backup | SQLite database copy for local recovery. | Backup workflow | Restore, verification, history | Local filesystem |
| Backup Manifest | Metadata/provenance file beside a backup. | Backup manifest writer | Backup verification | Local filesystem |
| Restore Plan | Dry-run plan for applying a backup to a target DB. | Restore planner | Restore apply, UI review | JSON payload |
| Restore History | Record of restore operations. | Restore workflow | Restore history UI/CLI | Local filesystem |
| Corpus Audit Report | Anonymized corpus-level report over local files. | Audit module | Audit history, diff | Local filesystem |
| Audit Record | Governance/operation event in a local or central audit log. | Governance module | Audit list, readiness checks | JSONL file |
| Identity Actor | Local static actor configuration for governance checks. | App config | Governance identity binding | Config payload |
| Policy Document | Local central policy or backup policy document. | User/configured governance input | Governance readiness/runtime | Local filesystem |
| Personal UI Action | Registered local UI command routed through `/api/action`. | `personal_ui.py` | Browser UI | Runtime registry |
| MCP Tool | Read-only stdio tool exposed to MCP-capable local agents. | `mcp.py` | Codex, ZCode, OpenCode, other MCP clients | Runtime manifest / JSON-RPC |
| JSON Schema | Packaged contract used to validate command/API payloads. | `schemas.py` | CLI, tests, agents, docs | `docs/schemas/` |

## Relationship Matrix

| From | Relationship | To | Owner / Contract |
|---|---|---|---|
| Codex Transcript File | is parsed into | Event | `parser.py`, `database.py` |
| Codex Transcript File | creates or updates | Session | `importer.py`, `database.py` |
| Event | belongs to | Session | `events.session_id` |
| Event | may belong to | Turn | `events.turn_id`, `events.turn_index` |
| Session | contains | Turn | `turns.session_id` |
| Turn | groups | Event | `turns`, `events.turn_index` |
| Import Log | records provenance for | Codex Transcript File | `import_logs.raw_path`, `raw_sha256` |
| Parse Warning | references | Session | `parse_warnings.session_id` |
| Event | indexes into | FTS Index | `events_fts` triggers |
| Event | derives | Clean Knowledge Field | `database.classify_index_text` |
| Clean Knowledge Field | indexes into | FTS Index | `events_fts` triggers |
| FTS Index | powers | Retrieval Result | `retrieval.py` |
| Summary | references | Evidence Event | `summary.evidence_event_ids` |
| Summary Chunk | derives from | Summary / Turn / Event | `summary_pipeline.py` |
| Vector Chunk | embeds | Summary Chunk | `vector_adapter.py` |
| Retrieval Result | references | Session / Event | `retrieval_query` contract |
| Hybrid Result | combines | FTS Result / Vector Result | `hybrid_retrieval` contract |
| Agent Retrieval Payload | wraps | Retrieval Result / Hybrid Result | `agent_retrieval` contract |
| Client Overview | lists | Session | `client_overview` contract |
| Client Session Detail | includes | Summary / Event Preview | `client_session` contract |
| Client Warnings | includes | Parse Warning / Privacy Finding | `client_warnings` contract |
| Export Preview | plans | Output File | `client_export_preview`, `export_target_manifest` |
| Export Target | writes | Output File | `export_targets.py`, `exporter.py` |
| Export Manifest | records | Output File / Privacy Finding / Evidence Event | `export_target_manifest` |
| Privacy Finding | gates or modifies | Export Target | `privacy_mode` warn/redact/fail |
| Restore Plan | must precede | Restore Apply | `restore_plan`, `restore` |
| Backup Manifest | verifies | Backup | `backup_manifest.py` |
| Governance Preflight | evaluates | Command / Operation | `governance_*_preflight` contracts |
| Permission Check | evaluates | Actor / Operation / Resource | `governance_permission_check` |
| Audit Record | records | Governance-sensitive Operation | `governance_audit_*` contracts |
| Personal UI Action | routes to | ArchiveStore Method | `ACTION_REGISTRY`, `/api/action` |
| MCP Tool | routes to | ArchiveStore Method | `mcp.py`, `threadvault mcp serve` |
| MCP Tool | returns | Agent Retrieval / Client Session / Client Export Preview Payload | `structuredContent` |
| JSON Schema | validates | JSON Payload | `schemas.py`, `docs/schemas/` |

## Database Mapping

| Logical Entity | SQLite Area | Notes |
|---|---|---|
| Archive Database | SQLite file | Default is `data/threadvault.db` under the project root; `--db`, `THREADVAULT_DB`, and `[storage].archive_db` can override it. |
| Session | `sessions` | Durable session metadata, project cwd, source kind, timestamps, event and warning counts. |
| Turn | `turns` | Grouping and aggregate text fields for user/assistant/tool activity. |
| Event | `events` | Normalized event text, type, tool, file path, raw JSON, and turn references. |
| Clean Knowledge Field | `events.indexed_text`, `events.index_policy`, `events.value_level` | Derived high-value search text and classification. |
| FTS Index | `events_fts` | FTS5 virtual table over `indexed_text`, maintained by event insert/update/delete triggers. |
| Import Log | `import_logs` | Raw path/hash/status provenance. |
| Parse Warning | `parse_warnings` | Parser/import warnings tied to sessions. |
| Ingestion Request | `ingestion_queue` | Hook/CLI queued work and processing status. |
| Vector Index Metadata | `vector_index_meta` | Adapter and dimensions for the optional local vector index. |
| Vector Chunk | `vector_chunks` | Embedded summary/evidence chunks with metadata and evidence event IDs. |

## Primary Data Flows

### 1. Import And Archive

```text
Codex home
  -> discover sessions / archived_sessions
  -> parse JSONL records
  -> normalize sessions, turns, events, parse warnings
  -> derive clean indexed_text and value levels
  -> write SQLite tables
  -> update events_fts through triggers
  -> expose list/search/stats/doctor/client views
```

Important boundaries:

- The importer reads local files only.
- Raw transcript text remains local.
- Hook-triggered ingestion should enqueue or narrowly signal work, not perform large scans inside the hook process.

### 2. Search, Retrieval, And Agent Use

```text
Query text + filters
  -> retrieval query
  -> FTS result set
  -> optional vector result set
  -> optional hybrid rank/explanation
  -> agent retrieval payload
  -> UI, CLI, MCP client, or future client
```

Important boundaries:

- FTS remains the default, always-available retrieval path.
- Vector retrieval is optional and config-gated.
- Vector chunks are derived from summaries/evidence; raw events are not vectorized by default.
- Agent payloads should not expose raw local paths unless local debug behavior is explicitly requested.

### 2.1 MCP Cross-Agent Use

```text
Codex / ZCode / OpenCode
  -> MCP stdio initialize + tools/list
  -> threadvault_retrieve / threadvault_session / threadvault_export_preview
  -> ArchiveStore contracts
  -> structuredContent returned to the agent
```

Important boundaries:

- MCP is a transport adapter, not a new archive implementation.
- MCP tools are read-only in the first version.
- `threadvault_export_preview` can plan Obsidian/Skill output but must not write files.
- Export writes stay explicit CLI/UI actions with privacy and preview gates.
- Obsidian remains a Markdown output consumer, not a direct SQLite client.

### 3. Summary And Evidence

```text
Session + events
  -> local rule summary
  -> evidence event IDs
  -> session detail, export preview, export target, summary chunks
```

Important boundaries:

- Summaries must remain traceable to stored event IDs.
- External LLM summaries are not the default path.
- Missing or weak evidence should remain visible as warnings rather than being hidden.

### 4. Export Preview And Export Write

```text
Selection + target profile + privacy mode
  -> export preview
  -> privacy scan
  -> user review / UI preview acceptance
  -> matching export write action
  -> output files + export manifest
```

Important boundaries:

- Preview is read-only.
- Write actions require preview acceptance in the UI/backend flow.
- Privacy mode controls behavior:
  - `warn`: report findings and write content.
  - `redact`: redact supported sensitive text before writing.
  - `fail`: block high-risk findings.
- Export output belongs in the configured/export directory, not inside the archive database.

### 5. Personal UI

```text
Browser at 127.0.0.1
  -> static HTML/CSS/JS from personal_ui.py
  -> GET /api/health and read routes
  -> POST /api/action for registered actions
  -> ArchiveStore methods
  -> JSON payloads and local filesystem outputs
```

Important boundaries:

- The UI is local-first and bound to `127.0.0.1` by default.
- The UI does not parse raw Codex transcripts itself.
- The UI reuses `ArchiveStore`, client interfaces, retrieval, export, backup/restore, schema, and governance contracts.
- Basic mode is an entry path for common tasks; pro mode exposes the broader workbench.

### 6. Backup, Restore, And History

```text
Archive database
  -> backup copy + optional manifest
  -> verify backup
  -> restore plan
  -> explicit restore apply
  -> restore history
```

Important boundaries:

- Backups may contain private transcript content.
- Restore apply is intentionally separated from restore planning.
- Destructive cleanup/prune operations require explicit apply/confirmation.

### 7. Governance And Audit

```text
Command / operation / actor / config
  -> governance status or preflight
  -> permission/readiness/policy result
  -> optional audit record
  -> UI and CLI diagnostics
```

Important boundaries:

- Governance is local opt-in by default.
- Identity actor binding is local static config in the current model, not authenticated enterprise identity.
- Read-only shared server and central policy/audit/backup flows are optional governance surfaces, not required for personal local use.
- External model calls remain explicit and policy-visible.

## Interface Surface Map

| Surface | Entry | Reads | Writes | Safety Notes |
|---|---|---|---|---|
| CLI | `threadvault ...` | Archive DB, config, local files | Archive DB, export files, backups, audit/history files | Command flags and JSON contracts define exact behavior. |
| Personal UI read routes | `GET /api/health`, `/api/client/*`, `/api/retrieve` | Archive DB, config | No archive writes expected | Used for browsing, search, session detail, warnings, and health. |
| Personal UI actions | `POST /api/action` | Archive DB, config | May write exports, backups, schemas, restore targets, maintenance operations | Registry marks confirmation, preview, and disabled/dangerous gates. |
| Agent interface | `threadvault agent retrieve ... --json` | Retrieval/hybrid/vector status | No writes | Designed for stable machine use and evidence references. |
| Client interface | `threadvault client ... --json` | Store, retrieval, governance status | Export preview is read-only; export writes use export target commands/actions | Designed for UI and future clients. |
| Schema interface | `threadvault schemas ...` | Packaged schema registry | Optional schema artifact writes | Validates JSON contracts. |
| Governance interface | `threadvault governance ...` | Config, policy files, audit stores | Optional audit/policy/audit-store writes | Separates readiness/preflight from enforcement. |

## Personal UI Action Families

| Family | Example Actions | Underlying Area | Write Risk |
|---|---|---|---|
| Archive browsing | `sessions_list`, `client_overview`, `client_session` | Store/client interface | Read-only |
| Search/retrieval | `search`, `retrieve`, `hybrid_retrieve`, `agent_retrieve` | Retrieval/agent interface | Read-only |
| Summary/vector | `summarize`, `summary_chunks`, `vector_status`, `vector_index` | Summary pipeline/vector adapter | `vector_index` writes optional vector tables |
| Privacy/warnings | `privacy_scan`, `warnings`, `client_warnings` | Privacy/parser warning surfaces | Read-only |
| Export | `client_export_preview`, `export_session`, `export_target_markdown`, `export_target_obsidian`, `export_target_skill` | Export targets/exporter | Export writes require preview acceptance |
| Backup/restore | `backup`, `backup_verify`, `restore_plan`, `restore_apply`, history actions | Backup/restore modules | Backup writes local files; restore apply changes target DB |
| Maintenance | `doctor`, `stats`, `reindex`, `vacuum` | Database/store diagnostics | Reindex/vacuum mutate archive internals |
| Schemas/docs | `schemas_list`, `schemas_show`, `validate_json`, `schemas_write`, `robot_docs_*` | Schema registry | Schema write creates/updates schema files |
| Governance | `governance_status`, `governance_preflight`, gap/readiness/smoke actions | Governance module | Some governance store/audit actions write local records |

## Safety And Privacy Boundaries

| Boundary | Rule |
|---|---|
| Raw transcript content | Stays local unless the user explicitly exports or shares local output files. |
| Archive DB vs export folder | The archive DB is the searchable index/store; export folders are user-facing files for Codex, Markdown tools, or Obsidian. |
| Preview vs write | Preview describes planned output; write actions create files only after the matching preview/confirmation path. |
| Privacy scan | Export and warning workflows must surface privacy findings instead of silently discarding them. |
| Confirmation | Restore apply, destructive maintenance, prune, and similar operations require explicit confirmation. |
| Vector indexing | Optional; disabled by default unless configured. It indexes derived chunks, not every raw event by default. |
| External model calls | Not default; must remain explicit and visible in governance diagnostics. |
| Server/shared use | Optional governance/client path; personal local CLI/UI remains usable without it. |

## What ThreadVault Is Not

| Misreading | Correct Model |
|---|---|
| "The knowledge graph is a graph database." | It is a maintained conceptual map. Runtime storage is SQLite. |
| "The DB path shown in the UI is an export." | The shown DB path is the archive/index database. Exports are files in an output directory. |
| "The UI owns archive logic." | The UI calls existing store/client/action contracts. |
| "Preview writes files." | Preview is read-only; write actions are separate. |
| "Vector search replaces FTS." | FTS remains the default. Vector/hybrid is optional. |
| "Governance means cloud/team mode is required." | Governance is local opt-in by default; shared use is optional. |
| "Backups are safe to share because they are operational artifacts." | Backups can contain private transcripts and should be treated as private. |

## Completeness Checklist For Future Changes

When adding a new capability, update this graph if the change introduces or materially changes any of the following:

- A new durable entity, table, schema, or artifact.
- A new write path from UI, CLI, agent, or server.
- A new privacy, confirmation, governance, or audit boundary.
- A new relationship between archive data and exported knowledge assets.
- A new retrieval adapter, ranking signal, or evidence reference type.
- A new client surface that bypasses or wraps existing store methods.

Before implementation, answer:

1. Which entity owns the data?
2. Is this read-only, write-only, or read-write?
3. Which JSON schema validates the public payload?
4. Which privacy and confirmation gates apply?
5. Does the output live in the archive DB, a generated export folder, or an operational history/audit file?
6. Which existing module should be reused instead of creating duplicate logic?

# Architecture

ThreadVault is a local-first archive, retrieval, export, governance, and personal UI system for Codex sessions. The architecture keeps raw transcript handling, search/retrieval, export generation, and UI interaction behind reusable Python modules so the CLI, local Web UI, and agent-facing contracts do not duplicate business logic.

## Design Principles

- Keep raw Codex transcript data local by default.
- Keep SQLite as the personal archive database.
- Put durable archive behavior behind `ArchiveStore`.
- Keep the personal Web UI static and stdlib-served unless explicitly changed.
- Reuse JSON schema contracts for CLI, UI, and agent payloads.
- Separate read-only preview from write actions.
- Keep privacy scan, confirmation, and governance gates visible at the API and UI layers.

## Main Modules

| Area | Primary Files | Responsibility |
|---|---|---|
| CLI | `src/threadvault/cli.py` | Typer command surface, argument parsing, user-facing command orchestration. |
| Configuration | `config.py`, `app_config.py`, `privacy_config.py` | Default paths, `threadvault.toml`, privacy allowlist, vector config, governance config. |
| Parser/import | `parser.py`, `importer.py`, `codex_adapter.py`, `database.py` | Codex JSONL discovery, parsing, normalization, imports, FTS triggers. |
| Store | `src/threadvault/store.py` | High-level archive workflows and reusable business entrypoint for CLI/UI. |
| Ingestion automation | `ingestion.py`, `codex_hooks.py` | Hook-safe ingestion queue, queue listing, dry-run/apply processing. |
| Retrieval | `retrieval.py`, `hybrid_retrieval.py`, `agent_interface.py` | Stable query contracts, FTS retrieval, hybrid ranking, agent-facing output. |
| Summary/vector | `summarizer.py`, `summary_pipeline.py`, `vector_adapter.py` | Evidence-backed summaries, summary/evidence chunks, optional local deterministic vectors. |
| Client interface | `client_interface.py`, `client_runtime.py` | Client manifest, overview, session detail, export preview, warnings, local TUI runtime. |
| MCP interface | `mcp.py`, `mcp_contracts.py` | MCP stdio server, tool manifests, JSON-RPC request handling, read-only cross-agent integration surface. |
| Export | `export_targets.py`, `exporter.py` | Single-session export, batch target preview/write, Markdown/Obsidian/Skill layouts, manifests. |
| Privacy | `privacy.py` | Sensitive content scanning, effective findings, redaction/fail decisions. |
| Backup/restore | `backup_manifest.py`, `backup_history.py`, `restore_plan.py`, `restore.py`, `restore_history.py` | Local backup verification, history, restore preflight, restore apply. |
| Audit | `audit.py` | Corpus audit reports, audit history, diff, prune. |
| Governance | `governance.py`, `shared_server.py` | Local governance status, preflight, policy readiness/runtime, audit records, optional read-only server surfaces. |
| Personal UI | `personal_ui.py` | Local HTTP server, static HTML/CSS/JS assets, route handling, action registry, Chinese localization. |
| Schemas | `schemas.py`, `docs/schemas/` | JSON contract registry and schema artifact generation. |

## Runtime Data Flow

```mermaid
flowchart TD
  CodexHome["CODEX_HOME / .codex"] --> TranscriptFiles["sessions + archived_sessions JSONL"]
  TranscriptFiles --> Parser["Parser / Importer"]
  Parser --> DB["SQLite Archive DB"]
  DB --> Store["ArchiveStore"]

  Store --> CLI["CLI Commands"]
  Store --> API["Local UI API"]
  Store --> Client["Client Interface"]
  Store --> MCP["MCP Stdio Server"]
  Store --> Retrieval["Retrieval / Agent Interface"]
  Store --> Export["Export Targets"]
  Store --> Ops["Backup / Restore / Audit"]
  Store --> Gov["Governance"]

  API --> Browser["Personal Web UI"]
  MCP --> Agents["Codex / ZCode / OpenCode"]
  Export --> Files["Export Directory"]
  Ops --> LocalArtifacts["Backups / History / Audit Files"]
```

## Archive Database vs Output Files

ThreadVault intentionally separates the searchable archive from generated artifacts.

| Thing | Default / Example | Owner | Meaning |
|---|---|---|---|
| Archive database | `<repo-root>\data\threadvault.db` by default in this checkout | `config.py`, `database.py`, `store.py` | The SQLite index/store for imported sessions; override with `--db`, `THREADVAULT_DB`, or `[storage].archive_db`. |
| Export directory | `<repo-root>\threadvault-ui-output` | `export_targets.py`, UI action params | Markdown/Obsidian/Skill files for human or Codex reuse. |
| Backup directory | User-provided or UI default | Backup modules | Copies of the archive database. |
| History/audit files | User-provided or default local paths | Audit/restore/governance modules | Local operational records. |

The database is useful because search/retrieval can query it. The export directory is useful because the user, Codex, Obsidian, or editors can read the generated files directly.

The archive database keeps raw event text and payloads, but the default FTS surface indexes `indexed_text`, a cleaned knowledge field derived from raw events. This preserves auditability while reducing low-value search noise such as empty events, token counts, screenshots/base64 blobs, and oversized tool outputs.

## Personal UI Architecture

The personal UI is a local browser app served by `personal_ui.py`.

```text
Browser
  -> GET / or /zh
  -> static HTML/CSS/JS embedded in personal_ui.py
  -> GET read routes for health, overview, session, warnings, retrieval
  -> POST /api/action for registered actions
  -> ArchiveStore and existing ThreadVault modules
```

Key UI rules:

- The server binds to `127.0.0.1` by default.
- Basic mode starts with three daily actions: search old records, open latest session, export for Codex reuse.
- Pro mode exposes the full workbench.
- Export write buttons stay locked until a matching preview exists.
- Running, completed, and failed states are rendered explicitly in the activity panel.
- The main UI translates and summarizes for humans; the JSON panel preserves raw payloads for debugging.

## API Route Families

| Route Family | Implementation | Purpose |
|---|---|---|
| `/`, `/zh`, static assets | `build_personal_ui_server` | Serve English or Chinese static UI. |
| `GET /api/health` | `build_health_payload` | Server status and important local paths. |
| `GET /api/client/overview` | `store.client_overview` | Session list and optional search overview. |
| `GET /api/client/session` | `store.client_session` | Session summary, previews, events, evidence. |
| `GET /api/client/warnings` | `store.client_warnings` | Parser warning and privacy scan context. |
| `GET /api/retrieve` | `store.agent_retrieve` | Agent-facing retrieval for UI search. |
| `POST /api/action` | `ACTION_REGISTRY`, `_execute_action` | Registered read/write actions with safety metadata. |

## MCP Interface Architecture

The MCP interface is a shallow transport adapter over existing deep modules. It owns protocol concerns only:

```text
MCP client
  -> stdio JSON-RPC initialize / tools/list / tools/call
  -> mcp.py dispatch
  -> ArchiveStore
  -> agent_interface / client_interface / diagnostics
  -> MCP content + structuredContent
```

First-version tools:

- `threadvault_capabilities`
- `threadvault_stats`
- `threadvault_doctor`
- `threadvault_retrieve`
- `threadvault_session`
- `threadvault_export_preview`

Design decisions:

- The MCP module does not parse transcript files.
- The MCP module does not access SQLite tables directly.
- Tool results preserve ThreadVault JSON contracts in `structuredContent`.
- Export preview remains read-only and does not write Markdown, Obsidian, or Skill files.
- Raw local paths remain hidden by default and require explicit `local_debug`.
- Future write tools must reuse preview, privacy, governance, and confirmation gates rather than introducing a separate write path.

## Action Safety Model

`ACTION_REGISTRY` classifies personal UI actions:

- `preview_required`: export writes need a matching accepted preview.
- `confirm_required`: dangerous writes need explicit confirmation.
- `dangerous_action`: UI should visually distinguish and gate the action.
- `dry_run_default`: actions default to read-only planning unless explicitly applied.

Backend checks remain the final gate. Frontend locks, progress hints, and confirmation prompts exist to make the workflow understandable, not to replace backend validation.

## Retrieval Architecture

ThreadVault retrieval has three related paths:

| Path | Module | Behavior |
|---|---|---|
| FTS retrieval | `retrieval.py` | Uses SQLite FTS5 over cleaned `events.indexed_text`. Default and always available after import. |
| Vector retrieval | `vector_adapter.py` | Optional config-gated local deterministic vectors over summary/evidence chunks. |
| Hybrid retrieval | `hybrid_retrieval.py` | Combines FTS and optional vector candidates with explanation fields. |

Agent-facing retrieval in `agent_interface.py` wraps these paths into stable machine-readable payloads and avoids raw local path exposure unless local debug behavior is requested.

## Export Architecture

Export has two levels:

- `exporter.py`: single-session/project Markdown-style export helpers.
- `export_targets.py`: target-oriented Markdown, Obsidian, and Skill preview/write flows with manifests.

The target-oriented flow is:

```text
selection + profile + privacy mode
  -> preview_export_target
  -> client_export_preview
  -> accepted matching preview
  -> export_target write
  -> threadvault-export-manifest.json
```

This flow prevents "click export and hope" behavior. Users see what will be written, where it will be written, and what privacy findings apply.

## Governance Architecture

Governance is optional and local-first by default. It provides:

- Status and readiness diagnostics.
- Permission and enforcement preflight.
- Identity actor binding from local static config.
- Central policy and backup policy readiness/runtime previews.
- Local and central audit store helpers.
- Business command instrumentation.
- Optional read-only shared server manifests and smoke checks.

Governance diagnostics do not make cloud sync mandatory and do not replace the personal local archive path.

## Schema Contracts

Public JSON payloads are registered in `schemas.py` and materialized under `docs/schemas/`.

Rules:

- Additive fields are preferred over breaking changes.
- Tests should validate important payloads against their packaged schemas.
- UI and agent code should consume stable contract fields instead of scraping human text.

## Documentation And Vocabulary

- `CONTEXT.md` defines canonical terms.
- `docs/KNOWLEDGE_GRAPH.md` maps entities, relationships, flows, and safety boundaries.
- `docs/API.md` documents local UI routes and action semantics.
- `docs/DATABASE.md` documents the SQLite storage model.
- `docs/progress/rounds/` records active work.
- `docs/progress/archive/legacy-v*` preserves historical version-phase evidence.

Do not recreate `docs/v0` through `docs/v4` or `docs/development-progress.md`; those were migrated into `docs/progress/archive/`.

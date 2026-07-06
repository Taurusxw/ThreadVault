# v4 Phase 01 Coverage Matrix: Personal UI Readiness

This matrix maps required Personal Web UI coverage to existing ThreadVault interfaces. Phase 01 records the target
coverage; later phases must implement it through the local UI server and action registry.

| UI capability | Existing interface to reuse | Future UI action family | Required safety/default |
|---|---|---|---|
| Initialize database | `threadvault init`; `ArchiveStore` database initialization | `database.init` | Local file only |
| Import Codex sessions | `threadvault import`; importer modules | `ingestion.import` | No parser rewrite |
| Ingestion queue enqueue/list/process | `threadvault ingest-queue enqueue/list/process` | `ingestion_queue.*` | Process apply is explicit |
| Session list | `threadvault list`; `ArchiveStore.list_sessions` | `sessions.list` | No raw paths unless local debug |
| Session detail | `threadvault client session` | `sessions.detail` | Raw transcript not included by default |
| Search | `threadvault search`; `threadvault retrieval query` | `search.query` | Use existing FTS/retrieval |
| Retrieval query | `threadvault retrieval query` | `retrieval.query` | Reuse v2 diagnostics |
| Hybrid retrieval | `threadvault retrieval hybrid` | `retrieval.hybrid` | Vector optional, FTS degradation |
| Agent retrieve | `threadvault agent retrieve` | `agent.retrieve` | Hide local metadata by default |
| Summary chunks | `threadvault summary-pipeline chunks` | `summary.chunks` | No embedding generation by default |
| Vector status/index/query | `threadvault vector status/index/query` | `vector.*` | Disabled by default unless config enables |
| Summarize | `threadvault summarize` | `summary.summarize` | Local rule summary only |
| Privacy scan | `threadvault privacy-scan` | `privacy.scan` | Must not be bypassed for export |
| Warnings | `threadvault warnings`; `threadvault client warnings` | `warnings.*` | Raw excerpts gated by local debug |
| Export session | `threadvault export`; `ArchiveStore.export_session` | `export.session` | Preview before execution |
| Export-target markdown | `threadvault export-target markdown` | `export_target.markdown` | Privacy mode honored |
| Export-target obsidian | `threadvault export-target obsidian` | `export_target.obsidian` | Privacy mode honored |
| Export-target skill | `threadvault export-target skill` | `export_target.skill` | Review candidate output |
| Client overview | `threadvault client overview` | `client.overview` | Local-first, no server required |
| Client session | `threadvault client session` | `client.session` | Governance preflight available |
| Client export preview | `threadvault client export-preview` | `client.export_preview` | Preview-only, no file writes |
| Client warnings | `threadvault client warnings` | `client.warnings` | Privacy summary visible |
| Config init/show/doctor | `threadvault config init/show/doctor` | `config.*` | Init must not overwrite unless explicit |
| Stats | `threadvault stats` | `maintenance.stats` | Read-only |
| Doctor | `threadvault doctor` | `maintenance.doctor` | Read-only |
| Self-test | `threadvault self-test` | `maintenance.self_test` | Read-only fixture smoke |
| Reindex | `threadvault reindex` | `maintenance.reindex` | Requires `confirm=true` |
| Vacuum | `threadvault vacuum` | `maintenance.vacuum` | Requires `confirm=true` |
| Backup | `threadvault backup`; backup history commands | `backup.create` | Show target path |
| Backup verify | `threadvault backup-verify`; `backup-history verify-latest` | `backup.verify` | Read-only verification |
| Backup history | `threadvault backup-history list/latest/prune` | `backup.history.*` | Prune dry-run by default |
| Restore plan | `threadvault restore-plan` | `restore.plan` | Preview-only |
| Restore apply | `threadvault restore` | `restore.apply` | Requires `confirm=true` |
| Restore history | `threadvault restore-history list/latest/prune` | `restore.history.*` | Prune dry-run by default |
| Audit corpus | `threadvault audit-corpus` | `audit.corpus` | Anonymous by default |
| Audit history | `threadvault audit-history list/latest/diff-latest/prune` | `audit.history.*` | Prune dry-run by default |
| Audit diff | `threadvault audit-diff` | `audit.diff` | Read-only |
| Schemas list/show/validate/write | `threadvault schemas list/show/write`; `validate-json` | `schemas.*` | `schema_write` requires `confirm=true` |
| Capabilities | `threadvault capabilities` | `discovery.capabilities` | Read-only |
| Robot docs guide | `threadvault robot-docs guide` | `discovery.robot_guide` | Read-only |
| Robot docs schemas | `threadvault robot-docs schemas` | `discovery.robot_schemas` | Read-only |
| v3 governance status | `threadvault governance status` | `governance.status` | Optional governance only |
| v3 governance gap audit | `threadvault governance v3 gap-audit` | `governance.v3_gap_audit` | Read-only |
| v3 acceptance smoke | `threadvault governance v3 acceptance-smoke` | `governance.v3_acceptance_smoke` | Local smoke, no cloud |
| Governance preflight | `threadvault governance preflight ...` | `governance.preflight.*` | Executes no business command |
| Governance instrumentation diagnostics | `threadvault governance instrumentation business-command` | `governance.instrumentation.business_command` | Preflight/audit evidence only |

## Phase Mapping

- Phase 02 should create `threadvault ui serve --host 127.0.0.1 --port 8766 --open` and serve a minimal static shell.
- Phase 03 should turn the static shell into the single-page personal workbench.
- Phase 04 should implement the action registry and cover this matrix end to end.
- Phase 05 should add `threadvault ui smoke --json` and validate server, actions, confirmations, v2/v3 non-regression,
  and local-first/privacy-first defaults.


# ThreadVault v0.30 Completion Gap Audit

## Summary

ThreadVault is substantially beyond the original CLI MVP. The current implementation provides local JSONL import, tolerant Codex parsing, SQLite/FTS5 indexing, listing/search/export/summarize, privacy scanning/redaction/fail modes, real-corpus anonymous audit, Codex state read-only enrichment, machine-friendly JSON contracts, local configuration, backup/restore safety workflows, retention maintenance, and packaged JSON schemas.

The remaining work is not a blocking CLI MVP gap. It is mostly product-direction work explicitly deferred by the original scope: Web/TUI, MCP server, vector database, cloud/team sync, and external LLM summarization.

## Evidence Snapshot

- CLI help exposes core and maintenance commands: `threadvault --help`.
- Capabilities command exposes 29 command families and 40 JSON outputs: `threadvault capabilities --json`.
- Packaged schema registry exposes 29 schemas: `threadvault schemas list --json`.
- Source/test/docs/schemas/plans/research files exist under the current workspace.
- Latest verified baseline before this audit: `py -3.12 -m pytest` -> `138 passed`; `py -3.12 -m ruff check .` -> passed.

## Original CLI MVP Requirements

| Requirement | Status | Evidence |
|---|---|---|
| Local-first, privacy-first CLI MVP | complete | README privacy section; local SQLite database; no network dependency in runtime commands. |
| Discover `~/.codex/sessions` and `~/.codex/archived_sessions` | complete | `import`, `doctor`, `ingest-sample`, and tests using `tests/fixtures/codex_home`. |
| Allow custom `--codex-home` | complete | `import`, `doctor`, `ingest-sample`, `audit-corpus` CLI options. |
| Streaming JSONL parsing | complete | Parser/importer modules and parser tests for current, legacy, malformed, and non-object records. |
| Support current Codex records | complete | Adapter tests for `session_meta`, `turn_context`, `event_msg`, `response_item`. |
| Support legacy rollout records | complete | Legacy parser fixture and tests. |
| Unknown/bad records do not abort import | complete | Parse warnings, malformed fixtures, importer tests. |
| SQLite schema with sessions/turns/events/import_logs/parse_warnings | complete | Database schema and doctor schema object checks. |
| FTS5 search index | complete | `events_fts`, FTS doctor check, `search` CLI/tests. |
| CLI commands `init/import/list/search/export/summarize` | complete | `threadvault --help`; integration tests. |
| Markdown export | complete | `export` command and export tests. |
| Basic rule summary with evidence IDs | complete | `summarize` command, summary tests, evidence fields. |
| Privacy scan warnings before export | complete | `privacy-scan`, export privacy modes, privacy tests. |
| First phase excludes Web/TUI/MCP/vector/cloud/external LLM | complete | README and capabilities mark external LLM/cloud as false; no UI/server layer added. |

## v0.2-v0.5 Hardening Requirements

| Area | Status | Evidence |
|---|---|---|
| `ArchiveStore` small interface | complete | `src/threadvault/store.py`. |
| Turn aggregation | complete | `turns` table, events `turn_id`, tests. |
| Machine-friendly `--json` | complete | `capabilities.json_outputs`, JSON-only tests. |
| `stats`, `doctor`, `warnings` | complete | CLI help, schemas, tests. |
| Search filters and field profiles | complete | `search --fields minimal|standard|full`, schema tests. |
| Export include/exclude, last-turns, profiles, formats | complete | README, export command, tests. |
| Read-only `state_5.sqlite` enrichment | complete | Doctor `codex_state`, importer enrichment tests. |
| `capabilities` and `robot-docs` | complete | CLI help, schema contract tests. |
| `reindex` and `vacuum` | complete | CLI help and tests. |
| Real-corpus dry-run audit | complete | `ingest-sample`, `audit-corpus`, anonymous audit tests. |
| Privacy severity and allowlist | complete | `privacy.py`, config tests, privacy scan tests. |
| Export `warn|redact|fail` privacy modes | complete | README, export tests. |
| Summary confidence/coverage fields | complete | summarizer tests and JSON output. |
| JSON schema registry and validation | complete | `schemas list/show/write`, `validate-json`, packaged schemas. |
| `self-test --json` | complete | CLI help and JSON command tests. |

## Maintenance And Recovery Features Added After MVP

| Feature | Status | Evidence |
|---|---|---|
| Local SQLite backup | complete | `backup`, schema, tests. |
| Backup verification and manifests | complete | `backup-verify`, `backup-manifest`, tests. |
| Backup history list/latest/verify/prune/config | complete | CLI groups and tests. |
| Restore plan preflight | complete | `restore-plan`, tests. |
| Safe restore with apply/overwrite gates | complete | `restore`, tests. |
| Restore history list/latest/prune/config | complete | CLI groups and tests. |
| Retention helper shared across audit/backup/restore | complete | `retention.py`, tests. |
| Retention and capabilities/doctor schema contracts | complete | v0.27-v0.29 tests and packaged schemas. |

## Documentation And Traceability

| Requirement | Status | Evidence |
|---|---|---|
| Per-phase plan Markdown | complete | `docs/v0/phases/phase-*/plan.md` through v0.30. |
| Per-phase external review Markdown | complete | Standardized external-review files under `docs/v0/phases/` through v0.30. |
| Development progress log | complete | `docs/development-progress.md`. |
| Research report appendices | complete | `docs/archive/mathforge-research-appendices.md` and `docs/v0/research/codex-session-archive-research.md`. |
| DOCX updated every phase | intentionally deferred | User previously accepted Markdown as source of truth; DOCX is not updated unless explicitly requested. |

## Known Deferred Scope

These are intentionally not implemented in the current CLI/data-layer completion line:

- Web UI.
- TUI.
- Desktop app.
- MCP server.
- REST API.
- Vector database or embedding index.
- Cloud sync.
- Team permissions.
- External LLM automatic summarization.
- Deep Obsidian integration.

## Remaining Candidate Follow-Ups

These are not blockers for CLI MVP completion, but are reasonable next phases if the project continues:

- Run a dedicated end-to-end smoke script that imports fixtures, searches, summarizes, exports all formats, validates schemas, backs up, restores, and self-tests in one command.
- Add final CLI MVP acceptance evidence once the user agrees the current CLI/data-layer line is ready to freeze.
- Optionally update the DOCX as a formal deliverable using the documents workflow.
- Add performance/memory instrumentation for very large synthetic JSONL files if real local histories grow beyond current fixtures.

## Audit Conclusion

The ThreadVault CLI/data-layer MVP and the subsequent agent-friendly maintenance hardening are effectively complete by current evidence. The project is ready for a final acceptance pass focused on end-to-end smoke validation and documentation freeze. The broader long-running goal should remain active until that acceptance pass is completed and the user agrees whether DOCX synchronization is required.


# Phase 03 / v0.3: Agent-Friendly Archive

## Goal

Make ThreadVault easier to maintain and easier for other agents or scripts to operate: preserve planning history, enrich sessions from Codex state when available, add stable machine-readable commands, and extend export formats without adding cloud or UI scope.

## Scope

- Keep the local-first SQLite/FTS5 architecture.
- Treat Codex JSONL transcripts and `state_5.sqlite` as unstable local facts behind adapters.
- Add documentation traceability for every phase.
- Borrow interface ideas from mature tools, but do not copy source code.

## Reference Projects Checked

- MeXenon/codex-session-export: project/session views, section filtering, Markdown export ergonomics.
- ezyyeah/codex-export: multi-format export patterns for Markdown, JSON, JSONL, and CSV.
- jinghan23/codex-export: Codex CLI plus Desktop coverage and session-id oriented workflows.
- ccusage Codex guide: explicit warning that Codex local usage parsing is experimental.
- CASS: robot-friendly `--json`, minimal fields, and health/guide commands.
- OpenAI Codex docs: local transcripts and hooks are useful inputs but not stable public APIs.

## Tasks

- Add read-only `state_5.sqlite` thread enrichment using `threads.rollout_path`.
- Add `capabilities`, `robot-docs guide`, and `robot-docs schemas`.
- Add `export --format md|json|jsonl|csv` and `--profile full|brief|agent|review`.
- Add `reindex --fts-only` and `vacuum`.
- Add v0.3 tests for state enrichment, export formats, robot docs, reindex, and documentation presence.
- Update README, development progress, research report Markdown, and external project review.

## Acceptance Commands

```powershell
py -3.12 -m pytest
threadvault --help
threadvault capabilities --json
threadvault robot-docs guide
threadvault reindex --fts-only --json
```

## Assumptions

- No Web UI, TUI, MCP server, vector database, cloud sync, team permissions, or external LLM summary in v0.3.
- Markdown files are the authoritative living documentation for this phase.
- The Word report is not updated unless a formal DOCX deliverable is requested.


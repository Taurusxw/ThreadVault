# ThreadVault v1: Personal Knowledge Layer

## Summary

`v1` turns ThreadVault from a manually invoked archive CLI into a personal Codex memory layer. The goal is automatic local accumulation plus durable knowledge outputs: Markdown vaults, Obsidian-ready files, project archives, and Codex Skill material.

The center of gravity is `automatic ingest + knowledge export`, not model-heavy summarization or UI work.

## Key Outcomes

- Codex activity can trigger ThreadVault safely through lightweight Hooks.
- Imports can run incrementally without requiring the user to remember manual scans.
- Project and session archives can be exported in batch.
- Obsidian/Markdown vault output is stable enough for daily use.
- Codex Skill output can package selected summaries and references.
- Evidence links remain visible from summaries back to ThreadVault event IDs.

## Architecture Changes

### Ingestion Automation Module

Create an `Ingestion Automation` module with a small interface around:

- Hook event capture.
- Codex home scan requests.
- Queue or pending-work records.
- Processing status and diagnostics.
- Import execution through the existing parser/importer/database path.

Codex Hooks must stay lightweight. A Hook should enqueue or narrowly signal work; it should not perform large transcript scans, full database maintenance, backup/restore, or privacy-heavy processing inside the Hook process.

### Export Target Module

Create an `Export Target` module with a small interface around:

- Archive selection: session, project, time range, or tagged set.
- Target profile: Markdown, Obsidian, Codex Skill, or later HTML.
- Export manifest: written files, skipped items, privacy findings, and evidence links.
- Shared privacy and path policy for all export targets.

This prevents Obsidian and Skill behavior from becoming more `if/elif` branches inside the current exporter.

### Summary Pipeline Preparation

Keep the default v1 summary path local and deterministic. Deepen summary structure enough to support evidence-backed vault exports, but do not make external LLM calls the default.

## Out Of Scope For v1

- Vector search and embedding indexes.
- Desktop app, Web UI, TUI, VS Code/Cursor extension.
- Server mode, REST API, team permissions, and cloud sync.
- Default external LLM automatic summaries.
- Mandatory background daemon installation.

## Suggested Milestones

1. `v1.0`: Ingestion Automation module and Hook-safe queue/process command.
2. `v1.1`: Batch project/session export with export manifests.
3. `v1.2`: Obsidian/Markdown vault target with stable file layout and evidence links.
4. `v1.3`: Codex Skill target that emits `SKILL.md` plus references from selected archive material.
5. `v1.4`: v1 acceptance smoke over fixture data and one anonymized local audit workflow.

## Acceptance Criteria

- A local Hook trigger can record or enqueue import work without exposing raw transcript content in logs.
- A user can run one ThreadVault command to process queued work and update the archive.
- A user can export a project into a Markdown/Obsidian-ready folder with stable links and privacy findings.
- A user can generate Codex Skill material from selected summaries without copying unrelated raw sessions.
- Existing `v0.31.0` CLI commands and JSON contracts remain compatible.


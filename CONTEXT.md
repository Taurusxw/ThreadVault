# ThreadVault Context

ThreadVault is a local-first, privacy-first archive and retrieval tool for local Codex sessions. This glossary defines the domain language used by docs, code, tests, and UI labels.

## Language

**Archive Database**:
The local SQLite database that stores imported Codex sessions, normalized events, warnings, search indexes, ingestion requests, and optional vector chunks.
_Avoid_: export database, cache, project output folder

**Archive**:
The local durable collection of imported Codex session data inside the archive database.
_Avoid_: export, backup, vault

**Codex Transcript File**:
A local JSONL file produced by Codex under `sessions` or `archived_sessions`.
_Avoid_: chat file, raw log, exported session

**Session**:
The primary archived unit representing one Codex conversation.
_Avoid_: thread when referring to stored ThreadVault data

**Turn**:
A conversation grouping of related user, assistant, and tool events inside a session.
_Avoid_: message group, step

**Event**:
A normalized record from a transcript, such as a message, tool call, system item, or related structured entry.
_Avoid_: line, row, message when the normalized record is meant

**Evidence Event**:
An event ID cited by a summary, retrieval result, chunk, or export as supporting evidence.
_Avoid_: citation without event reference

**Summary**:
A local, evidence-backed condensation of a session or project context.
_Avoid_: model answer, generated article

**Summary Chunk**:
A stable derived chunk selected from session summaries, turn summaries, or high-value evidence events for retrieval or vector indexing.
_Avoid_: raw embedding input

**Retrieval**:
The stable search interface over archived material, using FTS by default and optional vector or hybrid paths when configured.
_Avoid_: search when discussing the full interface contract

**Export Preview**:
A read-only plan describing which files an export would write and what privacy findings apply.
_Avoid_: export, dry export file

**Export Target**:
A concrete output profile such as Markdown, Obsidian, or Codex Skill.
_Avoid_: format when the target also controls folder layout and manifest behavior

**Export Directory**:
The local folder where user-facing Markdown, Obsidian, Skill, or other generated files are written.
_Avoid_: archive database, index database

**Privacy Finding**:
A structured sensitive-content finding that can warn, redact, or block export depending on privacy mode.
_Avoid_: parser warning

**Governance Preflight**:
A local readiness or policy check that reports whether an operation is safe or properly instrumented before execution.
_Avoid_: permission grant, enforcement by default

**Audit Record**:
A structured local record of a governance-sensitive operation.
_Avoid_: import log, parse warning

**Backup**:
A local copy of the archive database for recovery.
_Avoid_: export, vault, report

**Restore Plan**:
A reviewable dry-run description of restoring a backup to a target database.
_Avoid_: restore

**Personal UI**:
The local browser UI served by ThreadVault for browsing, searching, exporting, maintaining, and governing the archive.
_Avoid_: cloud UI, hosted dashboard

**Basic Mode**:
The Personal UI mode for common daily actions: search old records, open recent sessions, and export material for Codex reuse.
_Avoid_: limited product

**Pro Mode**:
The Personal UI mode exposing the broader workbench of archive, retrieval, export, maintenance, schema, and governance tools.
_Avoid_: admin-only mode

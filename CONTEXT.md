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

**Desktop Export Plan**:
An immutable desktop preview state that binds one session, output directory, export profile, and privacy mode. Any parameter change invalidates it before a confirmed write.
_Avoid_: cached command, implicit export permission

**Export Target**:
A concrete output profile such as Markdown, Obsidian, or Codex Skill.
_Avoid_: format when the target also controls folder layout and manifest behavior

**Export Directory**:
The local folder where user-facing Markdown, Obsidian, Skill, or other generated files are written.
_Avoid_: archive database, index database

**Privacy Finding**:
A structured sensitive-content finding that can warn, redact, or block export depending on privacy mode.
_Avoid_: parser warning

**Personal Safety Gate**:
A local privacy scan, read-only preview, explicit confirmation, or verification step that protects a personal operation before it writes or exposes data.
_Avoid_: team permission, governance preflight, central policy

**Backup**:
A local copy of the archive database for recovery.
_Avoid_: export, vault, report

**Backup Center**:
The native desktop view over the existing smart-backup policy. It presents status, schedule, disk guard, selected tier, and one-click execution without owning backup policy.
_Avoid_: backup engine, scheduler service

**Restore Plan**:
A reviewable dry-run description of restoring a backup to a target database.
_Avoid_: restore

**Native Desktop App**:
The local Tkinter application for browsing, searching, previewing exports, and running personal safety or maintenance actions.
_Avoid_: Personal UI, browser UI, hosted dashboard

**MCP Read-Only Interface**:
The local stdio interface through which an agent can inspect capabilities, diagnostics, retrieval results, sessions, and export previews without writing files or initializing a missing database.
_Avoid_: shared server, remote API, team service

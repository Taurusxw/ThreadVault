# 2026-07-13 Round 002: automatic ingestion and Codex integration

## Status

completed

## Goal

Connect daily Codex conversations to the local ThreadVault archive automatically, register the read-only MCP server in Codex, and remove current Codex event compatibility warnings without adding low-value metadata to normal search.

## Background

The queue, hook adapter, and MCP server existed, but none was installed in the active Codex configuration. The real archive therefore stopped updating unless `threadvault import` was run manually. A 316-file corpus audit also found unsupported `world_state` and `inter_agent_communication_metadata` records plus repeated collaborative `session_meta` warnings.

## Scope

- Add targeted single-transcript imports for Codex `Stop` hooks.
- Keep ingestion queue state as durable operational history.
- Add a dry-run-first user hook installer that preserves unrelated hooks.
- Recognize current world/inter-agent metadata without indexing it as user knowledge.
- Add schema v7 cleanup for stale unknown/duplicate warning taxonomy in existing archives.
- Register ThreadVault MCP through the supported Codex CLI.
- Backfill and verify the real local archive.
- Update the affected user, API, architecture, database, MCP, progress, and usage documents.

## Implementation Steps

1. Verify current Codex hook and MCP behavior against the installed CLI and official OpenAI documentation.
2. Refactor import processing so a hook can import one `transcript_path` instead of scanning the entire Codex home.
3. Extend queue processing and hook diagnostics for applied single-file imports.
4. Add idempotent `codex-hook install` dry-run/apply behavior.
5. Update parser compatibility and tests.
6. Install the user-level hook and MCP registration, back up the database, then backfill all transcripts.
7. Run focused/full validation plus live retrieval checks.

## Key Decisions

- Use `~/.codex/hooks.json`, a supported user-level hook source, so ThreadVault does not replace the existing Codex `notify` command.
- Keep Codex's one-time `/hooks` trust review; do not bypass the official safety mechanism.
- Import only the hook-provided transcript during `Stop`; use full-home import only for first-time backfill and recovery.
- Preserve `world_state` and inter-agent metadata as raw events with empty searchable text.
- Treat repeated session metadata as valid parent/subagent provenance, while retaining genuine missing function-output warnings.
- Use `session_meta.id` as the transcript identity when collaborative records also carry a parent `session_id`; reprocess unchanged files whenever `parse_version` is stale.
- Keep MCP read-only and separate from ingestion.

## Change List

- Added single-transcript imports and durable queue processing for Codex `Stop` events.
- Added an idempotent, dry-run-first user hook installer and installed the applied hook in the active Codex user configuration.
- Added native handling for `world_state` and `inter_agent_communication_metadata`, removed false duplicate-session warnings, and corrected collaborative child-session identity handling.
- Added schema v7 warning-taxonomy repair and parse-version-aware reimport behavior.
- Registered the read-only ThreadVault MCP server in the active Codex configuration.
- Updated package metadata to `2.1.0`, regenerated schemas, backed up the live database, and performed a full archive rebuild.

## Tests And Verification

- Focused parser/queue/hook suite: `30 passed`.
- Full suite: `280 passed in 33.97s`.
- Ruff and `pip check`: passed.
- Final rebuild snapshot: 320 transcripts discovered and imported, 790,799 events processed, zero failures, seven genuine `missing_function_call_output` warnings, and zero unknown-event warnings.
- Live database inspection after rebuild: 322 sessions, 806,237 events, matching FTS rows, and only seven missing-output warnings; two older sessions whose source JSONL files no longer exist were intentionally preserved.
- Final incremental catch-up scanned 326 current transcripts, imported the nine new or changed files with zero failures, and left a healthy schema-v7 database with 328 sessions, 808,698 events, matching FTS rows, and eight missing-output warnings.
- Applied-hook smoke: queue request 1 completed one targeted transcript import with 1,691 events and zero failures.
- `codex mcp list` and `codex mcp get threadvault` show the stdio server enabled; the six-tool manifest, a three-result agent retrieval, and the native desktop smoke all passed.
- Created and verified a pre-migration backup under `.tmp/pre-v2.1.0-backup/` before rebuilding the live database.

## Documentation Updates

- Updated README, API, architecture, database, MCP integration, usage manual, development, changelog, progress, TODO, knowledge graph, and project AGENTS guidance.
- This round is the new independent same-day L3 trace; Round 001 remains the completed personal-only modularization record.

## Risks And Follow-Up

- Codex will skip a new non-managed hook until the user reviews and trusts it once through `/hooks`.
- Active Codex work keeps creating or extending JSONL files, so point-in-time corpus counts can move until the hook has been trusted; the installed hook handles subsequent `Stop` events.
- Two preserved historical database sessions have no remaining source JSONL and therefore cannot be reparsed without an external copy.
- The eight incomplete function-call pairs in the latest moving snapshot appear to be genuinely interrupted calls and remain warnings rather than being silently normalized away.

## Next Step

The user should review and trust the installed command once through `/hooks`, then start a new Codex task so the newly registered ThreadVault MCP tools are loaded into that task.

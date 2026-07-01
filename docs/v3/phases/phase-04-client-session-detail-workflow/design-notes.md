# v3 Phase 04 Design Notes: Client Session Detail Workflow

## Summary

`client session` is the detail companion to `client overview`. It gives richer clients enough structured information to
show a session detail screen without re-parsing Codex JSONL files.

## Module Boundary

The implementation keeps ownership clear:

- database/session lookup remains in the existing database layer.
- local summary generation remains in the existing summary module.
- client payload shaping lives in `threadvault.client_interface`.
- export remains an action hint pointing to existing export/export-target commands.

## Event Preview Policy

The payload returns event previews, not full transcript records. `--event-limit` bounds the number of events and
`--max-chars` bounds each preview string. This is enough for client scanning while avoiding a disguised raw transcript
export.

## Local Debug Policy

Default detail output hides raw local paths and event file paths. `--local-debug` is explicit and mirrors the v2
agent-facing retrieval behavior.

## Deferred Decisions

- Whether to add a dedicated export preview payload before file-writing export commands.
- Whether session detail should include warning snippets or a separate warning detail workflow.
- How optional server deployments should audit session detail reads.


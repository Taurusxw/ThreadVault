# v4 Phase 04 Design Notes: UI Action Coverage

## Summary

Phase 04 turns `/api/action` from a placeholder into the Personal UI action registry. The registry lives in
`threadvault.personal_ui` and is intentionally the only write-action HTTP entrypoint.

## Registry Interface

Each action has a `PersonalUIActionSpec` with:

- action name
- user-facing label
- dangerous-action marker
- `confirm=true` requirement
- preview requirement
- dry-run default
- implementation status

`POST /api/action` accepts:

```json
{
  "action": "stats",
  "params": {},
  "confirm": false
}
```

and returns the existing `personal_ui_action` contract with normalized `result`, `safety`, `status`, and
`available_actions` fields.

## Safety Rules

The registry enforces Phase 04 safety centrally:

- `restore_apply` requires `confirm=true`
- `vacuum` requires `confirm=true`
- `reindex` requires `confirm=true`
- `schema_write` and `schemas_write` require `confirm=true`
- export write actions require `preview_accepted=true`
- prune/history apply flows default to dry-run; `apply=true` requires `confirm=true`
- backup can run without confirmation but returns the target path

## Reused Interfaces

The registry calls existing `ArchiveStore` methods or the same helper modules used by the CLI:

- ingestion queue, import, sessions, retrieval, hybrid retrieval, agent retrieval
- summary chunks, vector status/index/query
- privacy scan and warnings
- export preview and export target
- config, schemas, validation, capabilities, robot docs
- stats, doctor, self-test, reindex, vacuum
- backup, restore plan/apply/history, audit corpus/history/diff
- governance status, v3 gap audit, v3 acceptance smoke, preflight, and instrumentation diagnostics

It does not introduce a second parser, retrieval engine, privacy scanner, exporter, backup layer, or governance runtime.

## Deferred Or Constrained Behavior

Phase 04 does not add `threadvault ui smoke --json`; that remains Phase 05. The UI action registry is implemented and
discoverable, while final end-to-end acceptance smoke is deferred to the next phase.

External model calls, cloud sync, team enforcement, account login, and public server defaults remain outside personal UI
defaults.

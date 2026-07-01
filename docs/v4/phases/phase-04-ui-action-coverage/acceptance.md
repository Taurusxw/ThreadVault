# v4 Phase 04 Acceptance: UI Action Coverage

## Status

Accepted on 2026-07-01.

## Scope

Phase 04 accepts the unified Personal UI action registry behind `POST /api/action`.

The accepted registry covers the Phase 01 capability matrix with direct implementations or existing safe preview/dry-run
paths:

- database initialization and import
- ingestion queue enqueue/list/process
- session list/detail, search, retrieval, hybrid retrieval, agent retrieval
- summary chunks, summarize, vector status/index/query
- privacy scan and warnings
- export preview, session export, and export target markdown/obsidian/skill
- config init/show/doctor
- stats, doctor, self-test, reindex, vacuum
- backup, backup verify/history/prune
- restore plan/apply/history/prune
- audit corpus/history/diff/prune
- schemas list/show/validate/write
- capabilities and robot docs
- governance status, v3 gap audit, v3 acceptance smoke, preflight, instrumentation, and external-model diagnostics

## Acceptance Evidence

- Unknown actions return structured `personal_ui_action` JSON.
- Dangerous actions are blocked without `confirm=true`.
- Export write actions are blocked without accepted preview evidence.
- Prune apply flows are blocked without confirmation and dry-run by default.
- Backup action returns the target path.
- Representative read and write-safe actions execute through existing `ArchiveStore` or CLI helper modules.
- Capabilities and robot docs advertise the implemented personal UI action registry.
- The web UI sends useful params and confirmation flags to `/api/action`.
- No React, Vite, Node, cloud sync, login, public server default, team enforcement, external model calls, parser rewrite,
  SQLite retrieval rewrite, or privacy bypass was added.

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v404_ui_action_coverage.py -q
py -3.12 -m ruff check src\threadvault\personal_ui.py src\threadvault\store.py src\threadvault\schemas.py tests\test_v404_ui_action_coverage.py
```

Round validation:

```powershell
threadvault capabilities --json
threadvault robot-docs guide --json
threadvault robot-docs schemas --json
Test-Path deep-research-report.md
py -3.12 -m ruff check .
py -3.12 -m pytest
```

`threadvault ui smoke --json` remains a Phase 05 deliverable.

# v4 Phase 01 Acceptance: Personal UI Readiness

## Status

Accepted on 2026-07-01.

## Scope

Phase 01 establishes the v4 Personal Web UI planning base:

- v4 documentation entrypoint
- personal UI product boundary
- local-first/privacy-first safety boundary
- required UI capability coverage matrix
- focused documentation regression test

## Acceptance Evidence

The accepted Phase 01 baseline records that future v4 UI work must:

- run as a local personal localhost console
- default to `127.0.0.1`
- reuse `ArchiveStore` and accepted v1/v2/v3 interfaces
- avoid parser, SQLite retrieval, vector, summary, export, privacy, backup, restore, and governance rewrites
- preview export flows before execution
- require explicit confirmation for restore apply, vacuum, reindex, schema write, and prune/delete apply flows
- keep external model calls, cloud sync, team collaboration, account login, and public server behavior out of default
  personal UI scope

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v401_personal_ui_readiness.py -q
py -3.12 -m ruff check tests\test_v401_personal_ui_readiness.py
threadvault capabilities --json
Test-Path deep-research-report.md
```

Final results are recorded in `docs/development-progress.md`.

## Final Result

ThreadVault v4 now has a traceable documentation entrypoint and Phase 01 readiness baseline. The next implementation
round can build the local UI server without reopening the product boundary or re-auditing the complete capability list.

## Non-Claims Preserved

- No v4 HTTP server has been implemented in this phase.
- No Web UI action registry has been implemented in this phase.
- No new public CLI command has been added in this phase.
- No cloud, team, login, public server, external model, React, Vite, or Node behavior has been added.


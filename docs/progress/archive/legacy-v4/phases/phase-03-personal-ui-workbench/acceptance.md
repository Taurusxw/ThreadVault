# v4 Phase 03 Acceptance: Personal UI Workbench

## Status

Accepted on 2026-07-01.

## Scope

Phase 03 accepts the native static Personal UI workbench served by `threadvault ui serve`.

The accepted workbench includes:

- left navigation
- top search/status bar with database path
- main work area
- right JSON output panel
- Archive, Search, Session, Export, Privacy, Maintenance, Backup/Restore, Config, Schemas, and Governance views
- table/form/detail surfaces for read workflows
- explicit Phase 04 placeholders for dangerous or write-heavy actions

## Acceptance Evidence

The workbench preserves v4 boundaries:

- Python stdlib HTTP server plus static HTML/CSS/JS only
- no React, Vite, Node, or frontend build step
- no cloud sync, login, public server default, team enforcement, or external model calls
- existing `ArchiveStore` client/retrieval/warning routes remain the backend path
- raw JSON responses are always inspectable in the right panel

Safety boundaries are visible in the UI:

- export actions say preview is required before writing
- restore apply says `confirm=true` is required
- reindex says `confirm=true` is required
- vacuum says `confirm=true` is required
- schema write says `confirm=true` is required
- backup says the target path must be displayed

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v403_personal_ui_workbench.py -q
py -3.12 -m ruff check src\threadvault\personal_ui.py tests\test_v403_personal_ui_workbench.py
```

Broader sanity validation:

```powershell
threadvault ui serve --help
threadvault capabilities --json
Test-Path deep-research-report.md
```

Final full validation for this round:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

`threadvault ui smoke --json` remains a Phase 05 deliverable and is not claimed by Phase 03.

## Follow-Up

Phase 04 should replace placeholder write controls with a unified action registry that calls existing ThreadVault
interfaces and enforces confirmation, preview, and dry-run safety rules centrally.

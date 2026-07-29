# 2026-07-28 Round 001: Native desktop workbench

## Status

Implementation, automated validation, and target-Windows rendered review completed.

## Goal

Turn the primary Tkinter console into a calm, practical workbench while preserving ThreadVault's local-first privacy and safety gates.

## Background

The v2.4.0 desktop flow was functional but still used default-heavy native styling, rebuilt both session tables on every refresh, reread Codex state metadata for every snapshot, and rewrote current schema metadata through normal desktop snapshot initialization.

## Scope

- Centralize the native Tk visual system and style popup menus, confirmation dialogs, text surfaces, scrollbars, and control states.
- Make archive/search/open/export/backup hierarchy obvious without adding a frontend dependency or changing safety contracts.
- Preserve table selection, focus, and scroll while avoiding unchanged row mutations.
- Keep test and smoke verification away from the user's ignored archive, Codex home, and restore-history runtime files.

## Implementation Steps

1. Extract semantic palette/theme and themed confirmation/menu helpers to `desktop_theme.py`.
2. Add header/action hierarchy, a secondary-actions menu, scoped primary actions, and consistent busy/disabled handling.
3. Reconcile Treeview rows in place and retain the selected session during refresh.
4. Cache only local Codex title metadata behind state SQLite/WAL/SHM signatures.
5. Avoid current-schema metadata rewrites and add tests-wide temporary runtime isolation.

## Key Decisions

- Archive data is still fetched fresh for every snapshot; only local friendly-title metadata is reused with explicit file-signature invalidation.
- The workbench retains native file pickers but styles the application-owned popup and confirmation surfaces; platform-owned picker visuals are not overridden.
- `init_db()` now inserts a missing schema metadata row or updates a stale one, but does not rewrite an already-current value.
- The test fixture redirects default archive DB, Codex home, config, and restore history to `tmp_path`; production defaults are unchanged.
- `desktop_app.py` remained the cohesive controller. The newly independent theme concern moved to `desktop_theme.py`; no broader UI code deletion was justified by repository-wide reference evidence.
- The active package changes from `2.4.0` to `2.4.1` as a patch-level user-visible optimization without a public data or JSON-contract change.

## Change List

- Added `src/threadvault/desktop_theme.py` and centralized semantic tokens plus ttk/Tk state treatment.
- Updated `src/threadvault/desktop_app.py` for workbench hierarchy, themed dialogs/menu, stable controls, and in-place table reconciliation.
- Updated `src/threadvault/desktop_data.py` with state SQLite/WAL/SHM signature invalidation for friendly-title metadata.
- Updated `src/threadvault/database.py` so a current schema version does not rewrite `meta` during ordinary initialization.
- Updated `src/threadvault/database.py` to explicitly close backup SQLite connections before retention can delete superseded backup files on Windows.
- Added `tests/test_v408_desktop_workbench.py` and a global `tests/conftest.py` temporary-runtime fixture; updated restore-facing tests to prove isolation.
- Updated package/version, README, architecture, development, changelog, progress, and index records.

## Tests And Verification

- `python -m pytest tests/test_v22_restore.py tests/test_v407_desktop_app.py tests/test_v408_desktop_workbench.py -q` — 27 passed after full runtime isolation; real ignored archive and restore-history metadata unchanged.
- `python -m ruff check src/threadvault/database.py src/threadvault/desktop_app.py src/threadvault/desktop_theme.py src/threadvault/desktop_data.py tests/conftest.py tests/test_v22_restore.py tests/test_v407_desktop_app.py tests/test_v408_desktop_workbench.py` — passed.
- A focused schema-init test confirms a current schema adds zero SQLite `total_changes` while a stale metadata value is repaired with one update.
- Noninteractive Tk style/reconciliation query — passed; a synthetic 1,000-row first render took 3.7 ms and an unchanged refresh 1.8 ms with zero row mutations and preserved selection/focus/scroll.
- `python -m pytest -q` — 300 passed in isolated mode; real ignored archive and restore-history size/mtime unchanged.
- `python -m compileall -q src tests`, `python -m ruff check src tests`, and `python -m pip check` — passed.
- `threadvault desktop smoke --db <temporary-db> --json` — passed.
- Final noninteractive Tk query — first 5.7 ms, unchanged 2.3 ms for 1,000 rows; no row mutations and state persisted.
- Parent follow-up `python -m pytest tests/test_v408_desktop_workbench.py -q` — 6 passed after adding runtime assertions for entry, combobox, menu-button, scrollbar, and label-frame states; targeted ruff and `compileall` passed and live runtime metadata remained unchanged.
- Target-Windows rendered QA — passed at the effective 880×560 minimum-size layout. The main workbench, keyboard focus, disabled states, horizontal/vertical scrollbars, production secondary-actions menu, and themed manual-backup confirmation dialog rendered without clipping, overlap, or native gray leakage. Menu/dialog surfaces were auto-presented against an isolated runtime; no confirmation action was executed.
- The ignored live archive remained 1,242,583,040 bytes with mtime `2026-07-28T05:14:32.7552254Z`, and restore history remained 160,018 bytes with mtime `2026-07-28T05:11:18.8967540Z`, before and after rendered QA.

## Documentation Updates

Updated README (English and Chinese), architecture, development QA guidance, changelog, progress, DOC_INDEX, and this round. No new domain term or public API contract was introduced.

## Risks And Follow-Up

- Platform-owned file pickers retain the operating system theme.
- Before test isolation was added, two verification runs appended ignored restore-history from 156,048 bytes to 160,018 bytes; a bare desktop smoke then initialized the ignored real archive at 1,242,583,040 bytes. Neither file was read, reverted, rewritten, or pruned because individual user/runtime records cannot be safely removed automatically. A current-schema metadata guard, explicit backup connection closure, and suite-wide temporary runtime fixture were then added; the final isolated full suite and temporary smoke left both live files' size and mtime unchanged.

## Next Step

No further UI work is required for this round. Restart long-running Codex MCP processes when adopting the 2.4.1 runtime.

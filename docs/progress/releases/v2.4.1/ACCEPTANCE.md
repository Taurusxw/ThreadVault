# ThreadVault v2.4.1 Release Acceptance

## Scope

This release accepts source freshness/catch-up, catch-up-first smart backup, combined Codex Hook/MCP setup, the polished native desktop workbench, generated contracts, CI, and bilingual documentation.

Excluded from the release are local transcripts, databases, cold blobs, backups, exports, screenshots, environment files, and the unrelated ignored `tmp-pdf-check/` workspace directory.

## Acceptance Gates

- Source and installed metadata report `2.4.1`.
- Full branch-coverage pytest passes at or above 70%.
- Full source/test ruff, `compileall`, and `pip check` pass.
- Generated schemas include and validate source-sync, smart-backup.v2, and Codex integration contracts.
- Isolated desktop smoke and rendered Windows workflow QA pass.
- MCP manifest exposes six read-only tools; local Codex configuration contains the exact enabled ThreadVault entry.
- Live source catch-up completes without failed files, records genuine parser warnings, and leaves deep cold verification and FTS equality passing.
- Public-release hygiene finds no release-blocking tracked secrets, private runtime artifacts, or oversized release files.

## Validation Commands

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=threadvault --cov-report=term-missing
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\threadvault.exe schemas write --out docs\schemas --json
.\.venv\Scripts\threadvault.exe desktop smoke --db <temporary-db> --json
.\.venv\Scripts\threadvault.exe mcp manifest --json
.\.venv\Scripts\threadvault.exe storage sync --db data\threadvault.db --json
.\.venv\Scripts\threadvault.exe storage verify --db data\threadvault.db --deep --json
git diff --check
```

## Results

- Full automated suite: `311 passed, 1 skipped` in 131.08 seconds; total branch coverage `74.88%` (70% required).
- Ruff, `compileall`, dependency check, isolated desktop smoke, generated Schema registry, capabilities, and six-tool read-only MCP manifest: passed.
- Live catch-up: 62 + 2 + 1 + 4 targeted files imported during concurrent Codex activity; 134,250 events processed in total with no failed files. The final four-file pass surfaced one genuine incomplete function-call warning.
- Verified Evidence backup: 1.390 GB database; SHA and SQLite integrity valid; 98,699 cold blobs / 3.679 GB with zero missing or invalid references.
- Live archive after final catch-up: 404 sessions, 939,614 events, 3,904 turns, seven `missing_function_call_output` warnings, and FTS 939,614/939,614.
- Live cold verification after final catch-up: 98,913 blobs / 3.681 GB stored, with zero missing or invalid references.
- Rendered Windows QA: passed after reproducing and fixing the initial empty-window regression; session, Backup Center, Codex Integration, focus, scrolling, disabled states, and confirmed actions were inspected against the real local archive.
- Codex integration: exact Stop hook configuration present; exact read-only MCP registration enabled. Codex restart and `/hooks` review remain client-owned completion steps.

## Residual Risks

- An active transcript can become pending after the final check and before its Stop hook fires; this is expected and is caught by Hook or the next backup.
- Hook trust is intentionally not inferred from configuration because Codex owns the exact-command review state.
- Full NVDA narration and official MCP Inspector smoke remain low-priority follow-ups.

## Status

completed

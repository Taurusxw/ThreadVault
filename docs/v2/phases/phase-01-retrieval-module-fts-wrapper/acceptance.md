# Phase 01 Acceptance: Retrieval Module FTS Wrapper

## Scope

This acceptance covers the first v2 retrieval foundation. It verifies that ThreadVault has a `Retrieval` module wrapping the existing SQLite FTS5 search path while preserving current `threadvault search` behavior and JSON contracts.

## Evidence

- `threadvault.retrieval` exposes `RetrievalQuery` and `retrieve`.
- `ArchiveStore.search()` routes through the retrieval module.
- The retrieval module supports `mode="fts"`.
- Unsupported retrieval modes are rejected.
- CLI `search` output remains valid against `search_minimal`, `search_standard`, and `search_full`.
- Existing session, project, event type, and tool filters still work.
- Awkward FTS input still uses a safe quoted retry path.
- `capabilities --json` advertises `retrieval_module` and `retrieval_modes: ["fts"]`.

## Validation Commands

```powershell
py -3.12 -m pytest tests\test_v201_retrieval_module.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault search pytest --json --fields minimal
threadvault capabilities --json
threadvault schemas list --json
Test-Path deep-research-report.md
```

## Result

Accepted.

Final validation completed on 2026-07-01:

- `threadvault schemas write --out docs\schemas --json` -> passed.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 184 passed.
- `threadvault search pytest --json --fields minimal` -> passed and emitted a JSON array.
- `threadvault capabilities --json` -> passed and advertised `retrieval_module` plus `retrieval_modes: ["fts"]`.
- `threadvault schemas list --json` -> passed.
- `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable metadata for `threadvault==0.31.0`.
- `Test-Path deep-research-report.md` -> `False`.
- `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`.

This phase establishes the v2 retrieval module boundary without changing the existing CLI search contract, JSON schemas, package version, or database schema.

# Phase 02 Acceptance: Retrieval JSON Contracts And Diagnostics

## Scope

This acceptance covers v2.1 retrieval contracts and diagnostics. It verifies that ThreadVault exposes a v2 object-shaped retrieval JSON contract while preserving the legacy `threadvault search --json` array contracts.

## Evidence

- `threadvault.retrieval` now exposes:
  - `RETRIEVAL_CONTRACT_VERSION`
  - `RetrievalDiagnostics`
  - `RetrievalResponse`
  - `retrieve_response`
  - `build_retrieval_diagnostics`
  - `fts_index_status`
- `retrieve(conn, query)` still returns `list[SearchResult]` for compatibility.
- `ArchiveStore.retrieve(...)` returns the v2 retrieval object payload.
- `ArchiveStore.retrieval_diagnostics()` returns diagnostics without requiring a query.
- `threadvault retrieval query QUERY --json` emits:
  - `contract_version`
  - `query`
  - `diagnostics`
  - `results`
- `threadvault retrieval diagnose --json` emits:
  - `contract_version`
  - `diagnostics`
- `threadvault search QUERY --json --fields minimal|standard|full` remains an array contract.
- `capabilities --json` advertises:
  - command: `retrieval`
  - JSON outputs: `retrieval query`, `retrieval diagnose`
  - feature flag: `retrieval_diagnostics: true`
- `robot-docs guide --json` advertises retrieval contract metadata.
- `schemas list --json` includes:
  - `retrieval_query`
  - `retrieval_diagnostics`
- Generated schema artifacts exist:
  - `docs/schemas/retrieval_query.schema.json`
  - `docs/schemas/retrieval_diagnostics.schema.json`

## Validation Commands

```powershell
py -3.12 -m pytest tests\test_v202_retrieval_contracts_diagnostics.py
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault retrieval query pytest --json
threadvault retrieval diagnose --json
threadvault search pytest --json --fields minimal
threadvault capabilities --json
threadvault schemas list --json
threadvault retrieval --help
threadvault retrieval query --help
threadvault retrieval diagnose --help
py -3.12 -m pip install -e ".[dev]"
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

## Result

Accepted.

Final validation completed on 2026-07-01:

- `py -3.12 -m pytest tests\test_v202_retrieval_contracts_diagnostics.py` -> 6 passed.
- `threadvault schemas write --out docs\schemas --json` -> passed and wrote `retrieval_query` plus `retrieval_diagnostics` schema artifacts.
- `py -3.12 -m pytest tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py` -> 21 passed.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 190 passed.
- `threadvault retrieval query pytest --json` -> passed and emitted the v2 retrieval object contract.
- `threadvault retrieval diagnose --json` -> passed and emitted diagnostics with FTS index status.
- `threadvault search pytest --json --fields minimal` -> passed and emitted the legacy JSON array contract.
- `threadvault capabilities --json` -> passed and advertised the retrieval command, JSON outputs, and `retrieval_diagnostics` feature flag.
- `threadvault schemas list --json` -> passed and listed `retrieval_query` plus `retrieval_diagnostics`.
- `threadvault retrieval --help` -> passed and listed `query` plus `diagnose`.
- `threadvault retrieval query --help` -> passed and listed query filters, fields, mode, and JSON options.
- `threadvault retrieval diagnose --help` -> passed.
- `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`.
- `Test-Path deep-research-report.md` -> `False`.
- `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`.

This phase adds the v2 machine-facing retrieval contract without changing the existing search JSON contracts, package version, database schema, or global JSON contract version.

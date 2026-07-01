# Phase 03 Acceptance: Summary Evidence Chunk Selection

## Scope

This acceptance covers v2.2 summary/evidence chunk selection. It verifies that ThreadVault can produce stable, evidence-backed chunk payloads for future optional embedding/vector adapters without generating embeddings or vectorizing all raw events.

## Evidence

- Added `threadvault.summary_pipeline`.
- The Summary Pipeline module exposes:
  - `SUMMARY_CHUNKS_CONTRACT_VERSION`
  - `SummaryChunkRequest`
  - `build_summary_chunks`
- The new module returns a provider-neutral JSON payload with:
  - `contract_version`
  - `selection`
  - `chunks`
  - `skipped`
  - `diagnostics`
- Chunk types are:
  - `session_summary`
  - `turn_summary`
  - `evidence`
- Every emitted chunk has `evidence_event_ids`.
- Internal context events such as `turn_context` and `session_meta` are not emitted as chunk text.
- `diagnostics.embedding_generated` is `false`.
- Added `ArchiveStore.summary_chunks(...)`.
- Added CLI:
  - `threadvault summary-pipeline chunks`
- Added JSON schema:
  - `summary_chunks`
- Generated schema artifact:
  - `docs/schemas/summary_chunks.schema.json`
- Updated capabilities and robot docs discovery for:
  - command: `summary-pipeline`
  - JSON output: `summary-pipeline chunks`
  - feature flag: `summary_evidence_chunks: true`
- Updated user documentation and v2 phase index.

## Validation Commands

```powershell
py -3.12 -m pytest tests\test_v203_summary_evidence_chunks.py
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v203_summary_evidence_chunks.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault summary-pipeline chunks --db TEMP_DB --session sess-current --json
threadvault summary-pipeline chunks --db TEMP_DB --project E:\Codex\ThreadVault --json
threadvault capabilities --json
threadvault schemas list --json
threadvault summary-pipeline --help
threadvault summary-pipeline chunks --help
py -3.12 -m pip install -e ".[dev]"
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

## Result

Accepted.

Final validation completed on 2026-07-01:

- `py -3.12 -m pytest tests\test_v203_summary_evidence_chunks.py` -> 6 passed.
- `threadvault schemas write --out docs\schemas --json` -> passed and wrote `summary_chunks.schema.json`.
- `py -3.12 -m pytest tests\test_v203_summary_evidence_chunks.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py` -> 27 passed.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 196 passed.
- `threadvault summary-pipeline chunks --db TEMP_DB --session sess-current --json` -> passed and emitted `session_summary`, `turn_summary`, and `evidence` chunks.
- `threadvault summary-pipeline chunks --db TEMP_DB --project E:\Codex\ThreadVault --json` -> passed and selected fixture project sessions.
- `threadvault capabilities --json` -> passed and advertised `summary-pipeline`, `summary-pipeline chunks`, and `summary_evidence_chunks: true`.
- `threadvault schemas list --json` -> passed and listed `summary_chunks`.
- `threadvault summary-pipeline --help` -> passed and listed `chunks`.
- `threadvault summary-pipeline chunks --help` -> passed and listed session/project selection plus chunk controls.
- `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`.
- `Test-Path deep-research-report.md` -> `False`.
- `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`.

This phase provides embedding-ready chunk selection while preserving local-first defaults and without changing database schema, package version, global JSON contract version, retrieval contracts, or legacy search contracts.

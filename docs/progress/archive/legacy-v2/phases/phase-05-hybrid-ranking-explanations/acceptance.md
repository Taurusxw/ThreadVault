# Phase 05 Acceptance: Hybrid Ranking And Search Explanations

## Scope

This acceptance covers v2.4 hybrid ranking and explanation fields. It verifies that ThreadVault can return one mixed FTS/vector retrieval response, explain per-result ranking factors, and degrade to FTS-only when vector is absent, disabled, or unindexed.

## Evidence

- Added `threadvault.hybrid_retrieval`.
- The hybrid module exposes:
  - `HYBRID_RETRIEVAL_CONTRACT_VERSION`
  - `HYBRID_RANKING_WEIGHTS`
  - `HybridRetrievalRequest`
  - `hybrid_retrieve`
- Added `ArchiveStore.hybrid_retrieve(...)`.
- Added CLI:
  - `threadvault retrieval hybrid`
- Added JSON schema:
  - `hybrid_retrieval`
- Generated schema artifact:
  - `docs/schemas/hybrid_retrieval.schema.json`
- Updated capabilities and robot docs discovery for:
  - JSON output: `retrieval hybrid`
  - feature flag: `hybrid_retrieval: true`
  - retrieval schema: `hybrid_retrieval`
  - hybrid contract version: `hybrid_retrieval.v1`
- Hybrid results include:
  - `hybrid_id`
  - `source`
  - `score`
  - `scores`
  - `evidence_event_ids`
  - `explanation`
- Hybrid diagnostics report:
  - `capabilities_used`
  - FTS status.
  - vector status.
  - ranking strategy and weights.

## Validation Commands

```powershell
py -3.12 -m pytest tests\test_v205_hybrid_retrieval.py
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v205_hybrid_retrieval.py tests\test_v204_local_vector_adapter.py tests\test_v203_summary_evidence_chunks.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault retrieval hybrid pytest --db TEMP_DB --json
threadvault retrieval hybrid "parser failure" --db TEMP_DB --config TEMP_CONFIG --json
threadvault capabilities --json
threadvault schemas list --json
threadvault retrieval hybrid --help
py -3.12 -m pip install -e ".[dev]"
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

## Result

Accepted.

Final validation completed on 2026-07-01:

- `py -3.12 -m pytest tests\test_v205_hybrid_retrieval.py` -> 5 passed.
- `threadvault schemas write --out docs\schemas --json` -> passed and wrote `hybrid_retrieval.schema.json`.
- `py -3.12 -m pytest tests\test_v205_hybrid_retrieval.py tests\test_v204_local_vector_adapter.py tests\test_v203_summary_evidence_chunks.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py` -> 37 passed.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 206 passed.
- `threadvault retrieval hybrid pytest --db TEMP_DB --json` -> passed and returned FTS-only hybrid response with `vector.status = disabled_by_config`.
- `threadvault retrieval hybrid "parser failure" --db TEMP_DB --config TEMP_CONFIG --json` -> passed and returned mixed FTS/vector results with score breakdowns and explanations.
- `threadvault capabilities --json` -> passed and advertised `retrieval hybrid` plus `hybrid_retrieval: true`.
- `threadvault schemas list --json` -> passed and listed `hybrid_retrieval`.
- `threadvault retrieval hybrid --help` -> passed and listed query, config, db, limit, vector-limit, filters, and JSON options.
- `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`.
- `Test-Path deep-research-report.md` -> `False`.
- `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`.

This phase adds the hybrid retrieval contract without changing database schema, package version, global JSON contract version, vector index schema, legacy search contracts, or the existing FTS-only retrieval query contract.

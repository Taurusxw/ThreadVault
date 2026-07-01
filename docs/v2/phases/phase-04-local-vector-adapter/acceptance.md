# Phase 04 Acceptance: Local Vector Adapter

## Scope

This acceptance covers v2.3 local vector adapter work. It verifies that ThreadVault can build and query a local SQLite-backed vector index from `summary_chunks`, behind an explicit config gate, without external model calls or default vector indexing.

## Evidence

- Added config gate under `[retrieval.vector]`:
  - `enabled`
  - `adapter`
  - `dimensions`
- Missing config or `enabled = false` leaves vector index/query disabled.
- Added database schema version `4`.
- Added derived vector index tables:
  - `vector_index_meta`
  - `vector_chunks`
- Added `threadvault.vector_adapter`.
- The vector adapter exposes:
  - `VECTOR_CONTRACT_VERSION`
  - `LOCAL_VECTOR_ADAPTER`
  - `VectorIndexRequest`
  - `build_vector_index`
  - `query_vector_index`
  - `vector_index_status`
  - `embed_text`
- Added CLI commands:
  - `threadvault vector index`
  - `threadvault vector query`
  - `threadvault vector status`
- Added JSON schemas:
  - `vector_index`
  - `vector_query`
  - `vector_status`
- Generated schema artifacts:
  - `docs/schemas/vector_index.schema.json`
  - `docs/schemas/vector_query.schema.json`
  - `docs/schemas/vector_status.schema.json`
- Updated capabilities and robot docs discovery for:
  - command: `vector`
  - JSON outputs: `vector index`, `vector query`, `vector status`
  - feature flags: `local_vector_adapter: true`, `local_vector_enabled_by_default: false`
- Updated user documentation and v2 phase index.

## Validation Commands

```powershell
py -3.12 -m pytest tests\test_v204_local_vector_adapter.py
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v204_local_vector_adapter.py tests\test_v203_summary_evidence_chunks.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v29_doctor_schema_contract.py tests\test_v12_app_config.py tests\test_v06_schemas.py
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault vector index --db TEMP_DB --session sess-current --json
threadvault vector index --db TEMP_DB --session sess-current --config TEMP_CONFIG --json
threadvault vector query "parser failure" --db TEMP_DB --config TEMP_CONFIG --json
threadvault vector status --db TEMP_DB --config TEMP_CONFIG --json
threadvault capabilities --json
threadvault schemas list --json
threadvault vector --help
threadvault vector index --help
threadvault vector query --help
threadvault vector status --help
py -3.12 -m pip install -e ".[dev]"
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

## Result

Accepted.

Final validation completed on 2026-07-01:

- `py -3.12 -m pytest tests\test_v204_local_vector_adapter.py` -> 5 passed.
- `threadvault schemas write --out docs\schemas --json` -> passed and wrote `vector_index`, `vector_query`, and `vector_status` schema artifacts.
- `py -3.12 -m pytest tests\test_v204_local_vector_adapter.py tests\test_v203_summary_evidence_chunks.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v29_doctor_schema_contract.py tests\test_v12_app_config.py tests\test_v06_schemas.py` -> 42 passed.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 201 passed.
- `threadvault vector index --db TEMP_DB --session sess-current --json` without enabled config -> exited 1 with JSON error code `vector_disabled`.
- `threadvault vector index --db TEMP_DB --session sess-current --config TEMP_CONFIG --json` -> passed and indexed 3 chunks from `summary_chunks`.
- `threadvault vector query "parser failure" --db TEMP_DB --config TEMP_CONFIG --json` -> passed and returned ranked chunks with scores and evidence event IDs.
- `threadvault vector status --db TEMP_DB --config TEMP_CONFIG --json` -> passed and reported enabled config plus matching vector index chunks.
- `threadvault capabilities --json` -> passed and advertised schema version `4`, vector commands, and local vector feature flags.
- `threadvault schemas list --json` -> passed and listed `vector_index`, `vector_query`, and `vector_status`.
- `threadvault vector --help` -> passed and listed `index`, `query`, and `status`.
- `threadvault vector index --help` -> passed and listed session/project selection, config, db, chunk controls, and JSON options.
- `threadvault vector query --help` -> passed and listed query, config, db, limit, and JSON options.
- `threadvault vector status --help` -> passed.
- `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`.
- `Test-Path deep-research-report.md` -> `False`.
- `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`.

This phase intentionally changes the database schema version from `3` to `4` for local derived vector index tables. It does not change the package version, global JSON contract version, backup manifest version, restore record version, retrieval query contract, or legacy search contracts.

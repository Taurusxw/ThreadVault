# Phase 06 Acceptance: Agent-Facing Retrieval Interface

## Status

Accepted on 2026-07-01.

## Completed

- Added `threadvault.agent_interface` as the agent-facing retrieval module.
- Added agent-facing contract versions:
  - `agent_interface.v1`
  - `agent_retrieval.v1`
- Added manifest composition for retrieval capabilities, schema names, recommended commands, privacy defaults, and local vector configuration state.
- Added agent retrieval over existing retrieval modules:
  - `hybrid` mode on top of `threadvault.hybrid_retrieval`.
  - `fts` mode on top of `threadvault.retrieval`.
- Kept `hybrid` as the default mode, preserving FTS-only degradation when vector is disabled or unavailable.
- Added privacy-preserving default result shaping:
  - default output omits local metadata/path fields.
  - `--local-debug` explicitly includes local debug metadata.
- Added `ArchiveStore.agent_manifest(...)` and `ArchiveStore.agent_retrieve(...)`.
- Added CLI commands:
  - `threadvault agent manifest`
  - `threadvault agent retrieve`
- Added JSON schemas:
  - `agent_interface_manifest`
  - `agent_retrieval`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities and robot docs discovery for the agent interface.
- Updated `docs/v2/README.md`.
- Updated `docs/THREADVAULT_USAGE_MANUAL.md`.
- Added `tests/test_v206_agent_interface.py`.

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v206_agent_interface.py
py -3.12 -m ruff check src\threadvault\agent_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v206_agent_interface.py
```

Results:

- `tests\test_v206_agent_interface.py` -> 6 passed.
- Focused ruff -> passed after import ordering fix.

Schema and adjacent v2 regression:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v205_hybrid_retrieval.py tests\test_v204_local_vector_adapter.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py
```

Results:

- Schema generation wrote `agent_interface_manifest.schema.json` and `agent_retrieval.schema.json`.
- Adjacent regression -> 30 passed.

Final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault agent manifest --json
threadvault agent retrieve pytest --db TEMP_DB --json
threadvault agent retrieve pytest --mode fts --db TEMP_DB --local-debug --json
threadvault capabilities --json
threadvault schemas list --json
threadvault agent manifest --help
threadvault agent retrieve --help
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

Results:

- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 212 passed.
- `threadvault agent manifest --json` -> passed and emitted `agent_interface.v1`.
- `threadvault agent retrieve pytest --db TEMP_DB --json` -> passed and emitted hybrid-mode `agent_retrieval.v1` with FTS-only degradation.
- `threadvault agent retrieve pytest --mode fts --db TEMP_DB --local-debug --json` -> passed and emitted local debug metadata with `privacy.raw_paths_included = true`.
- `threadvault capabilities --json` -> passed and listed `agent` plus `agent_retrieval_interface`.
- `threadvault schemas list --json` -> passed and listed `agent_interface_manifest` plus `agent_retrieval`.
- `threadvault agent manifest --help` and `threadvault agent retrieve --help` -> passed.
- `Test-Path deep-research-report.md` -> `False`.
- Runtime/import metadata -> `0.31.0` and `0.31.0`.

## Acceptance Evidence

- `threadvault agent manifest --json` validates against `agent_interface_manifest`.
- `threadvault agent retrieve pytest --json` validates against `agent_retrieval`.
- `threadvault agent retrieve pytest --mode fts --json` validates against `agent_retrieval`.
- Default agent retrieval output omits local metadata.
- `--local-debug` output includes local metadata and sets `privacy.raw_paths_included = true`.
- Capabilities include `agent` commands and `agent_retrieval_interface`.
- Robot docs include the agent interface contract versions and schema names.

## Deferred

- Full MCP server adapter.
- JSON request body input from file or stdin.
- More advanced per-field redaction policy for agent result text.
- Saved agent query profiles.

## Bugs Found

- Ruff caught unsorted imports in `src/threadvault/store.py`; fixed with `ruff --fix`.

## Next

- Continue v2 toward Phase 07 final v2 acceptance smoke covering FTS-only and semantic-enabled modes.

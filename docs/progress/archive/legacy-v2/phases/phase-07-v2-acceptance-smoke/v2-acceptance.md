# v2 Acceptance Smoke

## Status

Accepted on 2026-07-01.

## Scope

This acceptance smoke covers the completed v2 retrieval and interfaces line:

- Retrieval module FTS wrapper.
- Retrieval JSON contracts and diagnostics.
- Summary/evidence chunk selection.
- Config-gated local vector adapter.
- Hybrid ranking and explanations.
- Agent-facing retrieval interface.

## Acceptance Evidence

### FTS-Only Mode

The acceptance smoke imports fixture Codex sessions into a temporary database, then verifies:

- `threadvault retrieval query pytest --json` returns `retrieval_query`.
- `diagnostics.used_mode` is `fts`.
- results are present.
- `threadvault retrieval hybrid pytest --json` returns `hybrid_retrieval`.
- hybrid diagnostics report `["fts", "hybrid"]`.
- vector diagnostics report `disabled_by_config`.
- all hybrid results include `evidence_event_ids`.
- `threadvault agent retrieve pytest --json` returns `agent_retrieval`.
- agent diagnostics report `["fts", "hybrid"]`.
- default agent output omits local metadata and sets `privacy.raw_paths_included = false`.

### Vector-Enabled Mode

The acceptance smoke creates a temporary `threadvault.toml` with:

```toml
[retrieval.vector]
enabled = true
adapter = "local-hash"
dimensions = 64
```

It then verifies:

- `threadvault vector index --session sess-current --config TEMP_CONFIG --json` returns `vector_index`.
- indexed chunk count is greater than zero.
- `threadvault vector status --config TEMP_CONFIG --json` returns `vector_status`.
- vector config is enabled and matching indexed chunks exist.
- `threadvault retrieval hybrid "parser failure" --config TEMP_CONFIG --json` returns `hybrid_retrieval`.
- hybrid diagnostics report `["fts", "vector", "hybrid"]`.
- hybrid results include both `fts` and `vector` sources.
- `threadvault agent retrieve "parser failure" --config TEMP_CONFIG --json` returns `agent_retrieval`.
- agent diagnostics report `["fts", "vector", "hybrid"]`.
- agent results include both `fts` and `vector` sources while still omitting local metadata by default.

### Discovery And Contracts

The acceptance smoke verifies:

- `capabilities()` advertises v2 feature flags:
  - `retrieval_module`
  - `retrieval_diagnostics`
  - `summary_evidence_chunks`
  - `local_vector_adapter`
  - `hybrid_retrieval`
  - `agent_retrieval_interface`
- `local_vector_enabled_by_default` remains `false`.
- `robot_guide()` advertises retrieval, summary pipeline, vector, and agent interface schemas.
- `robot_schemas()` and the schema registry include all v2 schemas.
- every v2 schema artifact exists under `docs/schemas/`.
- Phase 01 through Phase 07 planning and acceptance documents exist.
- `deep-research-report.md` remains absent.

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v207_v2_acceptance.py
py -3.12 -m ruff check tests\test_v207_v2_acceptance.py
```

Results:

- `tests\test_v207_v2_acceptance.py` -> 3 passed.
- Focused ruff -> passed.

Adjacent v2 validation:

```powershell
py -3.12 -m pytest tests\test_v201_retrieval_module.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v203_summary_evidence_chunks.py tests\test_v204_local_vector_adapter.py tests\test_v205_hybrid_retrieval.py tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py
```

Result:

- Adjacent v2 validation -> 38 passed.

Final validation:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault capabilities --json
threadvault schemas list --json
threadvault retrieval query pytest --db TEMP_DB --json
threadvault retrieval hybrid pytest --db TEMP_DB --json
threadvault agent manifest --json
threadvault agent retrieve pytest --db TEMP_DB --json
threadvault vector status --db TEMP_DB --json
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

Results:

- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 215 passed.
- `threadvault capabilities --json` -> passed and listed v2 commands and feature flags.
- `threadvault schemas list --json` -> passed and listed all v2 schemas.
- `threadvault retrieval query pytest --db TEMP_DB --json` -> passed.
- `threadvault retrieval hybrid pytest --db TEMP_DB --json` -> passed with FTS-only degradation.
- `threadvault agent manifest --json` -> passed.
- `threadvault agent retrieve pytest --db TEMP_DB --json` -> passed.
- `threadvault vector status --db TEMP_DB --json` -> passed with vector disabled by default.
- `Test-Path deep-research-report.md` -> `False`.
- Runtime/import metadata -> `0.31.0` and `0.31.0`.

## Final Result

ThreadVault v2 meets the roadmap acceptance criteria:

- Existing search behavior remains backed by the retrieval module.
- Retrieval and hybrid results include traceable evidence event IDs.
- Vector retrieval is optional and config-gated.
- Hybrid retrieval reports used capabilities.
- Agent-facing retrieval avoids raw local metadata by default and exposes local debug metadata only on explicit request.
- Future MCP/client work can sit on top of the same retrieval and agent interface modules.

## Deferred To v3 Or Later

- Full MCP server process and deployment packaging.
- Desktop/Web/IDE clients.
- Team permissions, centralized audit, cloud sync.
- External embedding providers or LLM summaries as defaults.

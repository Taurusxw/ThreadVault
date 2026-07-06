# Phase 07 / v2.6: v2 Acceptance Smoke

## Summary

Phase 07 is the final v2 acceptance smoke. It does not add a new feature module. It verifies that the v2 retrieval and interfaces product line is coherent across FTS-only mode, optional vector-enabled mode, hybrid ranking, agent-facing retrieval, schema discovery, documentation, and local-first/privacy-first constraints.

## Source Of Truth Read Before Implementation

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v2-retrieval-and-interfaces.md`
- `docs/v2/README.md`
- `docs/development-progress.md`
- Phase 01-06 plan, design, and acceptance documents under `docs/v2/phases/`

## Current v2 Capability Chain

- Phase 01: `threadvault.retrieval` wraps FTS5 search.
- Phase 02: retrieval JSON contracts and diagnostics.
- Phase 03: summary/evidence chunks for high-value embedding inputs.
- Phase 04: config-gated local vector adapter.
- Phase 05: hybrid ranking and explanations.
- Phase 06: agent-facing retrieval interface.

## Product Goal

Prove that v2 reaches the roadmap acceptance shape:

- Existing search commands continue to work through the retrieval module.
- Retrieval results include evidence references.
- Semantic/vector retrieval is optional and FTS remains usable when vector is absent.
- Hybrid search reports which capabilities were used.
- Agent-facing interfaces avoid private raw paths by default and expose local debug metadata only on explicit request.
- CLI, agent interface, future MCP adapters, and future GUI clients can rely on the same retrieval contracts.

## Implementation Plan

1. Add `tests/test_v207_v2_acceptance.py`.
2. Cover FTS-only acceptance:
   - import fixture Codex sessions into a temp DB.
   - run `retrieval query`.
   - run `retrieval hybrid` without vector config.
   - run `agent retrieve` without vector config.
   - assert evidence event IDs and FTS-only diagnostics.
3. Cover vector-enabled acceptance:
   - create temp config with `[retrieval.vector] enabled = true`.
   - build vector index from fixture session chunks.
   - run `vector status`.
   - run `retrieval hybrid`.
   - run `agent retrieve`.
   - assert vector capability is used where indexed chunks are available.
4. Cover discovery and contracts:
   - `capabilities` advertises v2 feature flags.
   - `robot_guide` advertises retrieval, vector, hybrid, and agent schemas.
   - `robot_schemas` and schema registry include all v2 contracts.
   - `validate_payload` accepts representative v2 payloads.
5. Cover documentation/source-of-truth:
   - v2 README links every phase including Phase 07.
   - every phase has a plan and acceptance file.
   - `deep-research-report.md` remains absent.
6. Update `docs/v2/README.md`.
7. Write `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md` after validation.
8. Append `docs/development-progress.md`.

## Out Of Scope

- No new database schema.
- No new vector algorithm.
- No MCP server process.
- No package version bump.
- No root DOCX or retired root research report update.

## Test Plan

Focused:

```powershell
py -3.12 -m pytest tests\test_v207_v2_acceptance.py
```

Adjacent v2:

```powershell
py -3.12 -m pytest tests\test_v201_retrieval_module.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v203_summary_evidence_chunks.py tests\test_v204_local_vector_adapter.py tests\test_v205_hybrid_retrieval.py tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py
```

Final:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault capabilities --json
threadvault schemas list --json
threadvault retrieval query pytest --json
threadvault retrieval hybrid pytest --json
threadvault agent manifest --json
threadvault agent retrieve pytest --json
threadvault vector status --json
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

## Acceptance Criteria

- Phase 07 focused tests pass.
- Full test suite passes.
- All v2 public schemas exist under `docs/schemas/`.
- V2 acceptance document records FTS-only and vector-enabled evidence.
- `docs/v2/README.md` marks Phase 07 accepted.
- `docs/development-progress.md` records final v2 acceptance.
- No root `deep-research-report.md` is recreated.
- Version remains `0.31.0` unless a separate release/version-bump phase is requested.

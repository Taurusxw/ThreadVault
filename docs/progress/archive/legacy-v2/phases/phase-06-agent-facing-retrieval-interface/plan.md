# Phase 06 / v2.5: Agent-Facing Retrieval Interface

## Summary

Phase 06 adds a stable agent-facing retrieval interface on top of the existing v2 retrieval, hybrid retrieval, vector status, schema, and capabilities work. The goal is to give MCP adapters, Codex agents, and other machine clients one compact discovery and query surface without making them learn every CLI branch or raw database detail.

This phase intentionally implements an agent-friendly JSON interface, not a full MCP server runtime. A future MCP adapter can call the same module and expose the same contracts.

## Source Of Truth Read Before Implementation

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v2-retrieval-and-interfaces.md`
- `docs/v2/README.md`
- `docs/v1/README.md`
- `docs/v0/README.md`
- `docs/development-progress.md`
- `docs/v0/research/codex-session-archive-research.md` as historical context for agent-oriented exports and comparable projects

The active v2 roadmap is `docs/roadmap/v2-retrieval-and-interfaces.md`. Older prompt text that mentions `docs/roadmap/v2-personal-knowledge-layer.md` or `docs/v0-v1/` is stale and must not recreate those paths.

## Current Baseline

The current v2 implementation already has:

- `threadvault.retrieval` with the `retrieval_query` and `retrieval_diagnostics` contracts.
- `threadvault.summary_pipeline` with high-value evidence chunk selection.
- `threadvault.vector_adapter` behind explicit `[retrieval.vector] enabled = true` configuration.
- `threadvault.hybrid_retrieval` with weighted FTS/vector ranking and explanations.
- Capabilities, robot docs, and schema discovery for those contracts.

Phase 06 should reuse those modules instead of copying query logic into the CLI.

## Product Goal

An agent should be able to:

1. Discover what retrieval capabilities ThreadVault supports.
2. See which JSON schemas and commands are stable for retrieval work.
3. Send one retrieval request that can choose `fts` or `hybrid`.
4. Receive ranked results with evidence event IDs and diagnostics.
5. Avoid accidental exposure of local raw database internals or private raw paths.

## Architecture Deepening

### New Module: Agent Interface

Add `threadvault.agent_interface` as a deep module with a small interface:

- `agent_manifest(config) -> dict`
- `agent_retrieve(conn, request, config) -> dict`

The module owns:

- Agent-facing contract versions.
- Retrieval mode selection between `fts` and `hybrid`.
- Query/request normalization.
- Manifest composition from existing capability/schema knowledge.
- Privacy-preserving result shaping.
- Explicit local debug expansion when requested.

The CLI should be a thin adapter. It should parse options, call the module through `ArchiveStore`, and print JSON or a compact table.

### New CLI Group

Add:

- `threadvault agent manifest --json`
- `threadvault agent retrieve QUERY --mode fts|hybrid --json`

The `agent` namespace is intentionally generic enough for future MCP/tool adapters, but Phase 06 only exposes retrieval-oriented capabilities.

### New JSON Contracts

Add schemas:

- `agent_interface_manifest`
- `agent_retrieval`

The manifest contract should include:

- `contract_version`
- `interface`
- `capabilities`
- `schemas`
- `recommended_commands`
- `privacy`
- `defaults`

The retrieval contract should include:

- `contract_version`
- `request`
- `results`
- `diagnostics`
- `privacy`

## Interface Rules

- Default mode is `hybrid`, because hybrid degrades to FTS-only when vector is disabled or unavailable.
- `fts` mode remains available for clients that want the simpler `retrieval_query` contract.
- `vector` is not a direct agent mode in this phase; agents use `hybrid` so FTS fallback is preserved.
- Results must include `evidence_event_ids`.
- Results must include source information such as `fts` or `vector`.
- Results must include enough text for agent use, but should avoid exposing raw database paths or raw transcript paths by default.
- `--local-debug` may include extra result metadata such as file path fields already present in retrieval/hybrid payloads.
- The module should not expose raw SQLite table names, raw SQL, or local archive paths.

## Out Of Scope

- Full MCP server process.
- REST server or long-running daemon.
- New vector provider or external embedding model.
- New ranking algorithm.
- GUI, desktop, VS Code/Cursor extension, team permissions, cloud sync.
- Changes to database schema or package version.

## Implementation Plan

1. Add `src/threadvault/agent_interface.py`.
2. Add dataclass request objects for manifest and retrieval requests.
3. Implement manifest composition using existing constants and `vector_index_status`.
4. Implement `agent_retrieve` on top of:
   - `retrieve_response` for `fts`.
   - `hybrid_retrieve` for `hybrid`.
5. Shape results into a common agent result structure.
6. Add `ArchiveStore.agent_manifest(...)` and `ArchiveStore.agent_retrieve(...)`.
7. Add CLI group and commands:
   - `agent manifest`
   - `agent retrieve`
8. Register schemas in `src/threadvault/schemas.py`.
9. Update capabilities and robot docs discovery.
10. Add tests in `tests/test_v206_agent_interface.py`.
11. Update user-facing docs where commands are visible.
12. Update `docs/v2/README.md`.
13. Generate schema files if schemas changed.
14. Write `acceptance.md` after validation.
15. Append `docs/development-progress.md`.

## Test Plan

Focused tests:

```powershell
py -3.12 -m pytest tests\test_v206_agent_interface.py
```

Schema and adjacent v2 regression:

```powershell
py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v205_hybrid_retrieval.py tests\test_v204_local_vector_adapter.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py
```

Schema regeneration and validation:

```powershell
threadvault schemas write --out docs\schemas --json
threadvault agent manifest --json
threadvault agent retrieve pytest --json
threadvault agent retrieve "parser failure" --mode hybrid --json
threadvault validate-json --schema agent_interface_manifest --input AGENT_MANIFEST_JSON --json
threadvault validate-json --schema agent_retrieval --input AGENT_RETRIEVAL_JSON --json
```

Final validation:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault capabilities --json
threadvault schemas list --json
threadvault agent manifest --help
threadvault agent retrieve --help
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

## Acceptance Criteria

- Agents can discover retrieval interface capabilities through `threadvault agent manifest --json`.
- Agents can run `threadvault agent retrieve QUERY --json` and receive an `agent_retrieval` payload.
- `hybrid` mode degrades to FTS-only when vector is disabled, preserving local default behavior.
- `fts` mode remains available and maps to the existing retrieval module.
- Agent results include stable IDs, source, score, text, evidence event IDs, and diagnostics.
- Default agent output avoids raw local paths; `--local-debug` explicitly opts into extra local metadata.
- `capabilities`, `robot-docs`, and `schemas list` expose the new agent interface.
- Existing retrieval, hybrid, vector, and legacy search behavior remains compatible.
- `deep-research-report.md` remains absent.

## Documentation Rules

This phase updates:

- `docs/v2/phases/phase-06-agent-facing-retrieval-interface/plan.md`
- `docs/v2/phases/phase-06-agent-facing-retrieval-interface/design-notes.md`
- `docs/v2/phases/phase-06-agent-facing-retrieval-interface/acceptance.md`
- `docs/v2/README.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- `docs/development-progress.md`
- `docs/schemas/*.schema.json`

Do not recreate or update `deep-research-report.md`. Do not modify the root DOCX. Keep root `README.md` short unless a compact command pointer becomes clearly necessary.

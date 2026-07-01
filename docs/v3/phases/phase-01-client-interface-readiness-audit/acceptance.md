# v3 Phase 01 Acceptance: Client Interface Readiness Audit

## Status

Accepted on 2026-07-01.

## Scope

This acceptance covers the v3 kickoff and readiness audit for richer clients and optional team governance.

The phase creates the v3 documentation entrypoint, records the initial client-interface boundary, and adds a focused
test for the interface discovery and local-first defaults that future v3 clients must preserve.

## Acceptance Evidence

The readiness audit confirms:

- `docs/v3/README.md` exists and points to the v3 roadmap.
- Phase 01 has `plan.md`, `design-notes.md`, and `acceptance.md`.
- `docs/README.md` includes v3 as the active development record and lists the v3 starting documents.
- v3 docs state that richer clients must reuse existing archive/export/summary/retrieval/vector/hybrid/agent-facing
  interfaces.
- `capabilities()` advertises:
  - `retrieval`
  - `summary-pipeline`
  - `vector`
  - `agent`
  - `export-target`
- `robot_guide()` advertises:
  - `agent_interface`
  - `retrieval`
  - `summary_pipeline`
  - `vector`
- `robot_schemas()` includes:
  - `agent_interface_manifest`
  - `agent_retrieval`
  - `hybrid_retrieval`
  - `summary_chunks`
  - `vector_status`
  - `export_target_manifest`
- `agent manifest --json` reports:
  - `mcp_runtime_included = false`
  - `raw_paths_in_default_output = false`
  - `external_model_calls = false`
- `capabilities()` keeps:
  - `local_first = true`
  - `local_vector_enabled_by_default = false`
  - `cloud_sync = false`
  - `external_llm_summary = false`

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v301_client_interface_readiness.py
py -3.12 -m ruff check tests\test_v301_client_interface_readiness.py
```

Results:

- `tests\test_v301_client_interface_readiness.py` -> passed.
- Focused ruff -> passed.

Adjacent validation:

```powershell
py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py tests\test_v301_client_interface_readiness.py
```

Result:

- Adjacent interface validation -> passed.

Manual smoke:

```powershell
threadvault capabilities --json
threadvault agent manifest --json
Test-Path deep-research-report.md
```

Results:

- `threadvault capabilities --json` -> passed.
- `threadvault agent manifest --json` -> passed.
- `Test-Path deep-research-report.md` -> `False`.

## Result

ThreadVault v3 now has a Markdown entrypoint and a tested client-interface readiness baseline. The first richer client can
start from existing v2 contracts without duplicating transcript parsing or retrieval logic.

## Deferred To Later v3 Phases

- Pick and implement the first richer client.
- Design an optional server interface.
- Define team permissions around raw transcript, summary/search, export, retention, restore, and delete capabilities.
- Extend audit logging for shared read/export/delete/restore operations.


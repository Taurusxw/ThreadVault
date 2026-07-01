# v3 Phase 33 Acceptance: v3 Final Acceptance Smoke

## Status

Accepted on 2026-07-01.

## Scope

Phase 33 accepts the final v3 smoke for richer clients and optional team-governance capabilities.

The accepted runtime is:

- `governance_v3_acceptance_smoke`
- CLI command:
  - `threadvault governance v3 acceptance-smoke`
- JSON schema:
  - `governance_v3_acceptance_smoke`

## Acceptance Evidence

The final smoke verifies:

- local CLI and governance defaults remain local-first and server/cloud opt-in
- accepted v2 retrieval, hybrid retrieval, vector-disabled default, and agent retrieval still work
- local richer client/TUI can browse, search, and export-preview without writing files
- optional read-only server prototype passes in-process smoke and remains opt-in
- governance separates raw transcript access from summary/search access
- denied sensitive side effects can be blocked before execution
- local preflight audit evidence can be written
- identity actor binding, central policy store, centralized audit store, and centralized backup policy runtimes are
  discoverable
- external model calls remain disabled by default and exposed through preflight diagnostics only
- capabilities, robot guide, robot schemas, generated schemas, phase docs, and retired root-report invariant are present

## Validation

- Schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_v3_acceptance_smoke.schema.json`
- Focused validation:
  - `py -3.12 -m pytest tests\test_v333_v3_final_acceptance_smoke.py -q` -> 3 passed
  - `py -3.12 -m ruff check src\threadvault\store.py src\threadvault\cli.py src\threadvault\governance.py src\threadvault\schemas.py tests\test_v321_v3_completion_gap_audit.py tests\test_v333_v3_final_acceptance_smoke.py` -> passed
- Adjacent v3 validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v322_identity_actor_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v331_centralized_backup_restore_policy_runtime.py tests\test_v332_business_command_governance_instrumentation.py tests\test_v333_v3_final_acceptance_smoke.py -q` -> 70 passed
- Final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 376 passed
- Manual final smoke:
  - Imported fixture Codex sessions into a temporary database.
  - `threadvault governance v3 acceptance-smoke --db TEMP_DB --work-dir TEMP_WORK --query pytest --session sess-current --json`
    -> passed with `status = accepted`, `ok = true`, `required_check_count = 7`, `failed_check_count = 0`, and
    `criteria_satisfied_count = 5`
- Final gap audit:
  - `threadvault governance v3 gap-audit --json` -> passed with `overall_status = complete`, `v3_complete = true`,
    `accepted_phase_count = 33`, `current_phase = phase-33-v3-final-acceptance-smoke`, and `blocking_count = 0`
- Retired report invariant:
  - `Test-Path deep-research-report.md` -> `False`

## Final Result

ThreadVault v3 meets the roadmap acceptance criteria:

- The CLI remains fully usable without any server.
- A richer client can browse/search/export-preview without duplicating parser logic.
- Optional shared deployment paths can distinguish raw transcript access from summary/search access.
- Audit evidence exists for sensitive operations through local audit and governance instrumentation.
- External model/cloud behavior is explicit, configurable, and disabled by default.

## Non-Claims Preserved

- No mandatory server or cloud behavior.
- No production shared enforcement claim.
- No authenticated external identity provider.
- No external model execution.
- No rewrite of accepted v2 retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval.

## Follow-Up Tracks

Future v3.x or v4 work can harden opt-in production shared enforcement, desktop/IDE packaging, external identity
providers, and richer client shells. Those tracks must continue to preserve local-first/privacy-first defaults.

# v3 Phase 25 Acceptance: Read-Only Shared Server Prototype

## Status

Accepted on 2026-07-01.

## Implemented

- Added `threadvault.shared_server` as the read-only server prototype module.
- Added manifest and smoke contracts:
  - `governance_read_only_server_manifest`
  - `governance_read_only_server_smoke`
- Added CLI commands:
  - `threadvault governance server read-only-manifest --json`
  - `threadvault governance server read-only-smoke --json`
  - `threadvault governance server serve-read-only --enable --host 127.0.0.1 --port 8765`
- Added a route manifest for read-only GET routes over existing ThreadVault interfaces:
  - `/health`
  - `/manifest`
  - `/client/manifest`
  - `/client/overview`
  - `/agent/retrieve`
  - `/governance/status`
  - `/governance/server/policy-readiness`
- Updated capabilities, robot guide, robot schemas, and generated schema artifacts.
- Updated v3 gap audit so `shared_read_only_deployment` is now `prototype_accepted` while v3 remains incomplete.

## Boundary Checks

- Server runtime remains opt-in and is not required for local CLI use.
- `serve-read-only` requires explicit `--enable` before binding a socket.
- The default host is loopback-oriented: `127.0.0.1`.
- No write routes are exposed.
- Export execution, restore execution, retention mutation, and external model calls are not exposed.
- Identity binding, central policy enforcement, central audit, and production shared deployment readiness remain out of
  scope.
- Accepted v2 retrieval, hybrid retrieval, vector indexing, and agent-facing retrieval were not rewritten.

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v325_read_only_shared_server_prototype.py -q
py -3.12 -m pytest tests\test_v325_read_only_shared_server_prototype.py tests\test_v321_v3_completion_gap_audit.py -q
py -3.12 -m ruff check src\threadvault\shared_server.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py src\threadvault\governance.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v321_v3_completion_gap_audit.py
```

Results:

- Phase 25 focused tests -> 5 passed.
- Phase 25 plus v3 gap audit tests -> 9 passed.
- Focused ruff -> passed.

Adjacent validation:

```powershell
py -3.12 -m pytest tests\test_v325_read_only_shared_server_prototype.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v303_client_overview.py tests\test_v28_capabilities_schema_contract.py -q
py -3.12 -m ruff check src\threadvault\shared_server.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py src\threadvault\governance.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py
```

Results:

- Adjacent server/client/discovery validation -> 22 passed.
- Adjacent ruff -> passed.

Manual smoke:

```powershell
threadvault schemas write --out docs\schemas --json
threadvault governance server read-only-manifest --json
threadvault governance server read-only-smoke --query pytest --json
threadvault governance v3 gap-audit --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- Schema artifacts were generated, including `governance_read_only_server_manifest.schema.json` and
  `governance_read_only_server_smoke.schema.json`.
- `read-only-manifest` returned `runtime.implemented = true`, `runtime.prototype = true`, and
  `runtime.production_ready = false`.
- `read-only-smoke` returned `ok = true` across 7 in-process routes.
- `v3 gap-audit` returned `v3_complete = false` and removed `optional_shared_server_runtime_missing` from blockers.
- `deep-research-report.md` remained absent.

## Remaining Work

- Accept or explicitly defer a concrete richer client runtime.
- Implement identity provider, actor binding, and team role mapping.
- Implement central policy storage and policy provenance.
- Implement central audit storage, query, retention, and tamper evidence.
- Implement central backup/restore policy for shared archives.
- Add automatic governance instrumentation for at least one narrow business command slice.
- Run final v3 acceptance smoke.

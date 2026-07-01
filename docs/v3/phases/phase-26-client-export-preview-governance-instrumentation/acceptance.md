# v3 Phase 26 Acceptance: Client Export Preview Governance Instrumentation

## Status

Accepted on 2026-07-01.

## Implemented

- Added explicit governance instrumentation options to `threadvault client export-preview`:
  - `--governance-role`
  - `--governance-config`
  - `--governance-audit-log`
  - `--governance-actor`
- Reused `governance_export_preview_preflight` from the business command path.
- Added `governance_instrumentation` to the `client_export_preview` JSON payload.
- Added blocked preview payloads when governance is enabled and the role is denied.
- Added optional local preflight audit writes from the business command path.
- Updated v3 gap audit to mark automatic instrumentation as partially accepted, not missing.
- Updated capabilities, robot guide, robot schemas, and generated schema artifacts.

## Boundary Checks

- Default `client export-preview` remains read-only and backward-compatible.
- Instrumentation is explicit; omitted governance options do not enable preflight.
- Preview instrumentation never writes export files or manifests.
- Audit records are local JSONL only and only written when `--governance-audit-log` is provided.
- Blocking happens before preview planning when governance is enabled and the role is denied.
- This phase does not implement broad command coverage, central policy, central audit, identity binding, or final v3 smoke.

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v326_client_export_preview_governance_instrumentation.py -q
py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py src\threadvault\governance.py tests\test_v326_client_export_preview_governance_instrumentation.py
```

Results:

- Phase 26 focused tests -> 5 passed.
- Focused ruff -> passed after wrapping long governance descriptions.

Adjacent validation:

```powershell
py -3.12 -m pytest tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v305_client_export_preview.py tests\test_v317_export_preview_governance_preflight.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v28_capabilities_schema_contract.py -q
py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py src\threadvault\governance.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py
```

Results:

- Adjacent client/governance/discovery validation -> 32 passed.
- Adjacent ruff -> passed.

Manual smoke:

```powershell
threadvault schemas write --out docs\schemas --json
threadvault client export-preview --db TEMP_DB --session sess-current --out TEMP_OUT --governance-role reviewer --json
threadvault client export-preview --db TEMP_DB --session sess-current --out TEMP_OUT --governance-config TEMP_CONFIG --governance-role reader --json
threadvault client export-preview --db TEMP_DB --session sess-current --out TEMP_OUT --governance-role reviewer --governance-audit-log TEMP_LOG --governance-actor reviewer@example --json
threadvault governance audit list --log TEMP_LOG --json
threadvault governance v3 gap-audit --json
```

Results:

- Schema artifacts regenerated successfully.
- Instrumented reviewer preview returned `reason = preflight_allowed`, `preview_generated = true`, and
  `governance_blocked = false`.
- Governance-enabled reader preview returned `reason = preflight_blocked`, `planned_file_count = 0`, and
  `governance_blocked = true`.
- Audit smoke wrote a local `export_preview_preflight` record with `business_command_executed = false` and
  `files_written = false`.
- v3 gap audit returned `current_phase = phase-26-client-export-preview-governance-instrumentation`,
  `automatic_instrumentation = partially_accepted`, and `v3_complete = false`.

## Remaining Work

- Expand automatic governance instrumentation beyond `client export-preview`.
- Accept or explicitly defer a concrete richer client runtime.
- Implement identity provider, actor binding, and team role mapping.
- Implement central policy storage and policy provenance.
- Implement central audit storage, query, retention, and tamper evidence.
- Implement central backup/restore policy for shared archives.
- Run final v3 acceptance smoke.

# v3 Phase 09 Acceptance: Permission Preflight Workflow

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

The phase is accepted when validation proves:

- `threadvault governance permission check --json` emits `governance_permission_check`.
- Governance-disabled checks set `enforced = false`.
- Governance-enabled checks allow and deny according to role/access mappings.
- Optional audit logging writes a local audit record.
- `governance_permission_check` exists in the schema registry and packaged schema artifacts.
- Capabilities and robot docs discovery advertise the workflow.
- `deep-research-report.md` remains absent.

## Validation Commands

Final validation included:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v309_permission_preflight.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v309_permission_preflight.py
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault governance permission check --operation export_archive --role reviewer --json
threadvault governance permission check --operation read_raw_transcript --role reader --config TEMP_CONFIG --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

## Validation Results

- `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_permission_check.schema.json`.
- `py -3.12 -m pytest tests\test_v309_permission_preflight.py` -> 5 passed.
- `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v309_permission_preflight.py` -> passed.
- Adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v307_governance_baseline.py tests\test_v308_local_audit_log.py tests\test_v309_permission_preflight.py tests\test_v302_client_manifest.py tests\test_v28_capabilities_schema_contract.py` -> 23 passed.
- Manual smoke:
  - `threadvault governance permission check --operation export_archive --role reviewer --json` -> passed.
  - `threadvault governance permission check --operation read_raw_transcript --role reader --config TEMP_CONFIG --audit-log TEMP_LOG --actor reader --target-type session --target-id sess-current --json` -> passed.
  - `threadvault governance audit list --log TEMP_LOG --json` -> passed.
  - `threadvault schemas list --json` -> passed.
  - `threadvault capabilities --json` -> passed.
  - `Test-Path deep-research-report.md` -> `False`.
- Final validation:
  - `py -3.12 -m ruff check .` -> passed.
  - `py -3.12 -m pytest` -> 252 passed.

## Final Result

ThreadVault v3 Phase 09 is accepted. Governance now has explicit permission preflight checks with optional audit logging,
while existing local CLI commands remain unenforced by default.

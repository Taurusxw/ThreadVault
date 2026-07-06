# v3 Phase 08 Acceptance: Local Audit Log Workflow

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

The phase is accepted when validation proves:

- `threadvault governance audit append --json` emits `governance_audit_append`.
- `threadvault governance audit list --json` emits `governance_audit_list`.
- Appending creates and extends a local JSONL file.
- Listing tolerates malformed lines and reports warnings.
- Audit workflow remains local-only and does not require a server.
- `governance_audit_append` and `governance_audit_list` exist in the schema registry and packaged schema artifacts.
- Capabilities and robot docs discovery advertise the workflow.
- `deep-research-report.md` remains absent.

## Validation Commands

Final validation included:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v308_local_audit_log.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v308_local_audit_log.py
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault governance audit append --log TEMP_LOG --operation export_archive --actor local --status ok --target-type session --target-id sess-current --json
threadvault governance audit list --log TEMP_LOG --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

## Validation Results

- `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_audit_append.schema.json` and `governance_audit_list.schema.json`.
- `py -3.12 -m pytest tests\test_v308_local_audit_log.py` -> 4 passed.
- `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v308_local_audit_log.py` -> passed after wrapping long lines.
- Adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v307_governance_baseline.py tests\test_v308_local_audit_log.py tests\test_v302_client_manifest.py tests\test_v28_capabilities_schema_contract.py` -> 18 passed.
- Manual smoke:
  - `threadvault governance audit append --log TEMP_LOG --operation export_archive --actor local --status ok --target-type session --target-id sess-current --json` -> passed.
  - `threadvault governance audit list --log TEMP_LOG --json` -> passed.
  - `threadvault governance status --json` -> passed.
  - `threadvault schemas list --json` -> passed.
  - `threadvault capabilities --json` -> passed.
  - `Test-Path deep-research-report.md` -> `False`.
- Final validation:
  - `py -3.12 -m ruff check .` -> passed.
  - `py -3.12 -m pytest` -> 247 passed.

## Final Result

ThreadVault v3 Phase 08 is accepted. Governance now has explicit local append/list audit workflows with JSON Schema
contracts and discovery surfaces, while server mode, cloud sync, permission enforcement, and automatic command
instrumentation remain deferred.

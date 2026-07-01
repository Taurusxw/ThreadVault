# v3 Phase 13 Acceptance: Export/Backup Governance Preflight

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

The phase is accepted when validation proves:

- `threadvault governance preflight export-backup --command COMMAND --role ROLE --json` emits
  `governance_export_backup_preflight`.
- The payload validates against the generated schema.
- Export/backup commands are recognized and mapped to policy.
- Out-of-scope commands return structured diagnostics.
- The command remains preflight-only and does not execute business commands.
- Optional `--audit-log` records a preflight audit entry.
- Capabilities, robot docs, schema registry, and packaged schema artifacts advertise the workflow.
- Existing business commands remain unmodified and unenforced.
- `deep-research-report.md` remains absent.

## Validation Commands

Final validation should include:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v313_export_backup_governance_preflight.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v313_export_backup_governance_preflight.py
py -3.12 -m pytest tests\test_v311_governance_enforcement_dry_run.py tests\test_v312_governance_policy_readiness.py tests\test_v313_export_backup_governance_preflight.py tests\test_v28_capabilities_schema_contract.py
threadvault governance preflight export-backup --command "threadvault export" --role reviewer --json
threadvault governance preflight export-backup --command "threadvault backup" --role reader --json
threadvault schemas list --json
threadvault capabilities --json
py -3.12 -m ruff check .
py -3.12 -m pytest
Test-Path deep-research-report.md
```

## Final Result

Accepted.

Phase 13 adds `threadvault governance preflight export-backup --json` as an explicit governance preflight for export and
backup command families. It reports permission, dry-run enforcement, privacy, audit, and execution expectations without
running the checked business command.

Validation completed:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v313_export_backup_governance_preflight.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v313_export_backup_governance_preflight.py
py -3.12 -m pytest tests\test_v311_governance_enforcement_dry_run.py tests\test_v312_governance_policy_readiness.py tests\test_v313_export_backup_governance_preflight.py tests\test_v310_governance_enforcement_gaps.py tests\test_v309_permission_preflight.py tests\test_v28_capabilities_schema_contract.py
threadvault governance preflight export-backup --command "threadvault export" --role reviewer --json
threadvault governance preflight export-backup --command "threadvault backup" --role reader --json
threadvault schemas list --json
threadvault capabilities --json
py -3.12 -m ruff check .
py -3.12 -m pytest
Test-Path deep-research-report.md
```

Observed results:

- Focused Phase 13 tests: 6 passed.
- Adjacent governance/discovery tests: 31 passed.
- Full test suite: 273 passed.
- Full ruff check: passed.
- `docs/schemas/governance_export_backup_preflight.schema.json` was generated.
- `governance_export_backup_preflight` appears in schema discovery.
- Capabilities advertise `governance preflight export-backup` and `governance_export_backup_preflight`.
- `threadvault governance preflight export-backup --command "threadvault export" --role reviewer --json` returned
  `preflight_status = would_allow`, `business_command_executed = false`, and `files_written = false`.
- `threadvault governance preflight export-backup --command "threadvault backup" --role reader --json` returned
  `preflight_status = would_block`, `business_command_executed = false`, and `backup_created = false`.
- `Test-Path deep-research-report.md` returned `False`.

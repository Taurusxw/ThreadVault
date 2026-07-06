# v3 Phase 11 Acceptance: Governance Enforcement Dry Run

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

The phase is accepted when validation proves:

- `threadvault governance enforcement check --command COMMAND --role ROLE --json` emits
  `governance_enforcement_check`.
- The payload validates against the generated schema.
- Known commands use the Phase 10 command inventory.
- Unknown commands return structured diagnostics.
- The command remains dry-run only and does not enforce existing business commands.
- Optional `--audit-log` records a dry-run audit entry.
- Capabilities, robot docs, schema registry, and packaged schema artifacts advertise the workflow.
- `deep-research-report.md` remains absent.

## Validation Commands

Final validation should include:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v311_governance_enforcement_dry_run.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v311_governance_enforcement_dry_run.py
py -3.12 -m pytest tests\test_v309_permission_preflight.py tests\test_v310_governance_enforcement_gaps.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v28_capabilities_schema_contract.py
threadvault governance enforcement check --command "threadvault export" --role reviewer --json
threadvault governance enforcement check --command "threadvault client session" --role reader --json
threadvault schemas list --json
threadvault capabilities --json
py -3.12 -m ruff check .
py -3.12 -m pytest
Test-Path deep-research-report.md
```

## Final Result

Accepted.

Phase 11 adds `threadvault governance enforcement check --json` as a dry-run governance enforcement preview. It resolves
a command through the Phase 10 inventory, reuses Phase 09 permission logic, and reports whether the command would be
allowed or blocked if future enforcement were wired in. It does not execute or enforce existing business commands.

Validation completed:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v311_governance_enforcement_dry_run.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v311_governance_enforcement_dry_run.py
py -3.12 -m pytest tests\test_v309_permission_preflight.py tests\test_v310_governance_enforcement_gaps.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v307_governance_baseline.py tests\test_v308_local_audit_log.py tests\test_v28_capabilities_schema_contract.py
threadvault governance enforcement check --command "threadvault export" --role reviewer --json
threadvault governance enforcement check --command "threadvault client session" --role reader --json
threadvault schemas list --json
threadvault capabilities --json
py -3.12 -m ruff check .
py -3.12 -m pytest
Test-Path deep-research-report.md
```

Observed results:

- Focused Phase 11 tests: 6 passed.
- Adjacent governance/discovery tests: 29 passed.
- Full test suite: 262 passed.
- Full ruff check: passed.
- `docs/schemas/governance_enforcement_check.schema.json` was generated.
- `governance_enforcement_check` appears in schema discovery.
- Capabilities advertise `governance enforcement check` and `governance_enforcement_dry_run`.
- `threadvault governance enforcement check --command "threadvault export" --role reviewer --json` returned
  `status = would_allow` and `business_command_executed = false`.
- `threadvault governance enforcement check --command "threadvault client session" --role reader --json` returned
  `status = would_block` and `business_command_executed = false`.
- `Test-Path deep-research-report.md` returned `False`.

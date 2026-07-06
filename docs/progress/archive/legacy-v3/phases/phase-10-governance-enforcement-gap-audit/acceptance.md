# v3 Phase 10 Acceptance: Governance Enforcement Gap Audit

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

The phase is accepted when validation proves:

- `threadvault governance enforcement gaps --json` emits `governance_enforcement_gaps`.
- Gap records cover the current command surface that matters for v3 governance.
- Current enforcement and automatic audit state remain disabled.
- `governance_enforcement_gaps` exists in the schema registry and packaged schema artifacts.
- Capabilities and robot docs discovery advertise the workflow.
- `gap-audit.md` exists and records the conclusions.
- `deep-research-report.md` remains absent.

## Validation Commands

Final validation should include:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v310_governance_enforcement_gaps.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v310_governance_enforcement_gaps.py
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault governance enforcement gaps --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

## Final Result

Accepted.

Phase 10 adds `threadvault governance enforcement gaps --json` as a planning-only governance inventory. It emits
`governance_enforcement_gaps.v1`, records 16 current command surfaces, and reports that permission enforcement,
automatic preflight, and automatic audit remain disabled for existing commands.

Validation completed:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v310_governance_enforcement_gaps.py
py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v310_governance_enforcement_gaps.py
py -3.12 -m pytest tests\test_v307_governance_baseline.py tests\test_v308_local_audit_log.py tests\test_v309_permission_preflight.py tests\test_v310_governance_enforcement_gaps.py tests\test_v302_client_manifest.py tests\test_v28_capabilities_schema_contract.py
threadvault governance enforcement gaps --json
threadvault schemas list --json
threadvault capabilities --json
py -3.12 -m ruff check .
py -3.12 -m pytest
Test-Path deep-research-report.md
```

Observed results:

- Focused Phase 10 tests: 4 passed.
- Adjacent governance/client/discovery tests: 27 passed.
- Full test suite: 256 passed.
- Full ruff check: passed.
- `docs/schemas/governance_enforcement_gaps.schema.json` was generated.
- `governance_enforcement_gaps` appears in schema discovery.
- Capabilities advertise `governance enforcement gaps`.
- `Test-Path deep-research-report.md` returned `False`.

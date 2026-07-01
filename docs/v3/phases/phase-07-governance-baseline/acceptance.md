# v3 Phase 07 Acceptance: Governance Baseline

## Status

Accepted on 2026-07-01.

## Acceptance Evidence

The phase is accepted when validation proves:

- `threadvault governance status --json` emits `governance_status`.
- Default governance is disabled and local-first.
- Config opt-in through `[governance] enabled = true` is visible.
- Server, cloud sync, and external model calls remain disabled by default.
- Access levels, roles, sensitive operations, and audit requirements are machine-readable.
- `governance_status` exists in the schema registry and packaged schema artifacts.
- Capabilities, robot docs, and client manifest discovery advertise the governance baseline.
- `deep-research-report.md` remains absent.

## Validation Commands

Final validation included:

```powershell
threadvault schemas write --out docs\schemas --json
py -3.12 -m pytest tests\test_v307_governance_baseline.py
py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v307_governance_baseline.py
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault governance status --json
threadvault governance status --config TEMP_CONFIG --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

## Validation Results

- `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_status.schema.json`.
- `py -3.12 -m pytest tests\test_v307_governance_baseline.py` -> 5 passed.
- `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v307_governance_baseline.py` -> passed after removing one unused import.
- Adjacent config/client validation:
  - `py -3.12 -m pytest tests\test_v12_app_config.py tests\test_v13_config_cli.py tests\test_v14_config_init.py tests\test_v302_client_manifest.py tests\test_v307_governance_baseline.py` -> 29 passed.
- Manual smoke:
  - `threadvault governance status --json` -> passed.
  - `threadvault governance status --config TEMP_CONFIG --json` -> passed with `[governance] enabled = true`.
  - `threadvault config show --config TEMP_CONFIG --json` -> passed and exposed governance config summary.
  - `threadvault schemas list --json` -> passed.
  - `threadvault capabilities --json` -> passed.
  - `Test-Path deep-research-report.md` -> `False`.
- Final validation:
  - `py -3.12 -m ruff check .` -> passed.
  - `py -3.12 -m pytest` -> 243 passed.

## Final Result

ThreadVault v3 Phase 07 is accepted. Governance now has a stable opt-in status payload, role/access vocabulary, and
discovery surface without requiring a server, enabling cloud sync, enforcing permissions, or changing local CLI defaults.

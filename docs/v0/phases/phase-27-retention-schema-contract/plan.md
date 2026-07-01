# Phase 27 / v0.27: Retention Schema Contract

## Goal

Tighten JSON schema contracts for retention prune outputs.

Audit, backup, and restore history pruning now share a retention keep-resolution helper. Runtime JSON always reports `keep_source` as either `cli` or `config`, but the schemas are slightly inconsistent: audit has an enum but did not require the field, while backup and restore require the field but allow any string.

## Scope

- Add a shared internal schema snippet for retention `keep_source`.
- Require `keep_source` in `audit_history_prune`.
- Restrict `keep_source` to `cli|config` in `backup_history_prune` and `restore_history_prune`.
- Add schema contract tests for all three prune schemas.
- Refresh packaged schemas.
- Do not change CLI behavior, database behavior, or prune implementations.

## Existing Project Lessons

- Reuse v0.5/v0.6 machine-friendly JSON contract work.
- Follow CASS-style stable robot output: schemas should be precise enough for agents to validate branch behavior.
- Follow `codebase-design`: keep the schema contract detail in the schema module instead of spreading assertions across CLI code.

## Tasks

- Update `threadvault.schemas.contract_schemas()`.
- Add tests that inspect schemas and validate both accepted and rejected `keep_source` values.
- Refresh `docs/schemas/*.schema.json`.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest tests\test_v27_retention_schema_contract.py tests\test_v06_schemas.py tests\test_v11_audit_config.py tests\test_v19_backup_config.py tests\test_v25_restore_history_config.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault schemas show audit_history_prune --json
threadvault schemas show backup_history_prune --json
threadvault schemas show restore_history_prune --json
```

## Assumptions

- Tightening the schema is compatible because runtime output already emits only `cli` or `config`.
- `keep_source` is now part of the stable retention JSON contract.
- This phase should not add new commands or storage changes.


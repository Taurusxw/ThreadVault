# Phase 29 / v0.29: Doctor Schema Contract

## Goal

Tighten the `doctor --json` schema contract so it matches the runtime diagnostic payload.

`doctor --json` is ThreadVault's main local health entrypoint. Runtime already emits schema version, schema objects, parse health, maintenance suggestions, platform/runtime metadata, Codex home discovery, JSONL count, and optional Codex state diagnostics. The schema still only requires the early `ok/checks/stats` fields.

## Scope

- Require stable doctor fields already emitted at runtime:
  - `parse_health`
  - `schema_version`
  - `schema_objects`
  - `maintenance_suggestions`
  - `python`
  - `platform`
  - `db_path`
  - `codex_home`
  - `session_dirs`
  - `missing_session_dirs`
  - `jsonl_files`
  - `codex_state`
- Add precise-enough schema properties for these fields.
- Add tests that validate real `threadvault doctor --json` output against the doctor schema.
- Refresh packaged schemas.
- Do not change doctor runtime behavior, database schema, or Codex home scanning behavior.

## Existing Project Lessons

- Reuse v0.5 doctor maintenance fields.
- Reuse v0.6 JSON Schema and `validate-json` infrastructure.
- Follow CASS-style health/doctor entrypoints: diagnostic outputs should be machine-verifiable.
- Follow `codebase-design`: keep contract details in `schemas.py`, not scattered through CLI code.

## Tasks

- Update `threadvault.schemas.contract_schemas()["doctor"]`.
- Add v0.29 contract tests for required fields and real doctor output validation.
- Refresh `docs/schemas/doctor.schema.json`.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest tests\test_v29_doctor_schema_contract.py tests\test_v05_contracts.py tests\test_v06_schemas.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault doctor --db <tmp.db> --codex-home tests/fixtures/codex_home --json
threadvault schemas show doctor --json
threadvault validate-json --schema doctor --input <doctor.json> --json
```

## Assumptions

- Tightening required fields is compatible because runtime doctor output already includes them.
- `codex_state` may contain success or warning details, but the top-level key is stable.
- This phase does not update the DOCX; Markdown remains the source of phase traceability.


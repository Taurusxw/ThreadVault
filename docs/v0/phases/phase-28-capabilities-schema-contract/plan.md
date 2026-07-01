# Phase 28 / v0.28: Capabilities Schema Contract

## Goal

Tighten the `capabilities --json` schema contract so it matches the runtime output and README promise.

`capabilities --json` is a primary agent entrypoint. Runtime output includes `stability_policy`, `json_outputs`, `export_formats`, `export_profiles`, `privacy_modes`, `search_fields`, and `feature_flags`, but the schema currently only requires the oldest core fields. v0.28 makes the contract explicit for machine callers.

## Scope

- Require stable capabilities fields already emitted at runtime:
  - `stability_policy`
  - `json_outputs`
  - `export_formats`
  - `export_profiles`
  - `privacy_modes`
  - `search_fields`
  - `feature_flags`
- Add schema properties for fields missing from the capabilities schema.
- Update `robot-docs schemas --json` capability field summary to include the same fields.
- Add contract tests validating current `threadvault capabilities --json` against the packaged schema.
- Refresh packaged schemas.
- Do not change command behavior or add new commands.

## Existing Project Lessons

- Reuse v0.5 machine-friendly CLI contract work.
- Reuse v0.6 JSON schema commands and validation instead of adding another contract format.
- Follow CASS-style agent entrypoints: a capabilities command should be complete enough for agents to discover supported formats and output contracts.
- Follow `codebase-design`: keep contract details in `schemas.py` and `store.robot_schemas()` rather than duplicating them in command code.

## Tasks

- Update `threadvault.schemas.contract_schemas()["capabilities"]`.
- Update `threadvault.store.robot_schemas()["capabilities"]`.
- Add tests for required fields and validate real capabilities output.
- Refresh `docs/schemas/capabilities.schema.json`.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest tests\test_v28_capabilities_schema_contract.py tests\test_v05_contracts.py tests\test_v06_schemas.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault capabilities --json
threadvault schemas show capabilities --json
threadvault robot-docs schemas --json
```

## Assumptions

- Tightening required fields is compatible because runtime output already includes them.
- JSON output remains append-only; adding required schema coverage for existing fields does not remove compatibility for real ThreadVault output.
- This phase does not update the DOCX; Markdown remains the source of phase traceability.


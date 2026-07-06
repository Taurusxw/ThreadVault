# Phase 06 / v0.6: Schema Validation Contracts

## Goal

Turn the v0.5 agent JSON contract from runtime documentation into reusable schema artifacts and a CLI validation workflow.

## Scope

- Keep ThreadVault local-first and privacy-first.
- Keep the work in the CLI/data layer.
- Do not add Web UI, TUI, MCP server, vector search, cloud sync, external LLM summaries, or team features.

## Tasks

- Add a schema module that exposes named JSON Schemas from the existing robot contract.
- Add mature `jsonschema` validation instead of hand-rolling schema checks.
- Add CLI commands:
  - `threadvault schemas list --json`
  - `threadvault schemas show NAME --json`
  - `threadvault schemas write --out docs/schemas --json`
  - `threadvault validate-json --schema NAME --input payload.json --json`
- Add packaged schema files under `docs/schemas/` so agents can consume contracts without running ThreadVault.
- Update `capabilities --json` and `robot-docs guide` to advertise schema commands.
- Add tests for schema list/show/write and validation pass/fail behavior.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault --help
threadvault schemas list --json
threadvault schemas show search_minimal --json
threadvault schemas write --out docs/schemas --json
threadvault search pytest --db <tmp.db> --json --fields minimal > <tmp-json>
threadvault validate-json --schema search_minimal --input <tmp-json> --json
```

## Assumptions

- JSON Schema draft 2020-12 is sufficient for v0.6 contract validation.
- `jsonschema` is acceptable as a runtime dependency because validation is a public CLI feature.
- Existing `robot-docs schemas --json` remains backward compatible and continues to include legacy explanatory keys.


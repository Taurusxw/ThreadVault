# Phase 06 / v1.4 Acceptance: v1 Smoke And Local Audit

## Goal

Run a final v1 acceptance phase over fixture data and a local audit workflow. This phase should prove that ThreadVault v1 has reached the documented personal knowledge layer outcome: automatic ingest signaling, explicit queue processing, batch export manifests, Obsidian/Markdown vault output, and Codex Skill candidate output.

This phase is primarily acceptance hardening. It should avoid adding new product surface unless a gap blocks v1 acceptance.

## Source Context

Required context read before this plan:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v1-personal-knowledge-layer.md`
- `docs/v1/README.md`
- `docs/v1/phases/phase-01-ingestion-automation-queue/acceptance.md`
- `docs/v1/phases/phase-02-codex-hook-adapter/acceptance.md`
- `docs/v1/phases/phase-03-export-target-manifest/acceptance.md`
- `docs/v1/phases/phase-04-obsidian-markdown-vault/acceptance.md`
- `docs/v1/phases/phase-05-codex-skill-target/acceptance.md`
- `docs/development-progress.md`
- existing v1 tests:
  - `tests/test_v101_ingestion_queue.py`
  - `tests/test_v102_codex_hook_adapter.py`
  - `tests/test_v103_export_target_manifest.py`
  - `tests/test_v104_obsidian_vault_target.py`
  - `tests/test_v105_codex_skill_target.py`

## Product Boundary

In scope:

- A final v1 acceptance document.
- One focused v1 end-to-end smoke test over fixture data.
- Verification that the v1 workflow is recoverable from docs:
  - plan files;
  - acceptance files;
  - development progress;
  - usage manual.
- Verification that `deep-research-report.md` remains retired.
- Verification that root `README.md` remains a short entrypoint.
- Final regression and CLI smoke commands.

Out of scope:

- New export target profiles.
- Vector search, MCP, REST, desktop, IDE, team, cloud, or external LLM features.
- Automatic Skill installation.
- DOCX synchronization.
- Version bump unless separately requested.

## Acceptance Workflow

The end-to-end v1 smoke should prove:

1. A Hook-like payload can enqueue ingestion work.
2. The queue can be processed explicitly with `--apply`.
3. Imported fixture sessions are searchable/listable through existing v0 interfaces.
4. `export-target markdown` writes manifest-bearing Markdown output.
5. `export-target obsidian` writes index/session/evidence pages.
6. `export-target skill` writes `SKILL.md` and references.
7. Capabilities advertise:
   - `ingestion_queue`
   - `codex_hook_adapter`
   - `export_target_manifest`
   - `obsidian_vault_target`
   - `codex_skill_target`
8. Schema registry includes:
   - `ingestion_enqueue`
   - `ingestion_queue_list`
   - `ingestion_process`
   - `codex_hook_ingest`
   - `codex_hook_config`
   - `export_target_manifest`
9. `deep-research-report.md` is absent.

## Documentation Updates

Create/update:

- `docs/v1/phases/phase-06-v1-acceptance-smoke/plan.md`
- `docs/v1/phases/phase-06-v1-acceptance-smoke/v1-acceptance.md`
- `docs/v1/README.md`
- `docs/development-progress.md`

Update `docs/THREADVAULT_USAGE_MANUAL.md` only if the final acceptance reveals missing or misleading v1 usage coverage.

Do not recreate or update `deep-research-report.md`. Do not modify the root DOCX.

## Test Plan

Add focused tests, likely in `tests/test_v106_v1_acceptance.py`:

- `test_v1_end_to_end_personal_knowledge_layer_smoke`
  - create temp db;
  - enqueue through `codex-hook ingest` using fixture transcript path;
  - process queue with `ingest-queue process --apply`;
  - assert imported sessions/events;
  - run all three export targets into temp output dirs;
  - validate each manifest against `export_target_manifest`;
  - assert expected files exist.
- `test_v1_capabilities_and_schema_discovery`
  - assert v1 feature flags and schema names are present.
- `test_v1_docs_and_retired_report_policy`
  - assert Phase 01-06 plan/acceptance docs exist;
  - assert `deep-research-report.md` is absent.

Regression checks:

```powershell
py -3.12 -m pytest tests\test_v106_v1_acceptance.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault capabilities --json
threadvault schemas list --json
threadvault export-target --help
threadvault ingest-queue --help
threadvault codex-hook --help
Test-Path deep-research-report.md
```

## Acceptance Criteria

- v1 end-to-end fixture smoke passes.
- Full pytest passes.
- Ruff passes.
- CLI smoke checks pass.
- v1 docs contain plan and acceptance records for every v1 phase.
- `docs/development-progress.md` records final v1 acceptance.
- No root `deep-research-report.md` is recreated.
- v1 can be considered complete against the roadmap boundary:
  - automatic ingest signaling;
  - explicit queue processing;
  - durable Markdown/Obsidian/Skill knowledge outputs;
  - local-first/privacy-first default.

## Open Assumptions

- Fixture data is sufficient for final automated v1 acceptance.
- An anonymized real local audit workflow can remain documented as a manual follow-up unless the user explicitly provides local corpus constraints for this acceptance phase.
- Package version remains `0.31.0` unless a separate versioning phase is requested.

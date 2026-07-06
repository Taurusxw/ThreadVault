# Phase 03 / v1.1 Foundation: Export Target Manifest

## Goal

Create the first v1 `Export Target` module: a small interface for batch session/project export that writes a stable manifest describing archive selection, target profile, written files, skipped items, privacy findings, and evidence links.

This phase begins the v1 knowledge-output line. It does not yet implement the full Obsidian vault layout or Codex Skill generation. Instead, it creates the manifest-bearing export seam that those later targets can reuse.

## Source Context

Required context read before this plan:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v1-personal-knowledge-layer.md`
- `docs/v1/README.md`
- `docs/v1/phases/phase-01-ingestion-automation-queue/plan.md`
- `docs/v1/phases/phase-02-codex-hook-adapter/plan.md`
- `docs/v0/README.md`
- `docs/development-progress.md`
- `src/threadvault/exporter.py`
- `src/threadvault/store.py`
- `src/threadvault/cli.py`
- `src/threadvault/database.py`
- `src/threadvault/schemas.py`
- `codebase-design` skill guidance for deep modules

## Product Boundary

v1 centers on automatic ingest plus durable knowledge output. Phase 01 and Phase 02 established automatic ingest triggers. Phase 03 starts durable output by making batch exports observable and machine-readable.

In scope:

- A new `Export Target` module.
- Batch export by selected sessions.
- Batch export by project/cwd.
- A `markdown` target profile using existing session Markdown export.
- A manifest file written beside batch exports.
- JSON output describing the same manifest.
- Privacy findings summarized per exported item.
- Evidence event IDs from local summaries.
- Tests proving batch export, manifest shape, schema validation, and docs traceability.

Out of scope:

- Obsidian-specific vault folders, backlinks, tags, or daily notes.
- Codex Skill output.
- HTML export.
- Vector search or semantic ranking.
- External LLM summaries.
- Cloud sync, server mode, team permissions, desktop UI.
- Replacing the existing `threadvault export` command.

## Architecture Decision

### Module

Add a new `threadvault.export_targets` module.

External interface:

- `ExportTargetRequest`
- `export_target(conn, request) -> dict`

The module should hide:

- archive selection details;
- per-session export loops;
- manifest construction;
- summary evidence extraction;
- privacy finding aggregation;
- skipped item reporting;
- stable path layout for this target profile.

### Seam

The seam lives between archive selection and target-specific file writing.

Callers should say what they want exported, not how to loop through sessions, how to call existing exporter helpers, how to summarize evidence, or how to construct the manifest. Later Obsidian and Skill adapters should sit behind the same seam rather than becoming more `if/elif` branches in the top-level CLI.

### First Target Profile

Support `profile = "markdown"` in this phase.

Behavior:

- Session exports are written under `sessions/`.
- A project index is written when exporting by project.
- A `threadvault-export-manifest.json` file is written at the target root.
- The manifest uses relative paths from the target root for written files.

Future target profiles such as `obsidian` and `skill` can reuse the same request/manifest shape with target-specific writers.

## CLI Shape

Add a new Typer group:

```powershell
threadvault export-target markdown --session SESSION_ID --out out --json
threadvault export-target markdown --session A --session B --out out --json
threadvault export-target markdown --project E:\Codex\ThreadVault --out out --json
```

Options:

- `--session` repeatable.
- `--project` single cwd selector.
- `--out` target directory.
- `--privacy-mode warn|redact|fail`.
- `--privacy-config PATH`.
- `--json`.

Selection rules:

- At least one `--session` or `--project` is required.
- `--session` and `--project` may both be provided; project sessions should be deduplicated against explicit session IDs.
- Unknown explicit sessions are reported as skipped.
- Unknown/empty project selection should succeed with `exported_count = 0` and a skipped/project-empty warning.

## Manifest Shape

Write `threadvault-export-manifest.json` with fields:

- `manifest_version`
- `target_profile`
- `generated_at`
- `root`
- `selection`
- `files`
- `skipped`
- `privacy`
- `evidence`

File entries:

- `kind`
- `session_id`
- `path`
- `format`
- `privacy_findings_count`
- `evidence_event_ids`

Privacy summary:

- `mode`
- `findings_count`
- `effective_findings_count`
- `by_severity`
- `by_kind`

Evidence summary:

- `event_ids`
- `sessions_with_evidence`

## JSON Contract

Add schema:

- `export_target_manifest`

Required top-level fields:

- `manifest_version`
- `target_profile`
- `generated_at`
- `root`
- `selection`
- `files`
- `skipped`
- `privacy`
- `evidence`

The CLI JSON output should be the manifest object itself, so saving the command output and validating the manifest file use the same schema.

## Capabilities

Update `capabilities()` and `robot_schemas()` so agents can discover:

- the new `export-target` command group;
- `export-target markdown` JSON output;
- the new `export_target_manifest` schema;
- a feature flag such as `export_target_manifest: true`.

Do not change package version in this phase.

## Documentation Updates

Create/update:

- `docs/v1/README.md`
- `docs/v1/phases/phase-03-export-target-manifest/plan.md`
- `docs/v1/phases/phase-03-export-target-manifest/acceptance.md`
- `docs/development-progress.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`

Do not recreate or update `deep-research-report.md`. Do not modify the root DOCX.

## Test Plan

Add focused tests, likely in `tests/test_v103_export_target_manifest.py`:

- export one explicit session and write manifest;
- export multiple sessions with `--session` repeated;
- export project sessions and include a project index;
- unknown explicit session is skipped and does not fail the whole batch;
- manifest JSON validates against `export_target_manifest`;
- capabilities and schema registry include the new export target entries;
- traceability docs exist.

Regression checks:

```powershell
py -3.12 -m pytest tests\test_v103_export_target_manifest.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault export-target --help
threadvault export-target markdown --help
threadvault capabilities --json
threadvault schemas list --json
```

## Acceptance Criteria

- A user can batch export selected sessions with one command.
- A user can batch export project sessions with one command.
- Every batch export writes a stable `threadvault-export-manifest.json`.
- The manifest records written files, skipped items, privacy summaries, and evidence event IDs.
- Existing `threadvault export` behavior remains compatible.
- New JSON output is schema-valid.
- Documentation makes the phase recoverable from `docs/README.md`, `docs/roadmap/`, `docs/v1/`, and `docs/development-progress.md`.

## Open Assumptions

- The first target profile is named `markdown`, not `obsidian`, because Obsidian-specific layout/linking is a later target profile.
- Manifest files may include local output paths and local project cwd metadata. They should be treated as local/private metadata.
- `privacy_mode = fail` should skip writing high-risk session files but still write a manifest explaining the skipped item.

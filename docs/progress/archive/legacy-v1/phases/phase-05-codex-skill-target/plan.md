# Phase 05 / v1.3 Foundation: Codex Skill Target

## Goal

Add a Codex Skill export target that packages selected ThreadVault summaries and evidence references into a reviewable Skill candidate folder. The target should emit a valid `SKILL.md`, a small `references/` set, and the existing `threadvault-export-manifest.json` so the generated skill material remains traceable to local ThreadVault sessions and event IDs.

This phase completes the v1 knowledge-output line after the Markdown manifest and Obsidian vault foundations. It does not install the generated skill into Codex automatically; it creates local candidate material that the user can inspect, edit, and install later.

## Source Context

Required context read before this plan:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v1-personal-knowledge-layer.md`
- `docs/v1/README.md`
- `docs/v1/phases/phase-03-export-target-manifest/plan.md`
- `docs/v1/phases/phase-04-obsidian-markdown-vault/plan.md`
- `docs/v1/phases/phase-04-obsidian-markdown-vault/acceptance.md`
- `docs/v0/research/codex-session-archive-research.md`
- `docs/development-progress.md`
- `src/threadvault/export_targets.py`
- `src/threadvault/store.py`
- `src/threadvault/cli.py`
- `src/threadvault/schemas.py`
- `src/threadvault/summarizer.py`
- `skill-creator` guidance for Skill structure and concise `SKILL.md` design
- `codebase-design` guidance for deep modules

## Research Carry-Forward

The v0 research report identified Codex Skill output as a natural extension of Markdown-first exports: Skills are centered on `SKILL.md` plus optional `references/`, scripts, and assets. It also warned that existing one-off exporters do not solve reliable parsing, privacy, evidence, and long-term archive traceability. Phase 05 therefore builds on the normalized ThreadVault archive and the `Export Target` module rather than copying external exporters.

Carry-forward decisions:

- Generate Skill material from summaries and selected evidence, not raw transcripts by default.
- Keep `SKILL.md` concise and procedural.
- Put detailed archive material in `references/`.
- Keep event IDs visible for traceability.
- Do not copy external project source code.
- Do not auto-install into `$CODEX_HOME/skills`.

## Product Boundary

In scope:

- A new `skill` export target profile inside `threadvault.export_targets`.
- A new CLI command:

```powershell
threadvault export-target skill --session SESSION_ID --out out --skill-name project-memory --json
threadvault export-target skill --project E:\Codex\ThreadVault --out out --skill-name threadvault-memory --json
```

- A generated Skill candidate layout:

```text
out/
  SKILL.md
  references/
    sessions.md
    evidence.md
  threadvault-export-manifest.json
```

- Required frontmatter in `SKILL.md`:
  - `name`
  - `description`
- References that include selected session summaries and high-value evidence events.
- Manifest entries for `SKILL.md`, `references/sessions.md`, and `references/evidence.md`.
- Privacy modes equivalent to other export targets.
- Tests for skill folder shape, frontmatter, references, manifest, project export, unknown sessions, privacy fail behavior, capabilities, schemas, and docs traceability.

Out of scope:

- Installing or updating skills under `$CODEX_HOME/skills`.
- Running `skill-creator` initialization scripts.
- Generating `agents/openai.yaml`.
- Bundling scripts or assets.
- External LLM rewriting of Skill instructions.
- Full raw transcript dumps in references.
- Vector search, MCP, REST, desktop, IDE extension, team, or cloud features.

## Architecture Decision

### Module

Extend `threadvault.export_targets` with `profile="skill"`.

External interface remains:

- `ExportTargetRequest`
- `export_target(conn, request) -> dict`

Add request fields that are optional and only meaningful for `profile="skill"`:

- `skill_name: str | None`
- `skill_description: str | None`

The module owns:

- skill-name normalization;
- target file layout;
- concise `SKILL.md` generation;
- reference generation;
- privacy handling;
- manifest construction.

### Seam

The seam stays at the `Export Target` module. CLI should only pass selection, target root, profile, privacy policy, and optional Skill metadata. It should not assemble frontmatter, references, evidence lists, or manifest entries.

### Skill Name Policy

Normalize skill names according to `skill-creator` constraints:

- lowercase letters, digits, and hyphens only;
- collapse repeated separators;
- trim leading/trailing hyphens;
- cap at 63 characters;
- default to `threadvault-skill` if no usable name remains.

## Skill Candidate Layout

### `SKILL.md`

Required shape:

```markdown
---
name: threadvault-memory
description: Use this skill when ...
---

# ThreadVault Memory

## Workflow

...

## References

- Read `references/sessions.md` for session summaries.
- Read `references/evidence.md` for event-backed evidence.
```

Content requirements:

- Keep concise.
- Explain that references are local ThreadVault exports.
- Tell agents to use evidence event IDs when relying on claims.
- Tell agents to avoid exposing private paths or secrets without user review.
- Point to `references/sessions.md` and `references/evidence.md`.

### `references/sessions.md`

Required content:

- H1: `# ThreadVault Session Summaries`
- generated timestamp
- selected project if any
- selected sessions
- one section per exported session with:
  - topic
  - session id
  - project cwd
  - user goal
  - key steps
  - key commands
  - files
  - problems
  - next steps
  - evidence event IDs

### `references/evidence.md`

Required content:

- H1: `# ThreadVault Evidence References`
- generated timestamp
- one section per session
- event sections for summary-referenced evidence IDs
- event metadata and trimmed text

The evidence reference should not include every raw event by default. It should carry enough context for the generated Skill to be useful without becoming a raw transcript dump.

## Manifest Shape

Reuse `export_target_manifest`.

For `skill`, file entries should use:

- `kind: skill_file`
- `kind: skill_reference`
- `path`
- `format: md`
- `session_id: null`
- `privacy_findings_count`
- `evidence_event_ids`

Top-level `target_profile` must be `skill`.

The manifest remains the machine-readable contract. `SKILL.md` is a human/agent-facing artifact.

## CLI Shape

Add command:

```powershell
threadvault export-target skill --session SESSION_ID --out out --skill-name NAME --json
```

Options:

- `--session` repeatable.
- `--project` single cwd selector.
- `--out` target directory.
- `--skill-name` optional.
- `--skill-description` optional.
- `--privacy-mode warn|redact|fail`.
- `--privacy-config PATH`.
- `--json`.

Selection rules remain the same as Phase 03 and Phase 04:

- At least one `--session` or `--project` is required.
- Explicit sessions and project-selected sessions are deduplicated.
- Unknown explicit sessions are reported as skipped.
- Empty project selection succeeds with an explanatory skipped item.

## Privacy Behavior

- `warn`: write files and record findings.
- `redact`: write redacted `SKILL.md` and reference files.
- `fail`: skip high-risk session-derived reference content while still writing a minimal `SKILL.md`, references, and manifest that explain skipped items.

The generated skill candidate can contain local project paths, session IDs, and excerpts. Treat it as local/private until reviewed.

## Capabilities And Agent Discovery

Update:

- `capabilities()["json_outputs"]` to include `export-target skill`.
- `capabilities()["feature_flags"]` to include `codex_skill_target: true`.
- `robot_guide()["recommended_commands"]` with a skill target example.
- `robot_schemas()["export_target_manifest"]` if useful to mention Skill file kinds.

Do not change:

- package version;
- database schema version;
- JSON contract version;
- existing `export-target markdown` behavior;
- existing `export-target obsidian` behavior;
- existing `threadvault export` behavior.

## Documentation Updates

Create/update:

- `docs/v1/README.md`
- `docs/v1/phases/phase-05-codex-skill-target/plan.md`
- `docs/v1/phases/phase-05-codex-skill-target/acceptance.md`
- `docs/development-progress.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`

Do not recreate or update `deep-research-report.md`. Do not modify the root DOCX. Keep root `README.md` short unless a compact command pointer becomes clearly necessary.

## Test Plan

Add focused tests, likely in `tests/test_v105_codex_skill_target.py`:

- export one explicit session and write:
  - `SKILL.md`
  - `references/sessions.md`
  - `references/evidence.md`
  - `threadvault-export-manifest.json`
- `SKILL.md` contains valid minimal frontmatter with normalized skill name and description.
- references include session summaries and evidence event IDs.
- repeated `--session` values are deduplicated.
- project export writes Skill candidate files from project-selected sessions.
- unknown explicit session is skipped without failing the whole batch.
- `privacy-mode fail` skips high-risk session-derived reference content and still writes Skill candidate files plus manifest.
- manifest validates against `export_target_manifest`.
- capabilities and schema registry expose the skill target.
- docs exist for this phase.

Regression checks:

```powershell
py -3.12 -m pytest tests\test_v105_codex_skill_target.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault export-target --help
threadvault export-target skill --help
threadvault capabilities --json
threadvault schemas list --json
threadvault schemas write --out docs\schemas --json
Test-Path deep-research-report.md
```

## Acceptance Criteria

- A user can export selected sessions into a Codex Skill candidate folder.
- A user can export a project into a Codex Skill candidate folder.
- The folder contains a concise `SKILL.md` and `references/` Markdown files.
- References include summaries and evidence event IDs without dumping full raw transcripts by default.
- Privacy modes behave consistently with existing export target paths.
- `threadvault-export-manifest.json` tracks written files, skipped items, privacy, and evidence.
- Existing v0/v1 commands remain compatible.
- Documentation makes the phase recoverable from `docs/README.md`, `docs/roadmap/`, `docs/v1/`, and `docs/development-progress.md`.

## Open Assumptions

- The generated output is a Skill candidate, not an automatically installed Skill.
- `agents/openai.yaml` is deferred until the user explicitly wants installed/discoverable UI metadata.
- A concise deterministic `SKILL.md` is preferable to a large generated instruction dump.
- `references/sessions.md` and `references/evidence.md` are enough for the v1 target; more granular reference files can be added later if size becomes an issue.

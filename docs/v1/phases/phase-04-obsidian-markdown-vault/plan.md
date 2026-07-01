# Phase 04 / v1.2 Foundation: Obsidian Markdown Vault Target

## Goal

Add the first Obsidian-ready knowledge output target on top of the v1 `Export Target` module. This phase should let a user export selected sessions or a project into a stable Markdown vault layout that is pleasant to read, carries evidence links, and remains machine-readable through the existing export manifest.

This phase does not try to build all future vault features. It creates the durable file layout and target profile that later tagging, richer summary bundles, and Codex Skill output can reuse.

## Source Context

Required context read before this plan:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v1-personal-knowledge-layer.md`
- `docs/v1/README.md`
- `docs/v1/phases/phase-03-export-target-manifest/plan.md`
- `docs/v1/phases/phase-03-export-target-manifest/acceptance.md`
- `docs/v0/README.md`
- `docs/v0/research/codex-session-archive-research.md`
- `docs/development-progress.md`
- `src/threadvault/export_targets.py`
- `src/threadvault/exporter.py`
- `src/threadvault/store.py`
- `src/threadvault/cli.py`
- `src/threadvault/schemas.py`
- `src/threadvault/summarizer.py`
- `codebase-design` skill guidance for deep modules and deepening

## Research Carry-Forward

The v0 research report repeatedly points to Markdown as the primary export substrate because it serves human reading, local knowledge tools, and future model context at the same time. It also recommends treating HTML, Obsidian, VS Code/Cursor, and Codex Skill outputs as derived layers rather than rebuilding parsing and storage per target.

Relevant carry-forward decisions:

- Keep Markdown as the primary durable format.
- Borrow the idea of section/filter/template-oriented export from existing Codex export tools, without copying external source code.
- Keep Obsidian output as a layer above normalized ThreadVault facts, not as a parallel parser.
- Preserve evidence links from summaries back to ThreadVault event IDs.
- Defer vector retrieval, GUI clients, cloud sync, and external LLM summaries.

## Product Boundary

v1.2 centers on an Obsidian/Markdown vault target that is useful today and structurally stable enough to build on later.

In scope:

- A new `obsidian` export target profile inside `threadvault.export_targets`.
- A new CLI command:

```powershell
threadvault export-target obsidian --session SESSION_ID --out out --json
threadvault export-target obsidian --session A --session B --out out --json
threadvault export-target obsidian --project E:\Codex\ThreadVault --out out --json
```

- Stable vault folders for:
  - `index.md`
  - `sessions/`
  - `evidence/`
- A session summary page for each exported session.
- A session evidence page for each exported session.
- Wiki-style links between index, session pages, and evidence pages.
- Evidence event IDs visible in session pages and manifest entries.
- Reuse of the existing `threadvault-export-manifest.json` contract.
- Privacy modes equivalent to `markdown` target exports.
- Tests for layout, manifest entries, unknown sessions, project exports, privacy fail behavior, capabilities, schemas, and docs traceability.

Out of scope:

- Obsidian plugins, `.obsidian/` configuration, graph styling, or workspace files.
- Daily notes, backlinks beyond stable wiki links, tag inference, or frontmatter taxonomy beyond minimal metadata.
- Codex Skill output.
- Vector/semantic search.
- External LLM summaries.
- Desktop, IDE extension, server, team, or cloud features.
- Replacing the existing `threadvault export` or `export-target markdown` behavior.

## Architecture Decision

### Module

Extend the existing `threadvault.export_targets` module rather than adding a new top-level exporter path.

External interface remains:

- `ExportTargetRequest`
- `export_target(conn, request) -> dict`

The allowed `request.profile` values become:

- `markdown`
- `obsidian`

The caller still provides selection, target directory, and privacy policy. The module owns session selection, target layout, file writing, privacy aggregation, evidence extraction, skipped item reporting, and manifest construction.

### Seam

The seam remains the `Export Target` module interface. Phase 04 should deepen that module instead of widening the CLI surface with target-specific orchestration.

The CLI should say:

- profile: `obsidian`
- selection: explicit sessions and/or project
- target root
- privacy mode/config

The CLI should not know:

- folder names;
- page naming rules;
- wiki-link formatting;
- frontmatter content;
- how summaries and evidence pages are assembled;
- how manifest file entries are collected.

### Internal Writer Shape

Inside `threadvault.export_targets`, split target-specific writing into internal helpers. Keep them private unless a later phase proves multiple modules need the interface.

Likely internal helpers:

- `_select_sessions(conn, request)`
- `_export_markdown_target(...)`
- `_export_obsidian_target(...)`
- `_write_manifest(root, manifest)`
- `_session_summary_page(session, summary)`
- `_session_evidence_page(session, events)`
- `_wiki_link(path)`

This is an internal seam only. Tests should exercise the public `export_target()` behavior through CLI and store paths, not private helpers.

## Vault Layout

Write files under the target root:

```text
out/
  index.md
  threadvault-export-manifest.json
  sessions/
    {session_id}.md
  evidence/
    {session_id}-evidence.md
```

### `index.md`

Required content:

- H1: `# ThreadVault Vault`
- generated timestamp
- optional project cwd
- exported session count
- skipped item count
- links to each session page
- links to evidence pages
- privacy mode and effective findings count

### `sessions/{session_id}.md`

Required content:

- YAML frontmatter:
  - `threadvault_session_id`
  - `threadvault_target_profile: obsidian`
  - `project`
  - `updated_at`
- H1 with summary topic.
- Session metadata.
- Link back to `[[index|Vault Index]]`.
- Link to the matching evidence page.
- Local deterministic summary sections:
  - User goal
  - Key steps
  - Key commands
  - Files
  - Problems
  - Next steps
  - Evidence event IDs
- Evidence IDs must stay visible as plain text so they remain searchable outside Obsidian.

### `evidence/{session_id}-evidence.md`

Required content:

- YAML frontmatter:
  - `threadvault_session_id`
  - `threadvault_target_profile: obsidian`
  - `kind: evidence`
- H1 naming the session.
- Link back to the session summary page.
- Event sections for the events referenced by the summary evidence IDs.
- Each event section includes:
  - event id
  - timestamp if available
  - event type/subtype
  - role/tool/file if available
  - text content, trimmed to a practical limit if needed

The evidence page should not include every raw event by default. It should include high-value evidence events referenced by the local summary. This keeps v1 vault output readable and respects the roadmap boundary that raw transcript retention belongs in SQLite and explicit exports, not every vault page.

## Manifest Shape

Reuse `export_target_manifest`.

For `obsidian`, file entries should use existing manifest fields:

- `kind`: one of:
  - `vault_index`
  - `session_summary`
  - `session_evidence`
- `session_id`
- `path`
- `format: md`
- `privacy_findings_count`
- `evidence_event_ids`

Top-level `target_profile` must be `obsidian`.

Do not introduce a new schema unless the existing manifest schema cannot represent the new files. The current schema is intentionally permissive with file entry internals and should handle this phase.

## CLI Shape

Add command:

```powershell
threadvault export-target obsidian --session SESSION_ID --out out --json
```

Options should match the `markdown` target command:

- `--session` repeatable.
- `--project` single cwd selector.
- `--out` target directory.
- `--privacy-mode warn|redact|fail`.
- `--privacy-config PATH`.
- `--json`.

Selection rules remain the same as Phase 03:

- At least one `--session` or `--project` is required.
- Explicit sessions and project-selected sessions are deduplicated.
- Unknown explicit sessions are reported as skipped.
- Empty project selection succeeds with `exported_count = 0` equivalent manifest state and a skipped project item.

## Privacy Behavior

Privacy policy should match the Phase 03 markdown target:

- `warn`: write files and record findings.
- `redact`: write redacted session/evidence/index files where findings are present.
- `fail`: skip writing a session summary/evidence pair when high-risk findings affect that session output, but still write `index.md` and `threadvault-export-manifest.json` explaining skipped items.

The index file itself may include local paths and should be treated as private local metadata.

## Capabilities And Agent Discovery

Update:

- `capabilities()["json_outputs"]` to include `export-target obsidian`.
- `capabilities()["feature_flags"]` to include `obsidian_vault_target: true`.
- `robot_guide()["recommended_commands"]` with an obsidian target example.
- `robot_schemas()["export_target_manifest"]` if useful to mention obsidian file kinds.

Do not change:

- package version;
- database schema version;
- JSON contract version;
- existing `export-target markdown` behavior;
- existing `threadvault export` behavior.

## Documentation Updates

Create/update:

- `docs/v1/README.md`
- `docs/v1/phases/phase-04-obsidian-markdown-vault/plan.md`
- `docs/v1/phases/phase-04-obsidian-markdown-vault/acceptance.md`
- `docs/development-progress.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`

Do not recreate or update `deep-research-report.md`. Do not modify the root DOCX. Keep root `README.md` short unless a compact command pointer becomes clearly necessary.

## Test Plan

Add focused tests, likely in `tests/test_v104_obsidian_vault_target.py`:

- export one explicit session and write:
  - `index.md`
  - `sessions/sess-current.md`
  - `evidence/sess-current-evidence.md`
  - `threadvault-export-manifest.json`
- session page includes frontmatter, backlink to index, evidence link, summary sections, and evidence event IDs.
- evidence page includes referenced event IDs and a backlink to the session page.
- repeated `--session` values are deduplicated.
- project export writes index and all selected session/evidence pages.
- unknown explicit session is skipped without failing the whole batch.
- `privacy-mode fail` skips high-risk session vault pages and still writes index plus manifest.
- manifest validates against `export_target_manifest`.
- capabilities and schema registry expose the obsidian target.
- docs exist for this phase.

Regression checks:

```powershell
py -3.12 -m pytest tests\test_v104_obsidian_vault_target.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault export-target --help
threadvault export-target obsidian --help
threadvault capabilities --json
threadvault schemas list --json
threadvault schemas write --out docs\schemas --json
Test-Path deep-research-report.md
```

## Acceptance Criteria

- A user can export selected sessions into an Obsidian-readable vault directory.
- A user can export a project into an Obsidian-readable vault directory.
- The vault contains an index, session summary pages, and evidence pages with stable links.
- Evidence event IDs remain visible in the vault and manifest.
- Privacy modes behave consistently with existing export paths.
- `threadvault-export-manifest.json` remains the machine-readable source for files, skipped items, privacy, and evidence.
- Existing v0/v1 commands remain compatible.
- Documentation makes the phase recoverable from `docs/README.md`, `docs/roadmap/`, `docs/v1/`, and `docs/development-progress.md`.

## Open Assumptions

- `obsidian` is the target profile name even though the output remains plain Markdown and usable outside Obsidian.
- Wiki links can be simple and stable; no `.obsidian` workspace metadata is needed.
- Evidence pages should include summary-referenced evidence events, not all raw transcript events.
- YAML frontmatter is acceptable for Obsidian-facing files, but the manifest remains the authoritative machine contract.
- This phase can extend the permissive `export_target_manifest` schema without a new contract version.

# Phase 05 Acceptance: Codex Skill Target

## Scope

This acceptance covers the v1 Codex Skill candidate target. It verifies that ThreadVault can package selected session or project archive material into a local Skill candidate folder with `SKILL.md`, `references/`, evidence event IDs, privacy reporting, and the existing export manifest.

## Evidence

- `threadvault export-target skill` writes `SKILL.md`.
- The target writes `references/sessions.md` and `references/evidence.md`.
- `SKILL.md` contains minimal valid frontmatter with a normalized skill name and description.
- Reference files include summary material and evidence event IDs.
- Project export uses the same target profile and manifest contract.
- Unknown explicit sessions are reported in `skipped`.
- `--privacy-mode fail` skips high-risk session-derived reference content while still writing a reviewable Skill candidate.
- `capabilities --json` advertises `export-target skill` and `codex_skill_target`.

## Validation Commands

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

## Result

Passed on 2026-07-01.

- `py -3.12 -m pytest tests\test_v105_codex_skill_target.py` -> 7 passed
- `py -3.12 -m pytest` -> 174 passed
- `py -3.12 -m ruff check .` -> passed
- `threadvault export-target --help` -> passed and listed `markdown`, `obsidian`, and `skill`
- `threadvault export-target skill --help` -> passed and listed selection, output, Skill metadata, privacy, and JSON options
- `threadvault capabilities --json` -> passed and advertised `export-target skill` plus `codex_skill_target: true`
- `threadvault schemas list --json` -> passed and listed `export_target_manifest`
- `threadvault schemas write --out docs\schemas --json` -> passed and refreshed generated schema artifacts
- `Test-Path deep-research-report.md` -> `False`
- `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
- Runtime/import metadata check -> `threadvault.__version__ = 0.31.0`, `importlib.metadata.version("threadvault") = 0.31.0`

The phase is accepted as the v1 Codex Skill candidate target foundation. Automatic Skill installation, `agents/openai.yaml`, bundled scripts/assets, external LLM rewriting, and richer Skill validation remain separate future work.

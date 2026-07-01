# Phase 04 Acceptance: Obsidian Markdown Vault Target

## Scope

This acceptance covers the v1 Obsidian/Markdown vault target. It verifies that ThreadVault can export selected sessions or project-selected sessions into a stable Markdown vault layout with an index, session summary pages, evidence pages, wiki links, privacy reporting, and the existing export manifest.

## Evidence

- `threadvault export-target obsidian` writes `index.md`.
- Exported sessions get `sessions/{session_id}.md` summary pages.
- Exported sessions get `evidence/{session_id}-evidence.md` evidence pages.
- Vault pages contain Obsidian wiki links between index, session pages, and evidence pages.
- Evidence event IDs remain visible in session pages, evidence pages, and `threadvault-export-manifest.json`.
- Project export uses the same target profile and manifest contract.
- Unknown explicit sessions are reported in `skipped`.
- `--privacy-mode fail` skips high-risk session vault pages while still writing index and manifest.
- `capabilities --json` advertises `export-target obsidian` and `obsidian_vault_target`.

## Validation Commands

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

## Result

Passed on 2026-07-01.

- `py -3.12 -m pytest tests\test_v104_obsidian_vault_target.py` -> 7 passed
- `py -3.12 -m pytest` -> 167 passed
- `py -3.12 -m ruff check .` -> passed
- `threadvault export-target --help` -> passed and listed `markdown` and `obsidian`
- `threadvault export-target obsidian --help` -> passed and listed selection, output, privacy, and JSON options
- `threadvault capabilities --json` -> passed and advertised `export-target obsidian` plus `obsidian_vault_target: true`
- `threadvault schemas list --json` -> passed and listed `export_target_manifest`
- `threadvault schemas write --out docs\schemas --json` -> passed and refreshed generated schema artifacts
- `Test-Path deep-research-report.md` -> `False`
- `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
- Runtime/import metadata check -> `threadvault.__version__ = 0.31.0`, `importlib.metadata.version("threadvault") = 0.31.0`

The phase is accepted as the v1 Obsidian/Markdown vault target foundation. Codex Skill generation, richer tags, daily notes, vector search, and desktop/IDE clients remain separate future work.

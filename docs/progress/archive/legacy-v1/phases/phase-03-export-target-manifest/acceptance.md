# Phase 03 Acceptance: Export Target Manifest

## Scope

This acceptance covers the first v1 `Export Target` module. It verifies that ThreadVault can batch export explicit sessions or project-selected sessions into a Markdown target directory and write a stable manifest for downstream vault, Obsidian, and Codex Skill targets.

## Evidence

- `threadvault export-target markdown` exports one selected session into `sessions/`.
- Repeated `--session` options are deduplicated while preserving the requested selection.
- `--project` writes a project index plus session Markdown files.
- Unknown explicit sessions are reported in `skipped` without failing the whole batch.
- Every batch export writes `threadvault-export-manifest.json`.
- The manifest records target profile, selection, written files, skipped items, privacy summary, and evidence event IDs.
- `capabilities --json` advertises the `export-target` command group and `export_target_manifest` feature flag.
- `schemas list --json` includes `export_target_manifest`.

## Validation Commands

```powershell
py -3.12 -m pytest tests\test_v103_export_target_manifest.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault export-target --help
threadvault export-target markdown --help
threadvault capabilities --json
threadvault schemas list --json
Test-Path deep-research-report.md
rg -n "docs/plans|docs/research/|ThreadVault-report-v1\.md" README.md docs tests src
```

## Result

Passed on 2026-07-01.

- `py -3.12 -m pytest tests\test_v103_export_target_manifest.py` -> 7 passed
- `py -3.12 -m pytest` -> 160 passed
- `py -3.12 -m ruff check .` -> passed
- `threadvault export-target --help` -> passed and listed `markdown`
- `threadvault export-target markdown --help` -> passed and listed selection, output, privacy, and JSON options
- `threadvault capabilities --json` -> passed and advertised `export-target` plus `export_target_manifest: true`
- `threadvault schemas list --json` -> passed and listed `export_target_manifest`
- `Test-Path deep-research-report.md` -> `False`
- `rg -n "docs/plans|docs/research/|ThreadVault-report-v1\.md" README.md docs tests src` -> no stale project references outside the validation command text itself
- `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
- Runtime/import metadata check -> `threadvault.__version__ = 0.31.0`, `importlib.metadata.version("threadvault") = 0.31.0`

The phase is accepted as the v1 export target manifest foundation. Obsidian-specific vault structure, backlinking, tagging, and Codex Skill output remain separate future work.

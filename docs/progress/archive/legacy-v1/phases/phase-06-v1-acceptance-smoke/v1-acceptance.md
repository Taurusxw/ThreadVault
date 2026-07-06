# v1 Acceptance: Personal Knowledge Layer

## Scope

This acceptance covers the ThreadVault v1 personal knowledge layer. It verifies that the completed v0.31.0 CLI/data-layer baseline now has v1 automatic ingest signaling, explicit queue processing, manifest-bearing batch exports, Obsidian/Markdown vault output, and Codex Skill candidate output.

## Evidence

- Codex Hook adapter can enqueue local ingestion work without importing inside the Hook process.
- Ingestion queue can process queued work explicitly with `--apply`.
- Imported sessions remain available through v0 listing and search commands.
- `export-target markdown` writes session Markdown plus `threadvault-export-manifest.json`.
- `export-target obsidian` writes `index.md`, session summary pages, evidence pages, and manifest.
- `export-target skill` writes `SKILL.md`, `references/sessions.md`, `references/evidence.md`, and manifest.
- Capabilities advertise v1 feature flags:
  - `ingestion_queue`
  - `codex_hook_adapter`
  - `export_target_manifest`
  - `obsidian_vault_target`
  - `codex_skill_target`
- Schema discovery includes all v1 JSON schemas.
- `deep-research-report.md` remains retired.

## Validation Commands

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

## Result

Passed on 2026-07-01.

- `py -3.12 -m pytest tests\test_v106_v1_acceptance.py` -> 3 passed
- `py -3.12 -m pytest` -> 177 passed
- `py -3.12 -m ruff check .` -> passed
- `threadvault capabilities --json` -> passed and advertised all v1 feature flags
- `threadvault schemas list --json` -> passed and listed all v1 schemas
- `threadvault export-target --help` -> passed and listed `markdown`, `obsidian`, and `skill`
- `threadvault ingest-queue --help` -> passed and listed `enqueue`, `list`, and `process`
- `threadvault codex-hook --help` -> passed and listed `ingest` and `config`
- `Test-Path deep-research-report.md` -> `False`
- `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
- Runtime/import metadata check -> `threadvault.__version__ = 0.31.0`, `importlib.metadata.version("threadvault") = 0.31.0`

v1 is accepted as the ThreadVault personal knowledge layer. It delivers Hook-safe automatic ingest signaling, explicit queue processing, manifest-bearing batch exports, Obsidian/Markdown vault output, and Codex Skill candidate output while preserving local-first/privacy-first defaults and the v0.31.0 CLI/data-layer baseline.

Deferred to v2/v3 or future opt-in work:

- vector/semantic retrieval;
- MCP/REST interfaces;
- desktop, IDE, or web clients;
- server/cloud/team governance;
- external LLM summaries;
- automatic Skill installation.

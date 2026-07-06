# 2026-07-03 Round 002 - Documentation Completeness

## 1. Goal

Make ThreadVault's active documentation detailed enough for a user or maintainer to understand what the system is for, where data lives, how the UI/CLI/API pieces connect, and which operations are read-only or write-capable.

## 2. Context

The existing `docs/KNOWLEDGE_GRAPH.md` only listed a few entities and one flow. Several active documents still reflected older v0-era scope, including statements that Web UI, vector retrieval, and governance were not included. That conflicted with the current codebase and made the product harder to understand.

## 3. Scope

- `README.md`
- `CONTEXT.md`
- `docs/README.md`
- `docs/DOC_INDEX.md`
- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/DATABASE.md`
- `docs/KNOWLEDGE_GRAPH.md`
- `docs/DEVELOPMENT.md`
- `docs/RULES.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- `docs/CHANGELOG.md`
- `docs/PROGRESS.md`
- `docs/TODO.md`

Historical archives under `docs/progress/archive/` were not rewritten.

## 4. Key Changes

- Added canonical vocabulary in `CONTEXT.md`.
- Expanded the knowledge graph into a real domain map with entities, relationships, data flows, database mappings, UI action families, and safety boundaries.
- Rewrote README around current capability, local UI workflow, important paths, and privacy boundaries.
- Expanded architecture, API, database, development, rules, and document index docs.
- Rewrote the Chinese usage manual to cover ordinary mode, pro mode, CLI, retrieval, export, privacy, backup/restore, governance, hooks, JSON schemas, and FAQ.
- Updated progress, changelog, and TODO records to reflect documentation completeness work.

## 5. Validation

Already run during this documentation work:

```powershell
py -3.12 -m pytest tests/test_v401_personal_ui_readiness.py tests/test_v403_personal_ui_workbench.py -q
py -3.12 -m ruff check src\threadvault\personal_ui.py
```

Recent results:

- Documentation-adjacent focused tests: `14 passed`.
- Ruff for touched UI Python surface: passed.

Completed validation:

```powershell
rg -n "当前不包含|Not included|does not include|138 passed|Web UI、TUI|向量数据库|--resource|summarize --external\" --json|audit append --operation" README.md CONTEXT.md AGENTS.md docs --glob "!docs/progress/archive/**"
py -3.12 -m pytest tests\test_v401_personal_ui_readiness.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py -q
py -3.12 -m ruff check src\threadvault\personal_ui.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py
```

Results:

- Outdated active-doc wording search: no matches.
- Focused tests: `22 passed`.
- Ruff: passed.
- Spot-checked documented governance/UI command examples against Typer help.

## 6. Remaining Risk

- Historical roadmap files intentionally retain future-tense planning language from earlier phases.
- Some generated local output directories remain in the working tree and may contain private data.
- Chinese localization implementation remains string-replacement based and should be structurally improved later.

## 7. Status

completed

# 2026-07-06 Round 002 Clean Knowledge Index

## 本轮目标

Reduce low-value noise in the local Codex knowledge base without deleting raw archived evidence. Advance the package and database schema version because the search/retrieval storage contract now has a cleaned knowledge index.

## 背景原因

The user confirmed that a local knowledge base should clean low-value information and preserve high-value information. The existing archive stored all event text directly in FTS, which made empty events, token counts, base64 screenshots, routine machine events, and oversized tool output dominate the default search surface.

## 修改范围

- `src/threadvault/database.py`
- `src/threadvault/retrieval.py`
- `src/threadvault/schemas.py`
- `src/threadvault/__init__.py`
- `pyproject.toml`
- Focused retrieval/vector/schema tests
- Active database, architecture, knowledge graph, changelog, progress, and document index docs
- Real project-local archive DB at `data/threadvault.db`

## 实施步骤

1. Added derived event fields: `indexed_text`, `index_policy`, and `value_level`.
2. Added event classification rules for empty text, low-value machine events, binary/image evidence, oversized tool output, and normal core/evidence text.
3. Changed FTS storage to index cleaned `indexed_text` while preserving raw `text_content` and `payload_json`.
4. Added schema version `5` migration and clean FTS recreation for legacy `text_content` FTS tables.
5. Added search index diagnostics to stats and doctor payloads.
6. Updated retrieval diagnostics to report `content_column: indexed_text`.
7. Bumped package version from `0.32.0` to `0.33.0`.
8. Upgraded `<python-env>` from Python `3.9.20` to Python `3.12.13` and reinstalled project dev dependencies.
9. Migrated and verified the real project-local archive database.

## 关键决策

- Preserve raw archive data for audit, export, warning review, and debugging.
- Clean only the default knowledge/search index.
- Treat skipped events as intentional index policy results, not deleted records.
- Keep FTS row count aligned with `events` so doctor checks remain simple and stable.
- Make reindex recompute clean fields so future classification rule improvements can be applied to existing archives.

## 修改清单

- Added `classify_index_text()` and clean index helper functions.
- Added `events.indexed_text`, `events.index_policy`, and `events.value_level`.
- Recreated `events_fts` over `indexed_text` and updated insert/update/delete triggers.
- Added `search_index_stats()` and included it in `stats()` and `doctor()`.
- Updated `reindex_fts()` to recompute clean fields before rebuilding FTS.
- Updated retrieval index status to describe the cleaned knowledge index.
- Updated tests for clean classification and schema version follow-through.
- Updated active docs and this round record.

## 测试与验证

- Real DB migration passed for `data/threadvault.db`.
- Schema version is now `5`.
- Clean event columns exist on `events`.
- `events_fts` uses `indexed_text`, not `text_content`.
- Doctor passed with `events=56680` and `events_fts=56680`.
- Real clean-index stats:
  - `total_events`: 56,680
  - `searchable_events`: 35,618
  - `skipped_events`: 21,062
  - `truncated_events`: 4,603
  - `metadata_only_events`: 12
  - `raw_chars`: 54,625,653
  - `indexed_chars`: 18,340,385
  - `indexed_char_ratio`: 0.3357467415538264
- `<python-env>\python.exe --version` -> Python `3.12.13`.
- `<python-env>\python.exe -m ruff check src\threadvault\database.py src\threadvault\retrieval.py src\threadvault\schemas.py tests\test_v201_retrieval_module.py tests\test_v204_local_vector_adapter.py` -> passed.
- `<python-env>\python.exe -m pytest tests\test_v201_retrieval_module.py tests\test_v204_local_vector_adapter.py tests\test_v05_contracts.py tests\test_v29_doctor_schema_contract.py -q` -> `24 passed`.

## 文档更新

- Updated `docs/CHANGELOG.md`.
- Updated `docs/PROGRESS.md`.
- Updated `docs/DOC_INDEX.md`.
- Updated active database/architecture/knowledge graph docs for the clean index model.
- Added this round record.

## 风险与遗留问题

- The clean index rules are intentionally conservative and may need tuning as more real archives are inspected.
- Raw low-value content still exists in the archive database by design; this is not a deletion or compaction feature.
- The upgraded Anaconda environment reported an unrelated existing dependency warning: `selenium` wants `websocket-client~=1.8`.
- A backup was created before migration: `data/threadvault-before-clean-index-20260706-130454.db`.

## 下一步计划

- Add configurable clean-index policy thresholds if future usage shows different projects need different noise tolerance.
- Consider adding a UI/CLI view for `search_index` diagnostics so users can see how much of the archive is searchable, skipped, or truncated.

## 状态

completed

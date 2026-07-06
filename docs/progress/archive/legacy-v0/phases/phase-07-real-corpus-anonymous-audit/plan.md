# Phase 07 / v0.7: Real Corpus Anonymous Audit

## Goal

Make real Codex home diagnostics safer by default. `ingest-sample` and new audit-style output should report parse health, warning distribution, and compatibility signals without exposing raw transcript text, raw absolute paths, or stable session identifiers unless the user explicitly opts in.

## Scope

- Keep ThreadVault local-first and privacy-first.
- Work only on CLI/data-layer diagnostics.
- Do not add UI, MCP server, vector search, cloud sync, team features, or external LLM summaries.
- Do not copy real user transcript content into fixtures, reports, or docs.

## Tasks

- Add anonymized sample identifiers derived from a per-run salt.
- Change `ingest-sample --json` default output to hide raw paths and session IDs.
- Add `--include-paths` for explicit opt-in path/session disclosure during local debugging.
- Add an `audit-corpus` command that wraps dry-run sampling and emits:
  - file count and parseable ratio
  - total events and warnings
  - top warning codes
  - classification counts
  - per-file anonymous samples
  - privacy note explaining that raw content is not emitted
- Add schema coverage for the audit output.
- Add tests proving default outputs do not contain fixture absolute paths or raw session IDs.
- Update README, phase progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault ingest-sample --codex-home tests/fixtures/codex_home --dry-run --json
threadvault audit-corpus --codex-home tests/fixtures/codex_home --json
threadvault audit-corpus --codex-home tests/fixtures/codex_home --include-paths --json
threadvault schemas show corpus_audit --json
```

## Assumptions

- Anonymous sample IDs only need to be stable within one command run.
- `--include-paths` is acceptable as explicit local opt-in for debugging.
- Existing tests may keep using fixture paths internally; public CLI JSON defaults should be privacy-safe.


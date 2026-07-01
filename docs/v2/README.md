# ThreadVault v2 Archive

This directory tracks active v2 development for the retrieval and interfaces layer.

v2 starts from the accepted v1 personal knowledge layer and adds a stable retrieval interface for CLI, agents, and future MCP/client integrations. The active roadmap source is `docs/roadmap/v2-retrieval-and-interfaces.md`.

## Development Rules

- Before each phase, read the current Markdown source of truth:
  `docs/README.md`, `docs/roadmap/major-version-roadmap.md`,
  `docs/roadmap/v2-retrieval-and-interfaces.md`, `docs/v1/README.md`,
  `docs/v0/README.md`, and `docs/development-progress.md`.
- The initial v2 goal text mentioned `docs/roadmap/v2-personal-knowledge-layer.md` and `docs/v0-v1/`; those paths do not exist in the current repository. Use the actual v2 roadmap plus the separate `docs/v0/` and `docs/v1/` archives.
- When a phase depends on prior research or comparable existing projects, cite the relevant archived Markdown in the phase plan, especially
  `docs/v0/research/codex-session-archive-research.md` and
  `docs/archive/mathforge-research-appendices.md`.
- Each phase gets its own directory under `phases/`.
- Each phase must include a detailed `plan.md` before implementation.
- Design notes, reviews, acceptance reports, or gap audits stay beside the phase plan when needed.
- `docs/development-progress.md` must be updated after each implementation round.
- Root `README.md` remains a short project entrypoint; phase detail belongs here or in the roadmap.
- `deep-research-report.md` is retired and must not be recreated.
- The root DOCX remains historical/formal background. Do not modify it during ordinary phase work.

## Phases

| Phase | Version Line | Title | Documents |
|---|---|---|---|
| 01 | v2.0 foundation | Retrieval Module FTS Wrapper | [plan](phases/phase-01-retrieval-module-fts-wrapper/plan.md), [acceptance](phases/phase-01-retrieval-module-fts-wrapper/acceptance.md) |
| 02 | v2.1 foundation | Retrieval JSON Contracts And Diagnostics | [plan](phases/phase-02-retrieval-json-contracts-diagnostics/plan.md), [design notes](phases/phase-02-retrieval-json-contracts-diagnostics/design-notes.md), [acceptance](phases/phase-02-retrieval-json-contracts-diagnostics/acceptance.md) |
| 03 | v2.2 foundation | Summary Evidence Chunk Selection | [plan](phases/phase-03-summary-evidence-chunks/plan.md), [design notes](phases/phase-03-summary-evidence-chunks/design-notes.md), [acceptance](phases/phase-03-summary-evidence-chunks/acceptance.md) |
| 04 | v2.3 foundation | Local Vector Adapter | [plan](phases/phase-04-local-vector-adapter/plan.md), [design notes](phases/phase-04-local-vector-adapter/design-notes.md), [acceptance](phases/phase-04-local-vector-adapter/acceptance.md) |
| 05 | v2.4 foundation | Hybrid Ranking And Search Explanations | [plan](phases/phase-05-hybrid-ranking-explanations/plan.md), [design notes](phases/phase-05-hybrid-ranking-explanations/design-notes.md), [acceptance](phases/phase-05-hybrid-ranking-explanations/acceptance.md) |
| 06 | v2.5 foundation | Agent-Facing Retrieval Interface | [plan](phases/phase-06-agent-facing-retrieval-interface/plan.md), [design notes](phases/phase-06-agent-facing-retrieval-interface/design-notes.md), [acceptance](phases/phase-06-agent-facing-retrieval-interface/acceptance.md) |
| 07 | v2.6 acceptance | v2 Acceptance Smoke | [plan](phases/phase-07-v2-acceptance-smoke/plan.md), [acceptance](phases/phase-07-v2-acceptance-smoke/v2-acceptance.md) |

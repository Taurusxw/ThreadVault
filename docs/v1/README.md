# ThreadVault v1 Archive

This directory tracks active v1 development for the personal knowledge layer.

v1 starts from the completed `v0.31.0` CLI/data-layer baseline and adds automatic ingestion plus durable knowledge outputs. The active roadmap source is `docs/roadmap/v1-personal-knowledge-layer.md`.

## Development Rules

- Before each phase, read the current Markdown source of truth:
  `docs/README.md`, `docs/roadmap/major-version-roadmap.md`,
  `docs/roadmap/v1-personal-knowledge-layer.md`, `docs/v0/README.md`,
  and `docs/development-progress.md`.
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
| 01 | v1.0 foundation | Ingestion Automation Queue | [plan](phases/phase-01-ingestion-automation-queue/plan.md), [acceptance](phases/phase-01-ingestion-automation-queue/acceptance.md) |
| 02 | v1.0 foundation | Codex Hook Adapter | [plan](phases/phase-02-codex-hook-adapter/plan.md), [acceptance](phases/phase-02-codex-hook-adapter/acceptance.md) |
| 03 | v1.1 foundation | Export Target Manifest | [plan](phases/phase-03-export-target-manifest/plan.md), [acceptance](phases/phase-03-export-target-manifest/acceptance.md) |
| 04 | v1.2 foundation | Obsidian Markdown Vault Target | [plan](phases/phase-04-obsidian-markdown-vault/plan.md), [acceptance](phases/phase-04-obsidian-markdown-vault/acceptance.md) |
| 05 | v1.3 foundation | Codex Skill Target | [plan](phases/phase-05-codex-skill-target/plan.md), [acceptance](phases/phase-05-codex-skill-target/acceptance.md) |
| 06 | v1.4 acceptance | v1 Smoke And Local Audit | [plan](phases/phase-06-v1-acceptance-smoke/plan.md), [v1 acceptance](phases/phase-06-v1-acceptance-smoke/v1-acceptance.md) |

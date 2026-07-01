# ThreadVault v4 Archive

This directory tracks active v4 development for the ThreadVault Personal Web UI.

v4 starts from the accepted v3 richer-client and governance baseline. Its purpose is a local, personal, localhost Web
console over the existing ThreadVault archive. It must reuse the accepted v1, v2, and v3 interfaces instead of creating a
parallel backend.

## Development Rules

- Before each phase, read the current Markdown source of truth:
  `docs/README.md`, `docs/roadmap/major-version-roadmap.md`, `docs/v3/README.md`,
  `docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md`, `docs/v2/README.md`,
  `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`, `docs/THREADVAULT_USAGE_MANUAL.md`,
  and `docs/development-progress.md`.
- If a phase needs historical research context, prefer the archived references:
  `docs/roadmap/v3-clients-and-team-governance.md`,
  `docs/v0/research/codex-session-archive-research.md`, and
  `docs/archive/mathforge-research-appendices.md`.
- Each phase gets its own directory under `phases/`.
- Each phase must include a detailed `plan.md` before implementation.
- Design notes, coverage matrices, gap audits, acceptance reports, and follow-up records stay beside the phase plan.
- `docs/development-progress.md` must be updated after each implementation round.
- Root `README.md` remains a short project entrypoint; detailed v4 phase records belong here.
- `deep-research-report.md` is retired and must not be recreated.
- The root DOCX remains historical/formal background. Do not modify it during ordinary phase work.

## Product Boundaries

- v4 centers on a personal local Web UI for one machine and one user.
- The default server host must be `127.0.0.1`.
- No account login, team collaboration, cloud sync, public server deployment, or mandatory external model calls are in
  v4 personal scope.
- Do not introduce React, Vite, Node, or a separate frontend build pipeline unless explicitly requested.
- Prefer a Python stdlib HTTP server plus static HTML, CSS, and JavaScript.
- The UI goal is complete and usable first. Visual polish is secondary to action coverage, safety, and traceability.

## Architecture Boundaries

- Reuse `ArchiveStore` as the primary backend module.
- Reuse v1 ingestion queue, Codex hook adapter, and export target capabilities.
- Reuse v2 retrieval, hybrid retrieval, vector adapter, summary chunks, and agent-facing retrieval.
- Reuse v3 client interface, local TUI runtime, governance diagnostics, business-command instrumentation, and acceptance
  smoke.
- Do not rewrite the Codex JSONL parser.
- Do not rewrite SQLite search or retrieval internals.
- Do not bypass privacy scanning for export or raw-read flows.
- Do not make the Web UI a second backend with its own business rules.

## Safety Boundaries

- `threadvault ui serve` must default to `--host 127.0.0.1`.
- Public binding must never be the default.
- Dangerous write operations must require explicit confirmation in the UI action layer:
  `restore_apply`, `vacuum`, `reindex`, and `schema_write`.
- Export actions must support preview before execution.
- Prune/delete actions must default to dry-run, with apply requiring explicit confirmation.
- Backup can execute directly, but must show the target path.
- External model calls, cloud sync, and team enforcement must remain disabled unless explicitly configured outside the
  personal UI defaults.

## Phases

| Phase | Version Line | Title | Documents |
|---|---|---|---|
| 01 | v4.0 readiness | Personal UI Readiness | [plan](phases/phase-01-personal-ui-readiness/plan.md), [design notes](phases/phase-01-personal-ui-readiness/design-notes.md), [coverage matrix](phases/phase-01-personal-ui-readiness/coverage-matrix.md), [acceptance](phases/phase-01-personal-ui-readiness/acceptance.md) |
| 02 | v4.1 server | Local UI Server | [plan](phases/phase-02-local-ui-server/plan.md), [design notes](phases/phase-02-local-ui-server/design-notes.md), [acceptance](phases/phase-02-local-ui-server/acceptance.md) |
| 03 | v4.2 workbench | Personal UI Workbench | [plan](phases/phase-03-personal-ui-workbench/plan.md), [design notes](phases/phase-03-personal-ui-workbench/design-notes.md), [acceptance](phases/phase-03-personal-ui-workbench/acceptance.md) |
| 04 | v4.3 actions | UI Action Coverage | [plan](phases/phase-04-ui-action-coverage/plan.md), [design notes](phases/phase-04-ui-action-coverage/design-notes.md), [acceptance](phases/phase-04-ui-action-coverage/acceptance.md) |
| 05 | v4.4 acceptance | v4 Acceptance Smoke | [plan](phases/phase-05-v4-acceptance-smoke/plan.md), [design notes](phases/phase-05-v4-acceptance-smoke/design-notes.md), [acceptance](phases/phase-05-v4-acceptance-smoke/acceptance.md) |
| 06 | v4.5 localization | UI Chinese Localization | [plan](phases/phase-06-ui-chinese-localization/plan.md), [design notes](phases/phase-06-ui-chinese-localization/design-notes.md), [acceptance](phases/phase-06-ui-chinese-localization/acceptance.md) |

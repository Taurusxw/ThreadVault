# ThreadVault v3 Archive

This directory tracks active v3 development for richer clients and optional team governance.

v3 starts from the accepted v2 retrieval and interfaces layer. The active roadmap source is
`docs/roadmap/v3-clients-and-team-governance.md`.

## Development Rules

- Before each phase, read the current Markdown source of truth:
  `docs/README.md`, `docs/roadmap/major-version-roadmap.md`,
  `docs/roadmap/v3-clients-and-team-governance.md`, `docs/v2/README.md`,
  `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`, and
  `docs/development-progress.md`.
- Use `docs/v0/research/codex-session-archive-research.md` and
  `docs/archive/mathforge-research-appendices.md` only when a phase needs historical research context.
- Each phase gets its own directory under `phases/`.
- Each phase must include a detailed `plan.md` before implementation.
- Design notes, reviews, acceptance reports, or gap audits stay beside the phase plan when needed.
- `docs/development-progress.md` must be updated after each implementation round.
- Root `README.md` remains a short project entrypoint; phase detail belongs here or in the roadmap.
- `deep-research-report.md` is retired and must not be recreated.
- The root DOCX remains historical/formal background. Do not modify it during ordinary phase work.

## Product Boundaries

- v3 centers on richer clients and optional team governance.
- Client layers must sit on top of ThreadVault archive, export, summary, retrieval, vector, hybrid, and agent-facing
  interfaces. They must not re-parse Codex transcripts or bypass privacy policy.
- The accepted v2 retrieval core remains the foundation. Do not rewrite FTS retrieval, hybrid ranking, vector indexing,
  or agent-facing retrieval unless a v3 phase first documents the reason and migration plan.
- Desktop shells, VS Code/Cursor extensions, optional local Web/TUI clients, optional server mode, team permissions,
  audit logs, and centralized backup/restore are in v3 planning scope.
- Server, cloud, and team capabilities must stay opt-in. Local-first and privacy-first defaults remain the baseline.

## Phases

| Phase | Version Line | Title | Documents |
|---|---|---|---|
| 01 | v3.0 readiness | Client Interface Readiness Audit | [plan](phases/phase-01-client-interface-readiness-audit/plan.md), [design notes](phases/phase-01-client-interface-readiness-audit/design-notes.md), [acceptance](phases/phase-01-client-interface-readiness-audit/acceptance.md) |
| 02 | v3.1 foundation | Client Manifest Entrypoint | [plan](phases/phase-02-client-manifest-entrypoint/plan.md), [design notes](phases/phase-02-client-manifest-entrypoint/design-notes.md), [acceptance](phases/phase-02-client-manifest-entrypoint/acceptance.md) |
| 03 | v3.1 foundation | Client Overview Workflow | [plan](phases/phase-03-client-overview-workflow/plan.md), [design notes](phases/phase-03-client-overview-workflow/design-notes.md), [acceptance](phases/phase-03-client-overview-workflow/acceptance.md) |
| 04 | v3.1 foundation | Client Session Detail Workflow | [plan](phases/phase-04-client-session-detail-workflow/plan.md), [design notes](phases/phase-04-client-session-detail-workflow/design-notes.md), [acceptance](phases/phase-04-client-session-detail-workflow/acceptance.md) |
| 05 | v3.1 foundation | Client Export Preview Workflow | [plan](phases/phase-05-client-export-preview-workflow/plan.md), [design notes](phases/phase-05-client-export-preview-workflow/design-notes.md), [acceptance](phases/phase-05-client-export-preview-workflow/acceptance.md) |
| 06 | v3.1 foundation | Client Warning Detail Workflow | [plan](phases/phase-06-client-warning-detail-workflow/plan.md), [design notes](phases/phase-06-client-warning-detail-workflow/design-notes.md), [acceptance](phases/phase-06-client-warning-detail-workflow/acceptance.md) |
| 07 | v3.2 governance | Governance Baseline | [plan](phases/phase-07-governance-baseline/plan.md), [design notes](phases/phase-07-governance-baseline/design-notes.md), [acceptance](phases/phase-07-governance-baseline/acceptance.md) |
| 08 | v3.2 governance | Local Audit Log Workflow | [plan](phases/phase-08-local-audit-log-workflow/plan.md), [design notes](phases/phase-08-local-audit-log-workflow/design-notes.md), [acceptance](phases/phase-08-local-audit-log-workflow/acceptance.md) |
| 09 | v3.2 governance | Permission Preflight Workflow | [plan](phases/phase-09-permission-preflight-workflow/plan.md), [design notes](phases/phase-09-permission-preflight-workflow/design-notes.md), [acceptance](phases/phase-09-permission-preflight-workflow/acceptance.md) |
| 10 | v3.2 governance | Governance Enforcement Gap Audit | [plan](phases/phase-10-governance-enforcement-gap-audit/plan.md), [design notes](phases/phase-10-governance-enforcement-gap-audit/design-notes.md), [gap audit](phases/phase-10-governance-enforcement-gap-audit/gap-audit.md), [acceptance](phases/phase-10-governance-enforcement-gap-audit/acceptance.md) |
| 11 | v3.2 governance | Governance Enforcement Dry Run | [plan](phases/phase-11-governance-enforcement-dry-run/plan.md), [design notes](phases/phase-11-governance-enforcement-dry-run/design-notes.md), [acceptance](phases/phase-11-governance-enforcement-dry-run/acceptance.md) |
| 12 | v3.2 governance | Governance Policy Readiness | [plan](phases/phase-12-governance-policy-readiness/plan.md), [design notes](phases/phase-12-governance-policy-readiness/design-notes.md), [acceptance](phases/phase-12-governance-policy-readiness/acceptance.md) |
| 13 | v3.2 governance | Export/Backup Governance Preflight | [plan](phases/phase-13-export-backup-governance-preflight/plan.md), [design notes](phases/phase-13-export-backup-governance-preflight/design-notes.md), [acceptance](phases/phase-13-export-backup-governance-preflight/acceptance.md) |
| 14 | v3.2 governance | Restore/Retention Governance Preflight | [plan](phases/phase-14-restore-retention-governance-preflight/plan.md), [design notes](phases/phase-14-restore-retention-governance-preflight/design-notes.md), [acceptance](phases/phase-14-restore-retention-governance-preflight/acceptance.md) |
| 15 | v3.2 governance | Raw Read Governance Preflight | [plan](phases/phase-15-raw-read-governance-preflight/plan.md), [design notes](phases/phase-15-raw-read-governance-preflight/design-notes.md), [acceptance](phases/phase-15-raw-read-governance-preflight/acceptance.md) |
| 16 | v3.2 governance | Summary/Search Governance Preflight | [plan](phases/phase-16-summary-search-governance-preflight/plan.md), [design notes](phases/phase-16-summary-search-governance-preflight/design-notes.md), [acceptance](phases/phase-16-summary-search-governance-preflight/acceptance.md) |
| 17 | v3.2 governance | Export Preview Governance Preflight | [plan](phases/phase-17-export-preview-governance-preflight/plan.md), [design notes](phases/phase-17-export-preview-governance-preflight/design-notes.md), [acceptance](phases/phase-17-export-preview-governance-preflight/acceptance.md) |
| 18 | v3.2 governance | External Model Governance Preflight | [plan](phases/phase-18-external-model-governance-preflight/plan.md), [design notes](phases/phase-18-external-model-governance-preflight/design-notes.md), [acceptance](phases/phase-18-external-model-governance-preflight/acceptance.md) |
| 19 | v3.3 governance | Server Policy Readiness | [plan](phases/phase-19-server-policy-readiness/plan.md), [design notes](phases/phase-19-server-policy-readiness/design-notes.md), [acceptance](phases/phase-19-server-policy-readiness/acceptance.md) |
| 20 | v3.3 governance | Centralized Audit Retention Readiness | [plan](phases/phase-20-centralized-audit-retention-readiness/plan.md), [design notes](phases/phase-20-centralized-audit-retention-readiness/design-notes.md), [acceptance](phases/phase-20-centralized-audit-retention-readiness/acceptance.md) |
| 21 | v3.6 readiness | v3 Completion Gap Audit | [plan](phases/phase-21-v3-completion-gap-audit/plan.md), [design notes](phases/phase-21-v3-completion-gap-audit/design-notes.md), [gap audit](phases/phase-21-v3-completion-gap-audit/gap-audit.md), [acceptance](phases/phase-21-v3-completion-gap-audit/acceptance.md) |
| 22 | v3.4 governance | Identity Actor Binding Readiness | [plan](phases/phase-22-identity-actor-binding-readiness/plan.md), [design notes](phases/phase-22-identity-actor-binding-readiness/design-notes.md), [acceptance](phases/phase-22-identity-actor-binding-readiness/acceptance.md) |
| 23 | v3.4 governance | Centralized Policy Store Readiness | [plan](phases/phase-23-centralized-policy-store-readiness/plan.md), [design notes](phases/phase-23-centralized-policy-store-readiness/design-notes.md), [acceptance](phases/phase-23-centralized-policy-store-readiness/acceptance.md) |
| 24 | v3.5 governance | Centralized Backup/Restore Policy Readiness | [plan](phases/phase-24-centralized-backup-restore-policy-readiness/plan.md), [design notes](phases/phase-24-centralized-backup-restore-policy-readiness/design-notes.md), [acceptance](phases/phase-24-centralized-backup-restore-policy-readiness/acceptance.md) |
| 25 | v3.3 prototype | Read-Only Shared Server Prototype | [plan](phases/phase-25-read-only-shared-server-prototype/plan.md), [design notes](phases/phase-25-read-only-shared-server-prototype/design-notes.md), [acceptance](phases/phase-25-read-only-shared-server-prototype/acceptance.md) |
| 26 | v3.4 governance | Client Export Preview Governance Instrumentation | [plan](phases/phase-26-client-export-preview-governance-instrumentation/plan.md), [design notes](phases/phase-26-client-export-preview-governance-instrumentation/design-notes.md), [acceptance](phases/phase-26-client-export-preview-governance-instrumentation/acceptance.md) |
| 27 | v3.1 runtime | Local TUI Client Runtime | [plan](phases/phase-27-local-tui-client-runtime/plan.md), [design notes](phases/phase-27-local-tui-client-runtime/design-notes.md), [acceptance](phases/phase-27-local-tui-client-runtime/acceptance.md) |
| 28 | v3.4 governance | Identity Actor Binding Runtime | [plan](phases/phase-28-identity-actor-binding-runtime/plan.md), [design notes](phases/phase-28-identity-actor-binding-runtime/design-notes.md), [acceptance](phases/phase-28-identity-actor-binding-runtime/acceptance.md) |
| 29 | v3.4 governance | Central Policy Store Runtime | [plan](phases/phase-29-central-policy-store-runtime/plan.md), [design notes](phases/phase-29-central-policy-store-runtime/design-notes.md), [acceptance](phases/phase-29-central-policy-store-runtime/acceptance.md) |
| 30 | v3.4 governance | Centralized Audit Store Runtime | [plan](phases/phase-30-centralized-audit-store-runtime/plan.md), [design notes](phases/phase-30-centralized-audit-store-runtime/design-notes.md), [acceptance](phases/phase-30-centralized-audit-store-runtime/acceptance.md) |
| 31 | v3.5 governance | Centralized Backup/Restore Policy Runtime | [plan](phases/phase-31-centralized-backup-restore-policy-runtime/plan.md), [design notes](phases/phase-31-centralized-backup-restore-policy-runtime/design-notes.md), [acceptance](phases/phase-31-centralized-backup-restore-policy-runtime/acceptance.md) |
| 32 | v3.4 governance | Business Command Governance Instrumentation | [plan](phases/phase-32-business-command-governance-instrumentation/plan.md), [design notes](phases/phase-32-business-command-governance-instrumentation/design-notes.md), [acceptance](phases/phase-32-business-command-governance-instrumentation/acceptance.md) |
| 33 | v3.6 acceptance | v3 Final Acceptance Smoke | [plan](phases/phase-33-v3-final-acceptance-smoke/plan.md), [design notes](phases/phase-33-v3-final-acceptance-smoke/design-notes.md), [acceptance](phases/phase-33-v3-final-acceptance-smoke/acceptance.md) |

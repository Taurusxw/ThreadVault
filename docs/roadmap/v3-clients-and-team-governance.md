# ThreadVault v3: Clients And Team Governance

## Summary

`v3` builds richer ways to use ThreadVault after the archive, export, and retrieval modules are stable. The goal is optional client and team workflows without weakening the local-first default.

The center of gravity is `richer clients + optional governance`, not replacing the CLI or forcing cloud infrastructure.

## Key Outcomes

- Desktop, Web, TUI, or IDE clients can browse/search/export through stable ThreadVault modules.
- VS Code/Cursor integrations can reuse Markdown exports or the retrieval interface.
- Optional server mode can support shared indexes, centralized audit, and team access.
- Team permissions separate raw transcript access from summary/search/export access.
- Audit logs and backup/restore policy are strong enough for shared use.

## Architecture Changes

### Client Layer

Treat GUI and IDE integrations as clients over ThreadVault's archive, export, summary, and retrieval interfaces. They should not re-parse Codex transcripts or bypass privacy policy.

Candidate clients:

- Desktop shell for local browsing and export.
- VS Code/Cursor extension for project-local archive browsing.
- Web UI for a local or optional server deployment.
- TUI only if it solves repeated local workflows better than the CLI.

### Optional Server Layer

Add server components only when the use case requires sharing, remote embedding, centralized audit, or policy enforcement. Server mode must be opt-in and should keep the local CLI useful without it.

### Governance Layer

Introduce team governance around:

- Access levels: raw transcript, summary, search, export, delete/retention.
- Audit logs for reads, exports, deletes, restore operations, and external model calls.
- Policy-controlled redaction and outbound-data rules.
- Backup and restore procedures suitable for shared archives.

## Out Of Scope For v3

- Making cloud sync mandatory.
- Removing local SQLite as the personal default.
- Allowing clients to skip privacy scanning for export/share operations.
- Treating external LLM summarization as safe without evidence validation and outbound policy.

## Suggested Milestones

1. `v3.0`: Client interface readiness audit over archive/export/retrieval modules.
2. `v3.1`: First richer client, preferably a local desktop shell or VS Code/Cursor extension.
3. `v3.2`: Optional local Web UI or TUI if workflows justify it.
4. `v3.3`: Server mode design and read-only shared deployment prototype.
5. `v3.4`: Team permissions and audit logs.
6. `v3.5`: Centralized backup/restore and retention policy.
7. `v3.6`: v3 acceptance smoke for local client and optional shared deployment.

## Acceptance Criteria

- The CLI remains fully usable without any server.
- A richer client can browse/search/export without duplicating parser logic.
- Shared deployments can distinguish raw transcript access from summary/search access.
- Audit records exist for sensitive operations.
- External model or cloud behavior is explicit, configurable, and visible in diagnostics.


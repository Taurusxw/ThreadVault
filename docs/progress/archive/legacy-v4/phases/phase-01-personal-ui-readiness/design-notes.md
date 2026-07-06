# v4 Phase 01 Design Notes: Personal UI Readiness

## Personal UI Boundary

The v4 UI is a local workbench for one user's existing ThreadVault archive. It is not a team product, not a cloud product,
and not a public service. The default runtime should be a localhost process opened by the user, backed by static assets
and a small Python stdlib HTTP server.

The first UI screen should be the usable workbench, not a marketing page. The expected layout for later phases is:

- left navigation for capability families
- top search bar for retrieval and agent query flows
- main work area for sessions, summaries, diagnostics, previews, and forms
- right JSON output panel for copyable machine-readable results

## Module Interface Direction

The future UI server should be a thin transport over existing modules. The important seam is not the HTTP handler. The
deep module should be an action registry that translates UI action names into calls against `ArchiveStore`, existing CLI
contract helpers, and accepted v2/v3 interfaces.

Desired interface shape for a later phase:

```text
run_ui_action(action_name, payload, *, db, config) -> action_result
```

That interface should centralize confirmation checks, preview requirements, JSON serialization, and error shaping. The
HTTP server can remain small because the action registry carries the business behavior.

## Reuse Commitments

- Session import remains backed by existing ingestion/import modules.
- Session list/detail/search remain backed by `ArchiveStore`, retrieval, and client interfaces.
- Summary, privacy, warning, export, config, schema, backup, restore, audit, and governance flows remain backed by the
  accepted CLI/store/runtime surfaces.
- The UI must call existing preview and privacy scan behavior instead of inventing new preview or redaction rules.
- The UI must expose JSON contracts as first-class output, because ThreadVault already treats append-only JSON contracts
  as its agent/client interface.

## Safety Model

Personal UI convenience must not weaken local-first and privacy-first defaults:

- Bind to `127.0.0.1` by default.
- Treat non-localhost binding as explicit advanced behavior.
- Require `confirm=true` for destructive or heavyweight writes:
  `restore_apply`, `vacuum`, `reindex`, `schema_write`, and any prune/delete apply action.
- Route export execution through preview-first flows.
- Keep prune/delete dry-run by default.
- Show backup destination paths before and after execution.
- Keep external model calls, cloud sync, and team enforcement disabled by default.

## Deferred Choices

- Exact HTTP route names are deferred to Phase 02.
- Exact single-page workbench styling is deferred to Phase 03.
- The exhaustive action registry implementation is deferred to Phase 04.
- Automated UI acceptance smoke is deferred to Phase 05.


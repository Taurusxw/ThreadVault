# Phase 30 / v0.30: Completion Gap Audit

## Goal

Perform a phase-level completion and gap audit against the original ThreadVault objective and the later quality-hardening requirements.

ThreadVault has implemented the CLI MVP and many maintenance/agent-friendly layers. v0.30 pauses feature work to inspect current evidence: commands, schemas, tests, documentation, privacy boundaries, and traceability.

## Scope

- Audit current implementation against:
  - original CLI MVP scope;
  - v0.2 data-layer and machine-friendly CLI goals;
  - v0.3-v0.5 documentation, traceability, privacy, real-corpus, and JSON contract goals;
  - later backup/restore/retention/schema hardening phases.
- Produce a durable audit document under `docs/v0/phases/phase-30-completion-gap-audit/`.
- Mark each requirement as `complete`, `partial`, `out-of-scope`, or `next`.
- Identify small fixable defects if found.
- Do not mark the overall long-running goal complete unless evidence proves all user requirements are satisfied.

## Evidence Sources

- Current `threadvault --help`, `capabilities --json`, and `schemas list --json`.
- `README.md`.
- `docs/development-progress.md`.
- `docs/v0/phases/`.
- `docs/v0/research/`.
- `docs/schemas/`.
- `tests/`.
- Source modules under `src/threadvault/`.
- Validation commands from the current environment.

## Existing Project Lessons

- Use `codebase-design`: audit the interfaces agents and users rely on, not just implementation line count.
- Reuse ThreadVault's own `capabilities`, schema, doctor, and self-test outputs as evidence.
- Follow CASS-style health/contract thinking: completion claims must be machine-checkable where possible.

## Tasks

- Create `docs/v0/phases/phase-30-completion-gap-audit/completion-gap-audit.md`.
- Update README with a short current-status pointer.
- Update `docs/development-progress.md`.
- Append a v0.30 implementation appendix to both research Markdown files.
- Run full pytest, ruff, and selected CLI smoke commands.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault --help
threadvault capabilities --json
threadvault schemas list --json
threadvault self-test --json
threadvault doctor --codex-home tests/fixtures/codex_home --json
```

## Assumptions

- DOCX remains out of scope unless explicitly requested.
- Audit is evidence-gathering and planning; it should not claim completion without full proof.
- Remaining future UI/cloud/vector work can be classified as intentionally out of current CLI/data-layer scope.



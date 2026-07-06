# Phase 21 / v0.21 External Review: Restore Plan Preflight

## Review Summary

v0.21 adds a restore preflight plan. Mature backup tools separate "verify/plan" from "apply"; ThreadVault should do the same before any overwrite-capable restore command exists.

## Sources Reviewed

- ThreadVault v0.16 `backup-verify`: read-only integrity and schema checks.
- ThreadVault v0.20 backup manifests: provenance and checksum evidence.
- ThreadVault audit/backup prune: dry-run first, explicit apply later.
- CASS-style robot workflows: deterministic JSON diagnostics for agents.
- Existing local Codex export tools: local-first artifact management, no cloud dependency.

## v0.21 Application

- Add `restore-plan`, not restore.
- Treat valid backups without manifests as usable but lower-confidence legacy artifacts.
- Block impossible or dangerous plans such as `target-db` equal to the backup path.
- Warn when the target file already exists because future restore would require explicit overwrite protection.

## Risks

- Users may mistake a successful plan for an executed restore. Docs and command wording must say it is read-only.
- Missing manifests should not strand v0.15-v0.19 backups; they produce warnings rather than hard errors.
- Path comparisons can be tricky on Windows. Use resolved paths where possible and tolerate non-existing targets.


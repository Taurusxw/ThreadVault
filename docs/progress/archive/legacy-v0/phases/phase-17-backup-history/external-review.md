# Phase 17 / v0.17 External Review: Backup History

## Review Summary

v0.17 adds backup history commands. This mirrors the already proven audit-history workflow: list local artifacts, identify the latest one, and provide a command that uses the latest artifact without manual filename copying.

## Sources Reviewed

- ThreadVault audit-history commands: reuse the successful list/latest pattern instead of inventing a new interface.
- CASS-style robot workflows: deterministic JSON outputs help agents chain commands safely.
- ccusage-style local maintenance: history directories need simple inspection commands before pruning or deletion.
- SQLite backup verification from v0.16: latest backup verification should call the existing verifier.

## v0.17 Application

- Add `backup-history list`.
- Add `backup-history latest`.
- Add `backup-history verify-latest`.
- Do not implement restore or prune.
- Keep malformed/non-SQLite backup files as warnings, not fatal list failures.

## Risks

- Treating every `.db` in a directory as a ThreadVault backup could be noisy. v0.17 focuses on canonical `threadvault-backup-*.db` files created by `backup --out DIR`.
- Users may expect pruning once history exists. v0.17 explicitly avoids deletion; retention can be designed later with backup-specific safeguards.


# v3 Phase 05 Design Notes: Client Export Preview Workflow

## Summary

`client export-preview` is a confirmation payload for richer clients. It lets a client show what would be exported before
the user triggers a file-writing command.

## Module Boundary

The export target module already owns archive selection, export profiles, privacy mode handling, and manifest shape.
Therefore preview planning belongs there too. The client interface wraps that preview for client-facing discovery and
action hints.

## Read-Only Rule

Preview must not create output directories, write export files, or write `threadvault-export-manifest.json`. Tests assert
that the requested output directory does not exist after preview.

## Privacy Rule

The preview scans the same text shape used by export targets enough to report high-risk blocking in `fail` mode. The
actual export command remains responsible for writing redacted or skipped files.

## Deferred Decisions

- Whether future team mode should require an audit record for export preview reads.
- Whether preview should estimate byte sizes for large archives.
- Whether preview should include per-file rendered text hashes.


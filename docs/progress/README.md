# Progress Directory

This directory contains long-term development traces for ThreadVault.

## Structure

```text
docs/progress/
├─ README.md
├─ rounds/
├─ phases/
├─ releases/
└─ archive/
```

## Round Records

Each development round uses:

```text
YYYY-MM-DD-round-001-short-task-name.md
```

Use lowercase kebab-case for the task name. Continue an existing round file when the same round is still active.

## Legacy Records

Historical records from `docs/v0` through `docs/v4` and `docs/development-progress.md` now live under
`docs/progress/archive/` after user confirmation. Their internal legacy filenames are preserved as evidence. New
development traces must use the standard `rounds/`, `phases/`, or `releases/` locations.

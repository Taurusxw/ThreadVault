from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .audit import build_corpus_audit
from .config import discover_session_dirs
from .database import SessionWriter, has_imported, log_failed, log_skipped
from .parser import iter_normalized_events, scan_session_file, sha256_file
from .state import load_state_threads


@dataclass
class ImportStats:
    discovered: int = 0
    imported: int = 0
    skipped: int = 0
    failed: int = 0
    events: int = 0
    warnings: int = 0


def discover_jsonl_files(codex_home: Path | None = None) -> list[tuple[Path, bool]]:
    files: list[tuple[Path, bool]] = []
    dirs = discover_session_dirs(codex_home)
    for session_dir in dirs:
        if not session_dir.exists():
            continue
        archived = session_dir.name == "archived_sessions"
        for path in sorted(session_dir.rglob("*.jsonl")):
            if path.is_file():
                files.append((path, archived))
    return files


def sample_codex_home(codex_home: Path | None = None, limit: int | None = None, include_paths: bool = False) -> dict[str, Any]:
    from .parser import sample_session_file

    files = discover_jsonl_files(codex_home)
    if limit is not None:
        files = files[:limit]
    samples = [sample_session_file(path, archived=archived) for path, archived in files]
    source = str(codex_home) if include_paths and codex_home is not None else "<codex_home>"
    return build_corpus_audit(samples, include_paths=include_paths, source=source, limit=limit)


def import_codex_home(conn, codex_home: Path | None = None) -> ImportStats:
    return import_codex_files(conn, discover_jsonl_files(codex_home), codex_home=codex_home)


def import_codex_files(
    conn,
    files: list[tuple[Path, bool]],
    *,
    codex_home: Path | None = None,
) -> ImportStats:
    """Import a known set of transcripts while loading Codex state metadata once."""

    stats = ImportStats()
    state_threads = load_state_threads(codex_home)
    for path, archived in files:
        resolved = path.expanduser().resolve()
        _import_file(conn, resolved, archived, state_threads.get(resolved), stats)
    return stats


def import_codex_file(
    conn,
    path: Path,
    *,
    archived: bool | None = None,
    codex_home: Path | None = None,
) -> ImportStats:
    """Import one transcript file, primarily for turn-scoped Codex hooks."""
    path = path.expanduser().resolve()
    stats = ImportStats()
    if archived is None:
        archived = "archived_sessions" in path.parts
    state_threads = load_state_threads(codex_home)
    _import_file(conn, path, archived, state_threads.get(path), stats)
    return stats


def _import_file(conn, path: Path, archived: bool, state: dict[str, Any] | None, stats: ImportStats) -> None:
    stats.discovered += 1
    raw_hash: str | None = None
    try:
        if not path.is_file() or path.suffix.lower() != ".jsonl":
            raise FileNotFoundError(f"Codex transcript JSONL not found: {path}")
        raw_hash = sha256_file(path)
        if has_imported(conn, path, raw_hash):
            log_skipped(conn, path, raw_hash, "File already imported with same hash.")
            stats.skipped += 1
            return
        parsed = scan_session_file(path, archived=archived)
        enrich_from_state(parsed, state)
        with conn:
            writer = SessionWriter(conn, parsed)
            for event, warning in iter_normalized_events(path, fallback_session_id=parsed.session_id):
                if warning is not None:
                    writer.add_warning(warning)
                    stats.warnings += 1
                elif event is not None:
                    writer.add_event(event)
            stats.events += writer.finish()
        stats.imported += 1
    except Exception as exc:  # noqa: BLE001 - import must record failure without breaking Codex.
        log_failed(conn, path, raw_hash, str(exc))
        stats.failed += 1


def enrich_from_state(parsed, state: dict[str, Any] | None) -> None:
    if not state:
        return
    parsed.session_id = state.get("id") or parsed.session_id
    parsed.cwd = parsed.cwd or state.get("cwd")
    if parsed.source_kind == "unknown":
        parsed.source_kind = state.get("source") or state.get("thread_source") or "unknown"
    parsed.archived = bool(state.get("archived")) or parsed.archived
    parsed.updated_at = parsed.updated_at or state.get("updated_at")
    parsed.first_seen_at = parsed.first_seen_at or state.get("created_at")
    flags = dict(parsed.flags)
    flags["state_enriched"] = True
    for key in ("title", "preview", "model", "agent_path"):
        if state.get(key) is not None:
            flags[f"state_{key}"] = state[key]
    parsed.flags = flags

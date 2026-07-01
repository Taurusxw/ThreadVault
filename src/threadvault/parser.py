from __future__ import annotations

from pathlib import Path

from .codex_adapter import CodexJsonlAdapter

_ADAPTER = CodexJsonlAdapter()

sha256_file = _ADAPTER.sha256_file
iter_jsonl_records = _ADAPTER.iter_jsonl_records
parse_session_file = _ADAPTER.parse_session_file
scan_session_file = _ADAPTER.scan_session_file
iter_normalized_events = _ADAPTER.iter_normalized_events
normalize_record = _ADAPTER.normalize_record


def sample_session_file(path: Path, archived: bool = False):
    return _ADAPTER.sample_file(path, archived=archived)

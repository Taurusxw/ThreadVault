from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .backup_manifest import sha256_file
from .config import default_data_dir


def default_restore_history_path() -> Path:
    return default_data_dir() / "restore-history.jsonl"


def append_restore_history(restore_payload: dict[str, Any], history_path: Path | None = None) -> dict[str, Any]:
    path = (history_path or default_restore_history_path()).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = _record_from_restore_payload(restore_payload)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {"path": str(path), "record": record}


def list_restore_history(history_path: Path | None = None) -> dict[str, Any]:
    path = (history_path or default_restore_history_path()).expanduser()
    records: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    invalid_lines: list[str] = []
    if not path.exists():
        return {"history": str(path), "records": records, "warnings": warnings, "invalid_lines": invalid_lines}
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw_line = line
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                warnings.append({"line_no": line_no, "code": "invalid_history_json", "message": str(exc)})
                invalid_lines.append(raw_line)
                continue
            if not isinstance(record, dict):
                warnings.append({
                    "line_no": line_no,
                    "code": "history_record_not_object",
                    "message": "Restore history record must be an object.",
                })
                invalid_lines.append(raw_line)
                continue
            records.append(record)
    records.sort(key=lambda item: (str(item.get("restored_at") or ""), str(item.get("target_db") or "")))
    return {"history": str(path), "records": records, "warnings": warnings, "invalid_lines": invalid_lines}


def latest_restore_history(history_path: Path | None = None) -> dict[str, Any]:
    listing = list_restore_history(history_path)
    latest = listing["records"][-1] if listing["records"] else None
    return {**listing, "latest": latest}


def prune_restore_history(history_path: Path | None = None, keep: int = 10, apply: bool = False) -> dict[str, Any]:
    if keep < 1:
        raise ValueError("keep must be at least 1")
    listing = list_restore_history(history_path)
    records = listing["records"]
    kept = records[-keep:]
    deletable = records[: max(0, len(records) - keep)]
    rewritten = False
    if apply and Path(listing["history"]).exists():
        path = Path(listing["history"])
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for raw_line in listing["invalid_lines"]:
                handle.write(raw_line if raw_line.endswith("\n") else f"{raw_line}\n")
            for record in kept:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        rewritten = True
    return {
        **listing,
        "ok": True,
        "apply": apply,
        "keep": keep,
        "kept": kept,
        "deletable": deletable,
        "rewritten": rewritten,
    }


def _record_from_restore_payload(payload: dict[str, Any]) -> dict[str, Any]:
    target = Path(payload["target_db"]).expanduser()
    backup = Path(payload["backup"]).expanduser()
    pre_restore_backup = payload.get("pre_restore_backup")
    return {
        "record_version": "0.23",
        "restored_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "backup": str(backup),
        "target_db": str(target),
        "apply": payload["apply"],
        "overwrite": payload["overwrite"],
        "allow_missing_manifest": payload["allow_missing_manifest"],
        "backup_sha256": sha256_file(backup) if backup.exists() else None,
        "target_sha256": sha256_file(target) if target.exists() else None,
        "pre_restore_backup": pre_restore_backup.get("destination") if isinstance(pre_restore_backup, dict) else None,
        "schema_version": _nested_get(payload, ["restored_verification", "schema_version"]),
        "stats": _nested_get(payload, ["restored_verification", "stats"]),
    }


def _nested_get(payload: dict[str, Any], path: list[str]) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current

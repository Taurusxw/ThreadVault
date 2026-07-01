from __future__ import annotations

import gc
import time
from pathlib import Path
from typing import Any

from .database import verify_database_backup

BACKUP_GLOB = "threadvault-backup-*.db"


def list_backup_files(backup_dir: Path) -> dict[str, Any]:
    backups: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for path in sorted(backup_dir.glob(BACKUP_GLOB)):
        verified = verify_database_backup(path)
        if not verified["ok"]:
            warnings.append({
                "path": str(path),
                "code": "invalid_backup",
                "errors": verified["errors"],
            })
            continue
        backups.append({
            "path": str(path),
            "bytes": verified["bytes"],
            "schema_version": verified["schema_version"],
            "stats": verified["stats"],
        })
    backups.sort(key=lambda item: (Path(item["path"]).name, item["path"]))
    return {"dir": str(backup_dir), "backups": backups, "warnings": warnings}


def latest_backup_file(backup_dir: Path) -> dict[str, Any]:
    listing = list_backup_files(backup_dir)
    latest = listing["backups"][-1] if listing["backups"] else None
    return {**listing, "latest": latest}


def verify_latest_backup(backup_dir: Path) -> dict[str, Any]:
    payload = latest_backup_file(backup_dir)
    latest = payload["latest"]
    if latest is None:
        return {
            **payload,
            "ok": False,
            "error": "no_valid_backups",
            "verification": None,
        }
    verification = verify_database_backup(Path(latest["path"]))
    return {
        **payload,
        "ok": verification["ok"],
        "error": None if verification["ok"] else "latest_backup_invalid",
        "verification": verification,
    }


def prune_backup_history(backup_dir: Path, keep: int, apply: bool = False) -> dict[str, Any]:
    if keep < 1:
        raise ValueError("keep must be at least 1")
    listing = list_backup_files(backup_dir)
    backups = listing["backups"]
    kept = backups[-keep:]
    deletable = backups[: max(0, len(backups) - keep)]
    deleted: list[str] = []
    if apply:
        gc.collect()
        for backup in deletable:
            path = Path(backup["path"])
            _unlink_with_retry(path)
            deleted.append(str(path))
    return {
        **listing,
        "ok": True,
        "apply": apply,
        "keep": keep,
        "kept": kept,
        "deletable": deletable,
        "deleted": deleted,
    }


def _unlink_with_retry(path: Path, attempts: int = 3, delay_seconds: float = 0.05) -> None:
    for attempt in range(attempts):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            gc.collect()
            time.sleep(delay_seconds)

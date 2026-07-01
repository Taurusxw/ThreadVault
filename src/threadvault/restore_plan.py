from __future__ import annotations

from pathlib import Path
from typing import Any

from .backup_manifest import verify_backup_manifest
from .database import verify_database_backup


def build_restore_plan(backup: Path, target_db: Path) -> dict[str, Any]:
    backup = backup.expanduser()
    target_db = target_db.expanduser()
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    recommended_actions: list[str] = []

    backup_verification = verify_database_backup(backup)
    manifest_verification = verify_backup_manifest(backup)
    if not backup_verification["ok"]:
        errors.append({"code": "backup_verification_failed", "message": "Backup database verification failed."})
        recommended_actions.append("Run threadvault backup-verify --backup <backup> --json and inspect errors before restore.")
    if not manifest_verification["ok"]:
        manifest_codes = {error["code"] for error in manifest_verification["errors"]}
        if manifest_codes == {"manifest_missing"}:
            warnings.append({
                "code": "manifest_missing",
                "message": "Backup manifest is missing; this may be a legacy backup created before manifests were added.",
            })
            recommended_actions.append("Prefer a backup with a valid manifest when available.")
        else:
            errors.append({"code": "manifest_verification_failed", "message": "Backup manifest verification failed."})
            recommended_actions.append("Run threadvault backup-manifest --backup <backup> --json and inspect errors before restore.")

    target_status = _target_status(backup, target_db)
    if target_status["same_as_backup"]:
        errors.append({"code": "target_same_as_backup", "message": "Restore target must not be the backup file itself."})
    if not target_status["parent_exists"]:
        warnings.append({"code": "target_parent_missing", "message": "Target parent directory does not exist yet."})
        recommended_actions.append("Create the target parent directory before running any future restore command.")
    if target_status["exists"]:
        warnings.append({
            "code": "target_exists",
            "message": "Target database already exists and would require explicit overwrite handling.",
        })
        recommended_actions.append("Create a fresh backup of the current target database before any future overwrite-capable restore.")

    if not errors:
        recommended_actions.append("Review this plan, then use a future explicit restore command only after backing up the current target.")

    return {
        "ok": not errors,
        "mode": "read_only_plan",
        "backup": str(backup),
        "target_db": str(target_db),
        "backup_verification": backup_verification,
        "manifest_verification": manifest_verification,
        "target": target_status,
        "errors": errors,
        "warnings": warnings,
        "recommended_actions": _dedupe(recommended_actions),
    }


def _target_status(backup: Path, target_db: Path) -> dict[str, Any]:
    parent = target_db.parent
    return {
        "path": str(target_db),
        "exists": target_db.exists(),
        "parent": str(parent),
        "parent_exists": parent.exists(),
        "same_as_backup": _same_path(backup, target_db),
    }


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left.absolute() == right.absolute()


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

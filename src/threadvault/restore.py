from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .backup_manifest import write_backup_manifest
from .database import backup_database, verify_database_backup
from .restore_history import append_restore_history
from .restore_plan import build_restore_plan


def restore_backup(
    backup: Path,
    target_db: Path,
    apply: bool = False,
    overwrite: bool = False,
    pre_restore_backup_dir: Path | None = None,
    allow_missing_manifest: bool = False,
    restore_history: Path | None = None,
) -> dict[str, Any]:
    backup = backup.expanduser()
    target_db = target_db.expanduser()
    plan = build_restore_plan(backup, target_db)
    errors = list(plan["errors"])
    warnings = list(plan["warnings"])
    pre_restore_backup = None
    restored_verification = None
    restored_doctor = None
    history = None

    manifest_missing = _has_manifest_missing_warning(plan)
    if manifest_missing and not allow_missing_manifest:
        errors.append({
            "code": "manifest_required",
            "message": "Backup manifest is missing; pass --allow-missing-manifest for legacy backups.",
        })
    if target_db.exists() and not overwrite:
        errors.append({"code": "target_exists_without_overwrite", "message": "Target exists; pass --overwrite to replace it."})
    if apply and target_db.exists() and overwrite and pre_restore_backup_dir is None:
        errors.append({
            "code": "pre_restore_backup_required",
            "message": "Pass --pre-restore-backup-dir before overwriting an existing target.",
        })

    ok_to_apply = not errors
    if apply and ok_to_apply:
        target_db.parent.mkdir(parents=True, exist_ok=True)
        if target_db.exists() and overwrite:
            assert pre_restore_backup_dir is not None
            pre_restore_backup = backup_database(target_db, pre_restore_backup_dir, force=False)
            if not pre_restore_backup["ok"]:
                errors.append({"code": "pre_restore_backup_failed", "message": "Could not create pre-restore backup."})
                ok_to_apply = False
        if ok_to_apply:
            shutil.copy2(backup, target_db)
            restored_verification = verify_database_backup(target_db)
            if restored_verification["ok"]:
                write_backup_manifest({
                    "destination": str(target_db),
                    "source_db": str(backup),
                    "schema_version": restored_verification["schema_version"],
                    "stats": restored_verification["stats"],
                })
            restored_doctor = restored_verification.get("doctor")
            if not restored_verification["ok"]:
                errors.append({"code": "restored_verification_failed", "message": "Restored database verification failed."})

    payload = {
        "ok": not errors,
        "mode": "applied" if apply and not errors else "dry_run",
        "apply": apply,
        "overwrite": overwrite,
        "allow_missing_manifest": allow_missing_manifest,
        "backup": str(backup),
        "target_db": str(target_db),
        "plan": plan,
        "pre_restore_backup": pre_restore_backup,
        "restored_verification": restored_verification,
        "restored_doctor": restored_doctor,
        "history": history,
        "errors": errors,
        "warnings": warnings,
    }
    if payload["ok"] and payload["apply"]:
        payload["history"] = append_restore_history(payload, restore_history)
    return payload


def _has_manifest_missing_warning(plan: dict[str, Any]) -> bool:
    return any(warning.get("code") == "manifest_missing" for warning in plan.get("warnings", []))

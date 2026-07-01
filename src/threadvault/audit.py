from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPORT_VERSION = "0.8"
REPORT_GLOB = "threadvault-audit-*.json"
PRIVACY_NOTE = (
    "Default corpus audit output omits raw transcript text, raw absolute paths, and raw session IDs. "
    "Use --include-paths only for local debugging."
)


def anonymize_sample(sample: dict[str, Any], salt: str, include_paths: bool = False) -> dict[str, Any]:
    sample_id = _sample_id(sample, salt)
    output = {
        "sample_id": sample_id,
        "events": sample["events"],
        "warnings": sample["warnings"],
        "classifications": sample["classifications"],
        "warning_codes": sample["warning_codes"],
    }
    if include_paths:
        output["path"] = sample.get("path")
        output["session_id"] = sample.get("session_id")
    return output


def build_corpus_audit(
    samples: list[dict[str, Any]],
    include_paths: bool = False,
    salt: str | None = None,
    source: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    audit_salt = salt or secrets.token_hex(16)
    warning_codes: dict[str, int] = {}
    classifications: dict[str, int] = {}
    total_events = 0
    total_warnings = 0
    for sample in samples:
        total_events += int(sample["events"])
        total_warnings += int(sample["warnings"])
        for code, count in sample["warning_codes"].items():
            warning_codes[code] = warning_codes.get(code, 0) + int(count)
        for classification, count in sample["classifications"].items():
            classifications[classification] = classifications.get(classification, 0) + int(count)
    total_files = len(samples)
    parseable_files = sum(1 for sample in samples if sample["events"] > 0)
    return {
        "report_version": REPORT_VERSION,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": source,
        "limit": limit,
        "privacy_note": PRIVACY_NOTE,
        "include_paths": include_paths,
        "files": total_files,
        "parseable_files": parseable_files,
        "parseable_ratio": (parseable_files / total_files) if total_files else 0,
        "events": total_events,
        "warnings": total_warnings,
        "warning_codes": dict(sorted(warning_codes.items())),
        "classifications": dict(sorted(classifications.items())),
        "samples": [anonymize_sample(sample, audit_salt, include_paths=include_paths) for sample in samples],
    }


def write_audit_report(report: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = str(report["generated_at"]).replace(":", "").replace("-", "")
    path = out_dir / f"threadvault-audit-{timestamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_audit_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def list_audit_reports(report_dir: Path) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for path in sorted(report_dir.glob(REPORT_GLOB)):
        try:
            report = load_audit_report(path)
        except Exception as exc:  # noqa: BLE001 - history listing must keep going.
            warnings.append({"path": str(path), "code": "invalid_report_json", "message": str(exc)})
            continue
        generated_at = report.get("generated_at")
        reports.append({
            "path": str(path),
            "generated_at": generated_at,
            "report_version": report.get("report_version"),
            "files": report.get("files"),
            "warnings": report.get("warnings"),
            "parseable_ratio": report.get("parseable_ratio"),
            "include_paths": report.get("include_paths", False),
        })
    reports.sort(key=lambda item: (str(item.get("generated_at") or ""), item["path"]))
    return {"dir": str(report_dir), "reports": reports, "warnings": warnings}


def latest_audit_report(report_dir: Path) -> dict[str, Any]:
    listing = list_audit_reports(report_dir)
    latest = listing["reports"][-1] if listing["reports"] else None
    return {**listing, "latest": latest}


def diff_latest_audit_reports(report_dir: Path) -> dict[str, Any]:
    listing = list_audit_reports(report_dir)
    reports = listing["reports"]
    if len(reports) < 2:
        return {
            **listing,
            "ok": False,
            "error": "not_enough_reports",
            "diff": None,
        }
    before = reports[-2]
    after = reports[-1]
    diff = diff_audit_reports(load_audit_report(Path(before["path"])), load_audit_report(Path(after["path"])))
    return {
        **listing,
        "ok": True,
        "before": before,
        "after": after,
        "diff": diff,
    }


def prune_audit_history(report_dir: Path, keep: int, apply: bool = False) -> dict[str, Any]:
    if keep < 1:
        raise ValueError("keep must be at least 1")
    listing = list_audit_reports(report_dir)
    reports = listing["reports"]
    kept = reports[-keep:]
    deletable = reports[: max(0, len(reports) - keep)]
    deleted: list[str] = []
    if apply:
        for report in deletable:
            path = Path(report["path"])
            path.unlink(missing_ok=True)
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


def diff_audit_reports(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    warning_deltas = _counter_delta(before.get("warning_codes", {}), after.get("warning_codes", {}))
    classification_deltas = _counter_delta(before.get("classifications", {}), after.get("classifications", {}))
    warning_delta = int(after.get("warnings", 0)) - int(before.get("warnings", 0))
    parseable_ratio_delta = float(after.get("parseable_ratio", 0)) - float(before.get("parseable_ratio", 0))
    return {
        "report_version": REPORT_VERSION,
        "before_generated_at": before.get("generated_at"),
        "after_generated_at": after.get("generated_at"),
        "files_delta": int(after.get("files", 0)) - int(before.get("files", 0)),
        "events_delta": int(after.get("events", 0)) - int(before.get("events", 0)),
        "warnings_delta": warning_delta,
        "parseable_ratio_delta": parseable_ratio_delta,
        "warning_code_deltas": warning_deltas,
        "classification_deltas": classification_deltas,
        "regressions": {
            "warnings_increased": warning_delta > 0,
            "parseable_ratio_decreased": parseable_ratio_delta < 0,
            "new_warning_codes": sorted(
                code
                for code, delta in warning_deltas.items()
                if delta > 0 and code not in before.get("warning_codes", {})
            ),
        },
    }


def _sample_id(sample: dict[str, Any], salt: str) -> str:
    identity = f"{sample.get('path', '')}\0{sample.get('session_id', '')}"
    digest = hashlib.sha256(f"{salt}\0{identity}".encode("utf-8", errors="replace")).hexdigest()
    return f"sample-{digest[:16]}"


def _counter_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, int]:
    keys = set(before) | set(after)
    return {key: int(after.get(key, 0)) - int(before.get(key, 0)) for key in sorted(keys)}


def path_is_disclosed(payload: dict[str, Any], path: Path) -> bool:
    return str(path) in str(payload)

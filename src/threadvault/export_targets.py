from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .app_config import AppConfig, load_app_config
from .database import get_events_filtered, get_project_sessions, get_sessions_by_ids
from .exporter import export_project_markdown, export_session
from .privacy import PrivacyFinding, effective_findings, has_high_risk, redact_sensitive_text, scan_sensitive_text
from .summarizer import build_summary

MANIFEST_VERSION = "1"
MANIFEST_NAME = "threadvault-export-manifest.json"
OBSIDIAN_TEXT_LIMIT = 4000
SKILL_EVIDENCE_SNIPPET_LIMIT = 700


@dataclass(frozen=True)
class ExportTargetRequest:
    out_dir: Path
    profile: str = "markdown"
    session_ids: list[str] = field(default_factory=list)
    project: str | None = None
    privacy_mode: str = "warn"
    privacy_config_path: Path | None = None
    skill_name: str | None = None
    skill_description: str | None = None


@dataclass
class ArchiveSelection:
    explicit_session_ids: list[str]
    selected: list[sqlite3.Row]
    project_sessions: list[sqlite3.Row]
    skipped: list[dict[str, Any]]


def export_target(conn: sqlite3.Connection, request: ExportTargetRequest) -> dict[str, Any]:
    if request.profile not in {"markdown", "obsidian", "skill"}:
        raise ValueError("profile must be markdown, obsidian, or skill.")
    if request.privacy_mode not in {"warn", "redact", "fail"}:
        raise ValueError("privacy_mode must be warn, redact, or fail.")
    if not request.session_ids and not request.project:
        raise ValueError("Provide at least one session id or project cwd.")

    root = request.out_dir.expanduser()
    root.mkdir(parents=True, exist_ok=True)
    config = load_app_config(request.privacy_config_path)
    selection = _select_archive(conn, request)

    if request.profile == "markdown":
        files, findings, evidence_ids = _export_markdown_target(conn, request, root, selection, config)
    elif request.profile == "obsidian":
        files, findings, evidence_ids = _export_obsidian_target(conn, request, root, selection, config)
    else:
        files, findings, evidence_ids = _export_skill_target(conn, request, root, selection, config)

    manifest = _build_manifest(
        request=request,
        root=root,
        selection=selection,
        files=files,
        skipped=selection.skipped,
        findings=findings,
        evidence_ids=evidence_ids,
    )
    _write_manifest(root, manifest)
    return manifest


def preview_export_target(conn: sqlite3.Connection, request: ExportTargetRequest) -> dict[str, Any]:
    if request.profile not in {"markdown", "obsidian", "skill"}:
        raise ValueError("profile must be markdown, obsidian, or skill.")
    if request.privacy_mode not in {"warn", "redact", "fail"}:
        raise ValueError("privacy_mode must be warn, redact, or fail.")
    if not request.session_ids and not request.project:
        raise ValueError("Provide at least one session id or project cwd.")

    root = request.out_dir.expanduser()
    config = load_app_config(request.privacy_config_path)
    selection = _select_archive(conn, request)
    files, findings, evidence_ids = _preview_files(conn, request, root, selection, config)
    return {
        "manifest_version": MANIFEST_VERSION,
        "target_profile": request.profile,
        "generated_at": _utc_now(),
        "root": str(root),
        "selection": {
            "sessions": selection.explicit_session_ids,
            "project": request.project,
            "selected_session_ids": [row["session_id"] for row in selection.selected],
        },
        "files": files,
        "skipped": selection.skipped,
        "privacy": _privacy_summary(request.privacy_mode, findings),
        "evidence": {
            "event_ids": sorted(set(evidence_ids)),
            "sessions_with_evidence": sorted({
                item["session_id"]
                for item in files
                if item["session_id"] is not None and item["evidence_event_ids"]
            }),
        },
        "diagnostics": {
            "preview": True,
            "writes_files": False,
            "manifest_written": False,
            "planned_file_count": len(files),
            "skipped_count": len(selection.skipped),
        },
    }


def _select_archive(conn: sqlite3.Connection, request: ExportTargetRequest) -> ArchiveSelection:
    explicit_session_ids = _dedupe(request.session_ids)
    explicit_sessions = get_sessions_by_ids(conn, explicit_session_ids)
    explicit_found = {row["session_id"] for row in explicit_sessions}
    skipped: list[dict[str, Any]] = [
        {"kind": "session", "session_id": session_id, "reason": "session_not_found"}
        for session_id in explicit_session_ids
        if session_id not in explicit_found
    ]

    selected: list[sqlite3.Row] = list(explicit_sessions)
    project_sessions: list[sqlite3.Row] = []
    if request.project:
        project_sessions = get_project_sessions(conn, request.project)
        if project_sessions:
            selected.extend(project_sessions)
        else:
            skipped.append({"kind": "project", "project": request.project, "reason": "project_has_no_sessions"})

    return ArchiveSelection(
        explicit_session_ids=explicit_session_ids,
        selected=_dedupe_session_rows(selected),
        project_sessions=project_sessions,
        skipped=skipped,
    )


def _preview_files(
    conn: sqlite3.Connection,
    request: ExportTargetRequest,
    root: Path,
    selection: ArchiveSelection,
    config: AppConfig,
) -> tuple[list[dict[str, Any]], list[PrivacyFinding], list[int]]:
    if request.profile == "markdown":
        return _preview_markdown_target(conn, request, root, selection, config)
    if request.profile == "obsidian":
        return _preview_obsidian_target(conn, request, root, selection, config)
    return _preview_skill_target(conn, request, root, selection, config)


def _preview_markdown_target(
    conn: sqlite3.Connection,
    request: ExportTargetRequest,
    root: Path,
    selection: ArchiveSelection,
    config: AppConfig,
) -> tuple[list[dict[str, Any]], list[PrivacyFinding], list[int]]:
    files: list[dict[str, Any]] = []
    all_findings: list[PrivacyFinding] = []
    all_evidence_ids: list[int] = []
    if request.project and selection.project_sessions:
        summaries = []
        for session in selection.project_sessions:
            events = get_events_filtered(conn, session["session_id"])
            summaries.append(build_summary(session, events))
        text = _project_markdown_preview_text(request.project, selection.project_sessions, summaries)
        project_findings = scan_sensitive_text(text, allowlist=config.allowlist)
        evidence_ids = _summary_evidence_ids(summaries)
        all_findings.extend(project_findings)
        all_evidence_ids.extend(evidence_ids)
        files.append(_planned_file("project_index", None, "project-index.md", len(project_findings), evidence_ids))

    for session in selection.selected:
        events = get_events_filtered(conn, session["session_id"])
        summary = build_summary(session, events)
        text = _session_export_preview_text(session, events, summary)
        findings = scan_sensitive_text(text, allowlist=config.allowlist)
        all_findings.extend(findings)
        if request.privacy_mode == "fail" and has_high_risk(findings):
            selection.skipped.append({
                "kind": "session",
                "session_id": session["session_id"],
                "reason": "high_risk_privacy_findings",
                "privacy_findings_count": len(findings),
            })
            continue
        evidence_ids = list(summary.evidence_event_ids)
        all_evidence_ids.extend(evidence_ids)
        files.append(_planned_file("session", session["session_id"], f"sessions/{session['session_id']}.md", len(findings), evidence_ids))
    return files, all_findings, all_evidence_ids


def _preview_obsidian_target(
    conn: sqlite3.Connection,
    request: ExportTargetRequest,
    root: Path,
    selection: ArchiveSelection,
    config: AppConfig,
) -> tuple[list[dict[str, Any]], list[PrivacyFinding], list[int]]:
    files: list[dict[str, Any]] = []
    all_findings: list[PrivacyFinding] = []
    all_evidence_ids: list[int] = []
    exported_sessions = []
    for session in selection.selected:
        events = get_events_filtered(conn, session["session_id"])
        summary = build_summary(session, events)
        evidence_events = _events_by_id(events, summary.evidence_event_ids)
        summary_path = root / "sessions" / f"{session['session_id']}.md"
        evidence_path = root / "evidence" / f"{session['session_id']}-evidence.md"
        summary_text = _session_summary_page(session, summary, evidence_path, root)
        evidence_text = _session_evidence_page(session, summary_path, evidence_events, root)
        findings = scan_sensitive_text(summary_text + "\n" + evidence_text, allowlist=config.allowlist)
        all_findings.extend(findings)
        if request.privacy_mode == "fail" and has_high_risk(findings):
            selection.skipped.append({
                "kind": "session",
                "session_id": session["session_id"],
                "reason": "high_risk_privacy_findings",
                "privacy_findings_count": len(findings),
            })
            continue
        evidence_ids = list(summary.evidence_event_ids)
        all_evidence_ids.extend(evidence_ids)
        files.append(
            _planned_file("session_summary", session["session_id"], f"sessions/{session['session_id']}.md", len(findings), evidence_ids)
        )
        files.append(
            _planned_file(
                "session_evidence",
                session["session_id"],
                f"evidence/{session['session_id']}-evidence.md",
                len(findings),
                evidence_ids,
            )
        )
        exported_sessions.append({
            "session": session,
            "summary_path": summary_path,
            "evidence_path": evidence_path,
            "summary": summary,
            "root": root,
        })
    index_text = _vault_index_page(request, exported_sessions, selection.skipped, request.privacy_mode, all_findings)
    index_findings = scan_sensitive_text(index_text, allowlist=config.allowlist)
    all_findings.extend(index_findings)
    files.insert(0, _planned_file("vault_index", None, "index.md", len(index_findings), sorted(set(all_evidence_ids))))
    return files, all_findings, all_evidence_ids


def _preview_skill_target(
    conn: sqlite3.Connection,
    request: ExportTargetRequest,
    root: Path,
    selection: ArchiveSelection,
    config: AppConfig,
) -> tuple[list[dict[str, Any]], list[PrivacyFinding], list[int]]:
    session_bundles: list[dict[str, Any]] = []
    all_findings: list[PrivacyFinding] = []
    all_evidence_ids: list[int] = []
    for session in selection.selected:
        events = get_events_filtered(conn, session["session_id"])
        summary = build_summary(session, events)
        evidence_events = _events_by_id(events, summary.evidence_event_ids)
        session_text = _skill_session_section(session, summary)
        evidence_text = _skill_evidence_section(session, evidence_events)
        findings = scan_sensitive_text(session_text + "\n" + evidence_text, allowlist=config.allowlist)
        all_findings.extend(findings)
        if request.privacy_mode == "fail" and has_high_risk(findings):
            selection.skipped.append({
                "kind": "session",
                "session_id": session["session_id"],
                "reason": "high_risk_privacy_findings",
                "privacy_findings_count": len(findings),
            })
            continue
        session_bundles.append({"session": session, "summary": summary, "evidence_events": evidence_events})
        all_evidence_ids.extend(summary.evidence_event_ids)
    skill_name = _normalize_skill_name(request.skill_name or _default_skill_name(request.project, session_bundles))
    skill_description = request.skill_description or _default_skill_description(skill_name, request.project)
    skill_text = _skill_markdown(skill_name, skill_description)
    index_text = _skill_index_reference(request, session_bundles, selection.skipped)
    sessions_text = _skill_sessions_reference(request, session_bundles, selection.skipped)
    evidence_text = _skill_evidence_reference(session_bundles)
    skill_findings = scan_sensitive_text(skill_text, allowlist=config.allowlist)
    index_findings = scan_sensitive_text(index_text, allowlist=config.allowlist)
    sessions_findings = scan_sensitive_text(sessions_text, allowlist=config.allowlist)
    evidence_findings = scan_sensitive_text(evidence_text, allowlist=config.allowlist)
    all_findings.extend(skill_findings)
    all_findings.extend(index_findings)
    all_findings.extend(sessions_findings)
    all_findings.extend(evidence_findings)
    evidence_ids = sorted(set(all_evidence_ids))
    files = [
        _planned_file("skill_file", None, "SKILL.md", len(skill_findings), evidence_ids),
        _planned_file("skill_reference", None, "references/index.md", len(index_findings), evidence_ids),
        _planned_file("skill_reference", None, "references/sessions.md", len(sessions_findings), evidence_ids),
        _planned_file("skill_reference", None, "references/evidence.md", len(evidence_findings), evidence_ids),
    ]
    for bundle in session_bundles:
        session_text = _skill_session_reference(bundle)
        session_findings = scan_sensitive_text(session_text, allowlist=config.allowlist)
        all_findings.extend(session_findings)
        files.append(
            _planned_file(
                "skill_session_reference",
                bundle["session"]["session_id"],
                _skill_session_reference_relpath(bundle["session"]["session_id"]),
                len(session_findings),
                list(bundle["summary"].evidence_event_ids),
            )
        )
    return files, all_findings, evidence_ids


def _planned_file(kind: str, session_id: str | None, path: str, findings_count: int, evidence_event_ids: list[int]) -> dict[str, Any]:
    return {
        "kind": kind,
        "session_id": session_id,
        "path": path,
        "format": "md",
        "privacy_findings_count": findings_count,
        "evidence_event_ids": evidence_event_ids,
    }


def _project_markdown_preview_text(cwd: str, sessions: list[sqlite3.Row], summaries) -> str:
    lines = ["# ThreadVault Project Archive", "", f"- Project: `{cwd}`", f"- Sessions: {len(sessions)}", ""]
    for session in sessions:
        lines.append(f"- `{session['session_id']}`")
    for summary in summaries:
        lines.extend(["", f"## {summary.topic}", "", f"- Session: `{summary.session_id}`"])
        if summary.user_goal:
            lines.append(f"- User goal: {summary.user_goal}")
    return "\n".join(lines) + "\n"


def _session_export_preview_text(session: sqlite3.Row, events: list[sqlite3.Row], summary) -> str:
    lines = [
        f"# ThreadVault Session {session['session_id']}",
        "",
        f"- Project: `{session['cwd'] or ''}`",
        f"- Raw path: `{session['raw_path']}`",
        "",
        "## Summary",
        "",
        summary.topic,
        "",
        "## Timeline",
        "",
    ]
    for event in events:
        lines.append(f"### Event {event['event_id']}: {event['top_type']}")
        if event["file_path"]:
            lines.append(f"- File: `{event['file_path']}`")
        if event["text_content"]:
            lines.append(event["text_content"])
    return "\n".join(lines) + "\n"


def _export_markdown_target(
    conn: sqlite3.Connection,
    request: ExportTargetRequest,
    root: Path,
    selection: ArchiveSelection,
    config: AppConfig,
) -> tuple[list[dict[str, Any]], list[PrivacyFinding], list[int]]:
    sessions_dir = root / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    all_findings: list[PrivacyFinding] = []
    all_evidence_ids: list[int] = []

    if request.project and selection.project_sessions:
        summaries = []
        for session in selection.project_sessions:
            events = get_events_filtered(conn, session["session_id"])
            summaries.append(build_summary(session, events))
        project_path, project_findings = export_project_markdown(request.project, selection.project_sessions, root, summaries=summaries)
        all_findings.extend(project_findings)
        evidence_ids = _summary_evidence_ids(summaries)
        all_evidence_ids.extend(evidence_ids)
        files.append({
            "kind": "project_index",
            "session_id": None,
            "path": _relative_path(project_path, root),
            "format": "md",
            "privacy_findings_count": len(project_findings),
            "evidence_event_ids": evidence_ids,
        })

    for session in selection.selected:
        events = get_events_filtered(conn, session["session_id"])
        summary = build_summary(session, events)
        path, findings = export_session(
            session,
            events,
            sessions_dir,
            fmt="md",
            privacy_mode=request.privacy_mode,
            privacy_config=config,
        )
        if request.privacy_mode == "fail" and has_high_risk(findings):
            selection.skipped.append({
                "kind": "session",
                "session_id": session["session_id"],
                "reason": "high_risk_privacy_findings",
                "privacy_findings_count": len(findings),
            })
            all_findings.extend(findings)
            continue
        evidence_ids = list(summary.evidence_event_ids)
        all_findings.extend(findings)
        all_evidence_ids.extend(evidence_ids)
        files.append({
            "kind": "session",
            "session_id": session["session_id"],
            "path": _relative_path(path, root),
            "format": "md",
            "privacy_findings_count": len(findings),
            "evidence_event_ids": evidence_ids,
        })

    return files, all_findings, all_evidence_ids


def _export_obsidian_target(
    conn: sqlite3.Connection,
    request: ExportTargetRequest,
    root: Path,
    selection: ArchiveSelection,
    config: AppConfig,
) -> tuple[list[dict[str, Any]], list[PrivacyFinding], list[int]]:
    sessions_dir = root / "sessions"
    evidence_dir = root / "evidence"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    files: list[dict[str, Any]] = []
    all_findings: list[PrivacyFinding] = []
    all_evidence_ids: list[int] = []
    exported_sessions: list[dict[str, Any]] = []

    for session in selection.selected:
        events = get_events_filtered(conn, session["session_id"])
        summary = build_summary(session, events)
        evidence_events = _events_by_id(events, summary.evidence_event_ids)
        summary_path = sessions_dir / f"{session['session_id']}.md"
        evidence_path = evidence_dir / f"{session['session_id']}-evidence.md"
        summary_text = _session_summary_page(session, summary, evidence_path, root)
        evidence_text = _session_evidence_page(session, summary_path, evidence_events, root)

        combined_findings = scan_sensitive_text(summary_text + "\n" + evidence_text, allowlist=config.allowlist)
        if request.privacy_mode == "fail" and has_high_risk(combined_findings):
            selection.skipped.append({
                "kind": "session",
                "session_id": session["session_id"],
                "reason": "high_risk_privacy_findings",
                "privacy_findings_count": len(combined_findings),
            })
            all_findings.extend(combined_findings)
            continue

        written_summary, summary_findings = _write_privacy_checked_text(
            summary_path,
            summary_text,
            privacy_mode=request.privacy_mode,
            config=config,
        )
        written_evidence, evidence_findings = _write_privacy_checked_text(
            evidence_path,
            evidence_text,
            privacy_mode=request.privacy_mode,
            config=config,
        )
        all_findings.extend(summary_findings)
        all_findings.extend(evidence_findings)
        evidence_ids = list(summary.evidence_event_ids)
        all_evidence_ids.extend(evidence_ids)

        if written_summary:
            files.append({
                "kind": "session_summary",
                "session_id": session["session_id"],
                "path": _relative_path(summary_path, root),
                "format": "md",
                "privacy_findings_count": len(summary_findings),
                "evidence_event_ids": evidence_ids,
            })
        if written_evidence:
            files.append({
                "kind": "session_evidence",
                "session_id": session["session_id"],
                "path": _relative_path(evidence_path, root),
                "format": "md",
                "privacy_findings_count": len(evidence_findings),
                "evidence_event_ids": evidence_ids,
            })
        if written_summary and written_evidence:
            exported_sessions.append({
                "session": session,
                "summary_path": summary_path,
                "evidence_path": evidence_path,
                "summary": summary,
                "root": root,
            })

    index_path = root / "index.md"
    index_text = _vault_index_page(
        request=request,
        exported_sessions=exported_sessions,
        skipped=selection.skipped,
        privacy_mode=request.privacy_mode,
        findings=all_findings,
    )
    _, index_findings = _write_privacy_checked_text(index_path, index_text, privacy_mode=request.privacy_mode, config=config)
    all_findings.extend(index_findings)
    files.insert(0, {
        "kind": "vault_index",
        "session_id": None,
        "path": _relative_path(index_path, root),
        "format": "md",
        "privacy_findings_count": len(index_findings),
        "evidence_event_ids": sorted(set(all_evidence_ids)),
    })
    return files, all_findings, all_evidence_ids


def _export_skill_target(
    conn: sqlite3.Connection,
    request: ExportTargetRequest,
    root: Path,
    selection: ArchiveSelection,
    config: AppConfig,
) -> tuple[list[dict[str, Any]], list[PrivacyFinding], list[int]]:
    references_dir = root / "references"
    references_dir.mkdir(parents=True, exist_ok=True)

    session_bundles: list[dict[str, Any]] = []
    skipped = selection.skipped
    all_findings: list[PrivacyFinding] = []
    all_evidence_ids: list[int] = []

    for session in selection.selected:
        events = get_events_filtered(conn, session["session_id"])
        summary = build_summary(session, events)
        evidence_events = _events_by_id(events, summary.evidence_event_ids)
        session_text = _skill_session_section(session, summary)
        evidence_text = _skill_evidence_section(session, evidence_events)
        combined_findings = scan_sensitive_text(session_text + "\n" + evidence_text, allowlist=config.allowlist)
        if request.privacy_mode == "fail" and has_high_risk(combined_findings):
            skipped.append({
                "kind": "session",
                "session_id": session["session_id"],
                "reason": "high_risk_privacy_findings",
                "privacy_findings_count": len(combined_findings),
            })
            all_findings.extend(combined_findings)
            continue
        session_bundles.append({
            "session": session,
            "summary": summary,
            "evidence_events": evidence_events,
        })
        all_findings.extend(combined_findings)
        all_evidence_ids.extend(summary.evidence_event_ids)

    skill_name = _normalize_skill_name(request.skill_name or _default_skill_name(request.project, session_bundles))
    skill_description = request.skill_description or _default_skill_description(skill_name, request.project)
    skill_path = root / "SKILL.md"
    index_path = references_dir / "index.md"
    sessions_path = references_dir / "sessions.md"
    evidence_path = references_dir / "evidence.md"

    skill_text = _skill_markdown(skill_name, skill_description)
    index_text = _skill_index_reference(request, session_bundles, skipped)
    sessions_text = _skill_sessions_reference(request, session_bundles, skipped)
    evidence_text = _skill_evidence_reference(session_bundles)

    _, skill_findings = _write_privacy_checked_text(skill_path, skill_text, privacy_mode=request.privacy_mode, config=config)
    _, index_findings = _write_privacy_checked_text(index_path, index_text, privacy_mode=request.privacy_mode, config=config)
    _, sessions_findings = _write_privacy_checked_text(sessions_path, sessions_text, privacy_mode=request.privacy_mode, config=config)
    _, evidence_findings = _write_privacy_checked_text(evidence_path, evidence_text, privacy_mode=request.privacy_mode, config=config)

    all_findings.extend(skill_findings)
    all_findings.extend(index_findings)
    all_findings.extend(sessions_findings)
    all_findings.extend(evidence_findings)
    evidence_ids = sorted(set(all_evidence_ids))
    files = [
        {
            "kind": "skill_file",
            "session_id": None,
            "path": _relative_path(skill_path, root),
            "format": "md",
            "privacy_findings_count": len(skill_findings),
            "evidence_event_ids": evidence_ids,
        },
        {
            "kind": "skill_reference",
            "session_id": None,
            "path": _relative_path(index_path, root),
            "format": "md",
            "privacy_findings_count": len(index_findings),
            "evidence_event_ids": evidence_ids,
        },
        {
            "kind": "skill_reference",
            "session_id": None,
            "path": _relative_path(sessions_path, root),
            "format": "md",
            "privacy_findings_count": len(sessions_findings),
            "evidence_event_ids": evidence_ids,
        },
        {
            "kind": "skill_reference",
            "session_id": None,
            "path": _relative_path(evidence_path, root),
            "format": "md",
            "privacy_findings_count": len(evidence_findings),
            "evidence_event_ids": evidence_ids,
        },
    ]
    for bundle in session_bundles:
        session_path = root / _skill_session_reference_relpath(bundle["session"]["session_id"])
        session_text = _skill_session_reference(bundle)
        _, session_findings = _write_privacy_checked_text(
            session_path,
            session_text,
            privacy_mode=request.privacy_mode,
            config=config,
        )
        all_findings.extend(session_findings)
        files.append({
            "kind": "skill_session_reference",
            "session_id": bundle["session"]["session_id"],
            "path": _relative_path(session_path, root),
            "format": "md",
            "privacy_findings_count": len(session_findings),
            "evidence_event_ids": list(bundle["summary"].evidence_event_ids),
        })
    return files, all_findings, evidence_ids


def _build_manifest(
    request: ExportTargetRequest,
    root: Path,
    selection: ArchiveSelection,
    files: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    findings: list[PrivacyFinding],
    evidence_ids: list[int],
) -> dict[str, Any]:
    return {
        "manifest_version": MANIFEST_VERSION,
        "target_profile": request.profile,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "root": str(root),
        "selection": {
            "sessions": selection.explicit_session_ids,
            "project": request.project,
            "selected_session_ids": [row["session_id"] for row in selection.selected],
        },
        "files": files,
        "skipped": skipped,
        "privacy": _privacy_summary(request.privacy_mode, findings),
        "evidence": {
            "event_ids": sorted(set(evidence_ids)),
            "sessions_with_evidence": sorted({
                item["session_id"]
                for item in files
                if item["session_id"] is not None and item["evidence_event_ids"]
            }),
        },
    }


def _write_manifest(root: Path, manifest: dict[str, Any]) -> None:
    manifest_path = root / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _write_privacy_checked_text(
    path: Path,
    text: str,
    privacy_mode: str,
    config: AppConfig,
) -> tuple[bool, list[PrivacyFinding]]:
    findings = scan_sensitive_text(text, allowlist=config.allowlist)
    if privacy_mode == "fail" and has_high_risk(findings):
        return False, findings
    if privacy_mode == "redact":
        text, findings = redact_sensitive_text(text, allowlist=config.allowlist)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True, findings


def _vault_index_page(
    request: ExportTargetRequest,
    exported_sessions: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    privacy_mode: str,
    findings: list[PrivacyFinding],
) -> str:
    effective = effective_findings(findings)
    lines = [
        "# ThreadVault Vault",
        "",
        f"- Generated: `{_utc_now()}`",
        "- Target profile: `obsidian`",
    ]
    if request.project:
        lines.append(f"- Project: `{request.project}`")
    lines.extend([
        f"- Exported sessions: {len(exported_sessions)}",
        f"- Skipped items: {len(skipped)}",
        f"- Privacy mode: `{privacy_mode}`",
        f"- Effective privacy findings: {len(effective)}",
        "",
        "## Sessions",
        "",
    ])
    if not exported_sessions:
        lines.append("- None exported.")
    for item in exported_sessions:
        session = item["session"]
        summary = item["summary"]
        session_link = _wiki_link(item["summary_path"], "Session", item["root"])
        evidence_link = _wiki_link(item["evidence_path"], "Evidence", item["root"])
        updated = f" updated `{session['updated_at']}`" if session["updated_at"] else ""
        lines.append(f"- `{session['session_id']}`{updated}: {session_link} / {evidence_link} - {summary.topic}")
    if skipped:
        lines.extend(["", "## Skipped", ""])
        for item in skipped:
            reason = item.get("reason", "unknown")
            label = item.get("session_id") or item.get("project") or item.get("kind")
            lines.append(f"- `{label}`: {reason}")
    return "\n".join(lines) + "\n"


def _session_summary_page(session: sqlite3.Row, summary, evidence_path: Path, root: Path) -> str:
    frontmatter = _frontmatter({
        "threadvault_session_id": summary.session_id,
        "threadvault_target_profile": "obsidian",
        "project": session["cwd"] or "",
        "updated_at": session["updated_at"] or "",
    })
    lines = [
        frontmatter,
        f"# {summary.topic}",
        "",
        "- Session: " + f"`{summary.session_id}`",
        f"- Project: `{session['cwd'] or ''}`",
        f"- Updated: `{session['updated_at'] or ''}`",
        f"- Vault index: {_wiki_link(root / 'index.md', 'Vault Index', root)}",
        f"- Evidence: {_wiki_link(evidence_path, 'Evidence', root)}",
    ]
    if summary.user_goal:
        lines.extend(["", "## User Goal", "", summary.user_goal])
    lines.extend(["", "## Key Steps", ""])
    lines.extend(_summary_items(summary.key_steps, "text"))
    lines.extend(["", "## Key Commands", ""])
    lines.extend(_summary_items(summary.key_commands, "command"))
    lines.extend(["", "## Files", ""])
    lines.extend(_summary_items(summary.files, "path"))
    lines.extend(["", "## Problems", ""])
    lines.extend(_summary_items(summary.problems, "text"))
    lines.extend(["", "## Next Steps", ""])
    lines.extend([f"- {item}" for item in summary.next_steps] or ["- Review the exported evidence before sharing."])
    lines.extend(["", "## Evidence Event IDs", ""])
    lines.append(", ".join(str(event_id) for event_id in summary.evidence_event_ids) or "None")
    lines.extend(["", "## Evidence Coverage", ""])
    lines.append(json.dumps(summary.evidence_coverage, ensure_ascii=False))
    if summary.missing_evidence_warnings:
        lines.extend(["", "## Missing Evidence Warnings", ""])
        lines.extend([f"- {item}" for item in summary.missing_evidence_warnings])
    return "\n".join(lines) + "\n"


def _session_evidence_page(session: sqlite3.Row, summary_path: Path, events: list[sqlite3.Row], root: Path) -> str:
    frontmatter = _frontmatter({
        "threadvault_session_id": session["session_id"],
        "threadvault_target_profile": "obsidian",
        "kind": "evidence",
    })
    lines = [
        frontmatter,
        f"# Evidence: {session['session_id']}",
        "",
        f"- Session summary: {_wiki_link(summary_path, 'Session Summary', root)}",
        "",
        "## Events",
        "",
    ]
    if not events:
        lines.append("- No evidence events were selected.")
    for event in events:
        lines.extend([
            f"### Event {event['event_id']}",
            "",
        ])
        if event["timestamp"]:
            lines.append(f"- Time: `{event['timestamp']}`")
        lines.append(f"- Type: `{event['top_type']}`" + (f" / `{event['sub_type']}`" if event["sub_type"] else ""))
        if event["role"]:
            lines.append(f"- Role: `{event['role']}`")
        if event["tool_name"]:
            lines.append(f"- Tool: `{event['tool_name']}`")
        if event["file_path"]:
            lines.append(f"- File: `{event['file_path']}`")
        if event["text_content"]:
            lines.extend(["", _code_block(_trim_text(event["text_content"], OBSIDIAN_TEXT_LIMIT)), ""])
    return "\n".join(lines) + "\n"


def _skill_markdown(skill_name: str, skill_description: str) -> str:
    return "\n".join([
        "---",
        f"name: {skill_name}",
        f"description: {json.dumps(skill_description, ensure_ascii=False)}",
        "---",
        "",
        f"# {skill_name.replace('-', ' ').title()}",
        "",
        "Use this Skill as a lightweight local ThreadVault memory packet. It contains summaries and evidence indexes, "
        "not full raw transcripts.",
        "",
        "## Workflow",
        "",
        "1. Read `references/index.md` first to understand the packet scope.",
        "2. Read `references/sessions.md` to choose the relevant session summary.",
        "3. Read only the matching `references/session-*.md` file when more detail is needed.",
        "4. Use `references/evidence.md` as an evidence index; preserve ThreadVault event IDs in derived claims.",
        "5. Ask before exposing private paths, secrets, or local context outside the local workspace.",
        "",
        "## References",
        "",
        "- `references/index.md`: packet map and reading order.",
        "- `references/sessions.md`: compact summary table.",
        "- `references/session-*.md`: per-session detail, loaded only when relevant.",
        "- `references/evidence.md`: selected evidence event index with short snippets.",
        "",
    ])


def _skill_index_reference(request: ExportTargetRequest, bundles: list[dict[str, Any]], skipped: list[dict[str, Any]]) -> str:
    lines = [
        "# ThreadVault Skill Packet Index",
        "",
        f"- Generated: `{_utc_now()}`",
        "- Target profile: `skill`",
        "- Packet shape: lightweight Skill candidate, not a raw transcript export.",
    ]
    if request.project:
        lines.append(f"- Project: `{request.project}`")
    lines.extend([
        f"- Exported sessions: {len(bundles)}",
        f"- Skipped items: {len(skipped)}",
        "",
        "## Reading Order",
        "",
        "1. Start with `references/sessions.md`.",
        "2. Open a listed `references/session-*.md` only when its topic is relevant.",
        "3. Use `references/evidence.md` to map claims back to ThreadVault event IDs.",
        "",
        "## Sessions",
        "",
    ])
    if not bundles:
        lines.append("- None exported.")
    for bundle in bundles:
        session = bundle["session"]
        summary = bundle["summary"]
        relpath = _skill_session_reference_relpath(session["session_id"])
        lines.append(f"- `{summary.session_id}`: `{relpath}` - {summary.topic}")
    if skipped:
        lines.extend(["", "## Skipped", ""])
        for item in skipped:
            reason = item.get("reason", "unknown")
            label = item.get("session_id") or item.get("project") or item.get("kind")
            lines.append(f"- `{label}`: {reason}")
    return "\n".join(lines) + "\n"


def _skill_sessions_reference(request: ExportTargetRequest, bundles: list[dict[str, Any]], skipped: list[dict[str, Any]]) -> str:
    lines = [
        "# ThreadVault Session Summaries",
        "",
        f"- Generated: `{_utc_now()}`",
    ]
    if request.project:
        lines.append(f"- Project: `{request.project}`")
    lines.extend([
        f"- Exported sessions: {len(bundles)}",
        f"- Skipped items: {len(skipped)}",
        "",
    ])
    if not bundles:
        lines.extend(["## Sessions", "", "- None exported."])
    for bundle in bundles:
        session = bundle["session"]
        summary = bundle["summary"]
        lines.extend([
            f"## {summary.topic}",
            "",
            f"- Session: `{summary.session_id}`",
            f"- Project: `{session['cwd'] or ''}`",
            f"- Updated: `{session['updated_at'] or ''}`",
            f"- Detail: `{_skill_session_reference_relpath(session['session_id'])}`",
        ])
        if summary.user_goal:
            lines.extend(["", "### User Goal", "", _trim_text(summary.user_goal, SKILL_EVIDENCE_SNIPPET_LIMIT)])
        lines.extend(["", "### Key Steps", ""])
        lines.extend(_summary_items(summary.key_steps, "text"))
        lines.extend(["", "### Key Commands", ""])
        lines.extend(_summary_items(summary.key_commands, "command"))
        lines.extend(["", "### Files", ""])
        lines.extend(_summary_items(summary.files, "path"))
        lines.extend(["", "### Problems", ""])
        lines.extend(_summary_items(summary.problems, "text"))
        lines.extend(["", "### Next Steps", ""])
        lines.extend([f"- {item}" for item in summary.next_steps] or ["- Review the exported evidence before sharing."])
        lines.extend(["", "### Evidence Event IDs", ""])
        lines.append(", ".join(str(event_id) for event_id in summary.evidence_event_ids) or "None")
        lines.append("")
    if skipped:
        lines.extend(["## Skipped", ""])
        for item in skipped:
            reason = item.get("reason", "unknown")
            label = item.get("session_id") or item.get("project") or item.get("kind")
            lines.append(f"- `{label}`: {reason}")
    return "\n".join(lines) + "\n"


def _skill_evidence_reference(bundles: list[dict[str, Any]]) -> str:
    lines = [
        "# ThreadVault Evidence Index",
        "",
        f"- Generated: `{_utc_now()}`",
        "- This index uses short snippets only. Use ThreadVault itself when full raw event text is required.",
        "",
    ]
    if not bundles:
        lines.append("- No evidence events were exported.")
    for bundle in bundles:
        session = bundle["session"]
        events = bundle["evidence_events"]
        lines.extend([
            f"## Session {session['session_id']}",
            "",
        ])
        if not events:
            lines.append("- No evidence events were selected.")
        for event in events:
            lines.extend([
                f"### Event {event['event_id']}",
                "",
            ])
            if event["timestamp"]:
                lines.append(f"- Time: `{event['timestamp']}`")
            lines.append(f"- Type: `{event['top_type']}`" + (f" / `{event['sub_type']}`" if event["sub_type"] else ""))
            if event["role"]:
                lines.append(f"- Role: `{event['role']}`")
            if event["tool_name"]:
                lines.append(f"- Tool: `{event['tool_name']}`")
            if event["file_path"]:
                lines.append(f"- File: `{event['file_path']}`")
            if event["text_content"]:
                lines.append(f"- Snippet: {_inline_text(_trim_text(event['text_content'], SKILL_EVIDENCE_SNIPPET_LIMIT))}")
    return "\n".join(lines) + "\n"


def _skill_session_reference(bundle: dict[str, Any]) -> str:
    session = bundle["session"]
    summary = bundle["summary"]
    evidence_events = bundle["evidence_events"]
    lines = [
        f"# {summary.topic}",
        "",
        f"- Session: `{summary.session_id}`",
        f"- Project: `{session['cwd'] or ''}`",
        f"- Updated: `{session['updated_at'] or ''}`",
        f"- Evidence events: {', '.join(str(event_id) for event_id in summary.evidence_event_ids) or 'None'}",
    ]
    if summary.user_goal:
        lines.extend(["", "## User Goal", "", _trim_text(summary.user_goal, SKILL_EVIDENCE_SNIPPET_LIMIT)])
    lines.extend(["", "## Key Steps", ""])
    lines.extend(_summary_items(summary.key_steps, "text"))
    lines.extend(["", "## Key Commands", ""])
    lines.extend(_summary_items(summary.key_commands, "command"))
    lines.extend(["", "## Files", ""])
    lines.extend(_summary_items(summary.files, "path"))
    lines.extend(["", "## Problems", ""])
    lines.extend(_summary_items(summary.problems, "text"))
    lines.extend(["", "## Next Steps", ""])
    lines.extend([f"- {item}" for item in summary.next_steps] or ["- Review the exported evidence before sharing."])
    lines.extend(["", "## Evidence Snippets", ""])
    if not evidence_events:
        lines.append("- No evidence events were selected.")
    for event in evidence_events:
        label = f"Event {event['event_id']}"
        event_type = f"{event['top_type']}" + (f"/{event['sub_type']}" if event["sub_type"] else "")
        lines.append(f"- `{label}` `{event_type}`: {_inline_text(_trim_text(event['text_content'] or '', SKILL_EVIDENCE_SNIPPET_LIMIT))}")
    return "\n".join(lines) + "\n"


def _skill_session_section(session: sqlite3.Row, summary) -> str:
    return "\n".join([
        f"Session: {summary.session_id}",
        f"Project: {session['cwd'] or ''}",
        f"Topic: {summary.topic}",
        f"User goal: {summary.user_goal or ''}",
        "Evidence: " + ", ".join(str(event_id) for event_id in summary.evidence_event_ids),
    ])


def _skill_evidence_section(session: sqlite3.Row, events: list[sqlite3.Row]) -> str:
    lines = [f"Session evidence: {session['session_id']}"]
    for event in events:
        lines.append(f"Event {event['event_id']}: {event['text_content'] or ''}")
    return "\n".join(lines)


def _skill_session_reference_relpath(session_id: str) -> str:
    return f"references/session-{_reference_stem(session_id)}.md"


def _reference_stem(value: str) -> str:
    chars = []
    last_dash = False
    for char in value.lower():
        if char.isalnum() or char in {"_", "-"}:
            chars.append(char)
            last_dash = False
        elif not last_dash:
            chars.append("-")
            last_dash = True
    normalized = "".join(chars).strip("-")[:96].strip("-")
    return normalized or "session"


def _default_skill_name(project: str | None, bundles: list[dict[str, Any]]) -> str:
    if project:
        return Path(project).name or "threadvault-skill"
    if len(bundles) == 1:
        return f"threadvault-{bundles[0]['summary'].session_id}"
    return "threadvault-skill"


def _default_skill_description(skill_name: str, project: str | None) -> str:
    if project:
        return f"Use when working with ThreadVault summaries and evidence exported for {project}."
    return f"Use when working with local ThreadVault summaries and evidence from {skill_name}."


def _normalize_skill_name(value: str) -> str:
    chars = []
    last_dash = False
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
            last_dash = False
        elif not last_dash:
            chars.append("-")
            last_dash = True
    normalized = "".join(chars).strip("-")[:63].strip("-")
    return normalized or "threadvault-skill"


def _summary_items(items: list[dict[str, Any]], key: str) -> list[str]:
    if not items:
        return ["- None found."]
    lines = []
    for item in items:
        evidence = item.get("evidence_event_id")
        suffix = f" (evidence: {evidence})" if evidence is not None else ""
        lines.append(f"- {item.get(key)}{suffix}")
    return lines


def _events_by_id(events: list[sqlite3.Row], event_ids: list[int]) -> list[sqlite3.Row]:
    by_id = {event["event_id"]: event for event in events}
    return [by_id[event_id] for event_id in event_ids if event_id in by_id]


def _frontmatter(values: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in values.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def _wiki_link(path: Path, alias: str, root: Path) -> str:
    target_path = Path(_relative_path(path, root)).with_suffix("")
    target = target_path.as_posix()
    return f"[[{target}|{alias}]]"


def _code_block(text: str) -> str:
    return "```text\n" + text.replace("```", "`\u200b``") + "\n```"


def _inline_text(text: str) -> str:
    compact = " ".join(text.split())
    if not compact:
        return "No text snippet."
    return compact.replace("|", "\\|")


def _trim_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _dedupe_session_rows(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    seen = set()
    deduped = []
    for row in rows:
        session_id = row["session_id"]
        if session_id in seen:
            continue
        seen.add(session_id)
        deduped.append(row)
    return deduped


def _summary_evidence_ids(summaries) -> list[int]:
    evidence_ids: list[int] = []
    for summary in summaries:
        evidence_ids.extend(summary.evidence_event_ids)
    return sorted(set(evidence_ids))


def _privacy_summary(mode: str, findings: list[PrivacyFinding]) -> dict[str, Any]:
    effective = effective_findings(findings)
    by_severity: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for finding in effective:
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        by_kind[finding.kind] = by_kind.get(finding.kind, 0) + 1
    return {
        "mode": mode,
        "findings_count": len(findings),
        "effective_findings_count": len(effective),
        "by_severity": by_severity,
        "by_kind": by_kind,
    }


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)

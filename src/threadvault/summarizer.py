from __future__ import annotations

import json
import re
from sqlite3 import Row
from typing import Any

from .models import Summary

FILE_PATTERN = re.compile(r"(?:(?:[A-Za-z]:\\|/)?[\w.\- ]+[\\/])?[\w.\-]+\.(?:py|ts|tsx|js|jsx|md|json|toml|yaml|yml|sql|txt)")


def build_summary(session: Row, events: list[Row]) -> Summary:
    user_events = [event for event in events if event["sub_type"] == "user_message" or event["role"] == "user"]
    assistant_events = [event for event in events if event["role"] == "assistant" or event["sub_type"] in {"message", "reasoning"}]
    command_events = [event for event in events if event["sub_type"] == "function_call"]
    problem_events = [
        event for event in events
        if _contains_problem(event["text_content"])
    ]

    first_user = _first_text(user_events)
    topic = _shorten(first_user or session["cwd"] or session["session_id"], 80)
    evidence_ids = [event["event_id"] for event in events if event["text_content"]][:20]

    key_steps = _key_steps(user_events, assistant_events)
    commands = _commands(command_events)
    files = _files(events)
    problems = [
        {"text": _shorten(event["text_content"] or "", 180), "evidence_event_id": event["event_id"]}
        for event in problem_events[:8]
    ]
    coverage, missing = _coverage({
        "key_steps": key_steps,
        "key_commands": commands,
        "files": files,
        "problems": problems,
    })

    return Summary(
        session_id=session["session_id"],
        topic=topic,
        user_goal=first_user,
        key_steps=key_steps,
        key_commands=commands,
        files=files,
        problems=problems,
        next_steps=_next_steps(events),
        evidence_event_ids=evidence_ids,
        evidence_coverage=coverage,
        missing_evidence_warnings=missing,
    )


def summary_to_markdown(summary: Summary) -> str:
    lines = [
        f"# Summary: {summary.topic}",
        "",
        f"- Session: `{summary.session_id}`",
    ]
    if summary.user_goal:
        lines.append(f"- User goal: {summary.user_goal}")
    lines.extend(["", "## Key Steps", ""])
    lines.extend(_items(summary.key_steps, "text"))
    lines.extend(["", "## Key Commands", ""])
    lines.extend(_items(summary.key_commands, "command"))
    lines.extend(["", "## Files", ""])
    lines.extend(_items(summary.files, "path"))
    lines.extend(["", "## Problems", ""])
    lines.extend(_items(summary.problems, "text"))
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


def _key_steps(user_events: list[Row], assistant_events: list[Row]) -> list[dict[str, Any]]:
    selected = (user_events[:3] + assistant_events[:5])[:8]
    return [
        {"text": _shorten(event["text_content"] or "", 180), "evidence_event_id": event["event_id"]}
        for event in selected if event["text_content"]
    ]


def _commands(events: list[Row]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for event in events[:12]:
        payload = json.loads(event["payload_json"])
        command = payload.get("arguments") or event["text_content"] or payload.get("name")
        commands.append({
            "command": _shorten(str(command), 220),
            "tool": payload.get("name") or event["tool_name"],
            "evidence_event_id": event["event_id"],
        })
    return commands


def _files(events: list[Row]) -> list[dict[str, Any]]:
    found: dict[str, int] = {}
    for event in events:
        if event["file_path"]:
            found.setdefault(event["file_path"], event["event_id"])
        text = event["text_content"] or ""
        for match in FILE_PATTERN.finditer(text):
            found.setdefault(match.group(0), event["event_id"])
    return [{"path": path, "evidence_event_id": event_id} for path, event_id in list(found.items())[:20]]


def _next_steps(events: list[Row]) -> list[str]:
    if any(event["sub_type"] == "function_call_output" for event in events):
        return ["Review command outputs and preserve useful fixes in project documentation."]
    return ["Add more sessions, then re-run search and export to build the archive."]


def _contains_problem(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(token in lowered for token in ["error", "failed", "failure", "exception", "traceback", "失败", "错误"])


def _first_text(events: list[Row]) -> str | None:
    for event in events:
        if event["text_content"]:
            return event["text_content"]
    return None


def _items(items: list[dict[str, Any]], key: str) -> list[str]:
    if not items:
        return ["- None found."]
    lines = []
    for item in items:
        evidence = item.get("evidence_event_id")
        suffix = f" (evidence: {evidence})" if evidence is not None else ""
        lines.append(f"- {item.get(key)}{suffix}")
    return lines


def _shorten(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _coverage(groups: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, Any], list[str]]:
    total = 0
    with_evidence = 0
    missing: list[str] = []
    by_group: dict[str, dict[str, int]] = {}
    for name, items in groups.items():
        group_total = len(items)
        group_with = sum(1 for item in items if item.get("evidence_event_id") is not None)
        total += group_total
        with_evidence += group_with
        by_group[name] = {"total": group_total, "with_evidence": group_with}
        if group_total != group_with:
            missing.append(f"{name} has {group_total - group_with} item(s) without evidence.")
    ratio = (with_evidence / total) if total else 1.0
    return {"total": total, "with_evidence": with_evidence, "ratio": ratio, "by_group": by_group}, missing

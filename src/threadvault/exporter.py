from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from sqlite3 import Row

from jinja2 import Template

from .app_config import PrivacyConfig, load_app_config
from .privacy import PrivacyFinding, has_high_risk, redact_sensitive_text, scan_sensitive_text
from .summarizer import build_summary, summary_to_markdown

SESSION_TEMPLATE = Template(
    """# ThreadVault Session {{ session["session_id"] }}

{% if session["cwd"] %}- Project: `{{ session["cwd"] }}`
{% endif -%}
{% if session["first_seen_at"] %}- First seen: `{{ session["first_seen_at"] }}`
{% endif -%}
{% if session["updated_at"] %}- Updated: `{{ session["updated_at"] }}`
{% endif -%}
- Source: `{{ session["source_kind"] }}`
- Raw path: `{{ session["raw_path"] }}`

## Timeline

{% for event in events -%}
### Event {{ event["event_id"] }}: {{ event["top_type"] }}{% if event["sub_type"] %} / {{ event["sub_type"] }}{% endif %}

{% if event["timestamp"] %}- Time: `{{ event["timestamp"] }}`
{% endif -%}
{% if event["role"] %}- Role: `{{ event["role"] }}`
{% endif -%}
{% if event["tool_name"] %}- Tool: `{{ event["tool_name"] }}`
{% endif -%}
{% if event["file_path"] %}- File: `{{ event["file_path"] }}`
{% endif -%}
{% if event["text_content"] %}
```text
{{ event["text_content"] }}
```
{% endif %}
{% endfor -%}
"""
)

PROJECT_TEMPLATE = Template(
    """# ThreadVault Project Archive

- Project: `{{ cwd }}`
- Sessions: {{ sessions|length }}

## Sessions

{% for session in sessions -%}
- `{{ session["session_id"] }}`{% if session["updated_at"] %} updated `{{ session["updated_at"] }}`{% endif %}
{% endfor %}

{% if summaries %}
## Session Summaries

{% for summary in summaries -%}
### {{ summary.topic }}

- Session: `{{ summary.session_id }}`
- Evidence: {{ summary.evidence_event_ids|join(", ") }}
{% if summary.user_goal %}- User goal: {{ summary.user_goal }}
{% endif %}
{% endfor %}
{% endif %}
"""
)


def export_session(
    session: Row,
    events: list[Row],
    out_dir: Path,
    fmt: str = "md",
    brief: bool = False,
    max_chars: int | None = None,
    max_tool_chars: int | None = None,
    privacy_mode: str = "warn",
    privacy_config: PrivacyConfig | None = None,
) -> tuple[Path, list[PrivacyFinding]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    events = [_trim_event(event, max_chars=max_chars, max_tool_chars=max_tool_chars) for event in events]
    if fmt == "md" and brief:
        summary = build_summary(session, events)
        text = summary_to_markdown(summary)
        path = out_dir / f"{session['session_id']}.brief.md"
    elif fmt == "md":
        text = SESSION_TEMPLATE.render(session=session, events=events)
        path = out_dir / f"{session['session_id']}.md"
    elif fmt == "json":
        text = json.dumps({"session": dict(session), "events": events}, ensure_ascii=False, indent=2, default=str)
        path = out_dir / f"{session['session_id']}.json"
    elif fmt == "jsonl":
        rows = [
            json.dumps({"session_id": session["session_id"], **event}, ensure_ascii=False, default=str)
            for event in events
        ]
        text = "\n".join(rows) + "\n"
        path = out_dir / f"{session['session_id']}.jsonl"
    elif fmt == "csv":
        path = out_dir / f"{session['session_id']}.csv"
        text = _csv_text(events)
    else:
        raise ValueError(f"Unsupported export format: {fmt}")
    config = privacy_config or load_app_config()
    findings = scan_sensitive_text(text, allowlist=config.allowlist)
    if privacy_mode == "fail" and has_high_risk(findings):
        return path, findings
    if privacy_mode == "redact":
        text, findings = redact_sensitive_text(text, allowlist=config.allowlist)
    path.write_text(text, encoding="utf-8")
    return path, findings


def export_session_markdown(
    session: Row,
    events: list[Row],
    out_dir: Path,
    brief: bool = False,
    max_chars: int | None = None,
    max_tool_chars: int | None = None,
    privacy_mode: str = "warn",
    privacy_config: PrivacyConfig | None = None,
) -> tuple[Path, list[PrivacyFinding]]:
    return export_session(
        session,
        events,
        out_dir,
        fmt="md",
        brief=brief,
        max_chars=max_chars,
        max_tool_chars=max_tool_chars,
        privacy_mode=privacy_mode,
        privacy_config=privacy_config,
    )


def export_project_markdown(cwd: str, sessions: list[Row], out_dir: Path, summaries=None) -> tuple[Path, list[PrivacyFinding]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    text = PROJECT_TEMPLATE.render(cwd=cwd, sessions=sessions, summaries=summaries or [])
    findings = scan_sensitive_text(text)
    path = out_dir / "project-index.md"
    path.write_text(text, encoding="utf-8")
    return path, findings


def _trim_event(event: Row, max_chars: int | None, max_tool_chars: int | None) -> dict:
    value = dict(event)
    text = value.get("text_content")
    limit = max_tool_chars if value.get("sub_type") == "function_call_output" and max_tool_chars is not None else max_chars
    if text and limit is not None and len(text) > limit:
        value["text_content"] = text[:limit] + "\n...[truncated]"
    return value


def _write_csv(path: Path, events: list[dict]) -> None:
    path.write_text(_csv_text(events), encoding="utf-8")


def _csv_text(events: list[dict]) -> str:
    columns = [
        "event_id",
        "session_id",
        "turn_id",
        "timestamp",
        "top_type",
        "sub_type",
        "role",
        "tool_name",
        "file_path",
        "text_content",
    ]
    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=columns)
    writer.writeheader()
    for event in events:
        writer.writerow({column: event.get(column) for column in columns})
    return handle.getvalue()

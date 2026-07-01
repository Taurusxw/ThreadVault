from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from .app_config import AllowlistRule


@dataclass(frozen=True)
class PrivacyFinding:
    kind: str
    excerpt: str
    start: int
    end: int
    severity: str
    allowlisted: bool = False


PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("private_key", "critical", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("api_key", "critical", re.compile(r"\b(?:sk|pk|rk|tvly|ghp|github_pat)_[A-Za-z0-9_\-]{16,}\b")),
    ("token_assignment", "high", re.compile(r"(?i)\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s]{8,}")),
    ("email", "medium", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("windows_abs_path", "low", re.compile(r"\b[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\?)+")),
    ("posix_abs_path", "low", re.compile(r"(?<![\w.-])/(?:Users|home|var|etc|tmp|opt|workspace|repo)/[^\s`'\"]+")),
]

RULES_VERSION = "2026-06-30.v1"


def scan_sensitive_text(text: str, allowlist: Iterable[AllowlistRule] | None = None) -> list[PrivacyFinding]:
    findings: list[PrivacyFinding] = []
    rules = list(allowlist or [])
    for kind, severity, pattern in PATTERNS:
        for match in pattern.finditer(text):
            excerpt = match.group(0)
            if len(excerpt) > 120:
                excerpt = excerpt[:117] + "..."
            findings.append(
                PrivacyFinding(
                    kind=kind,
                    excerpt=excerpt,
                    start=match.start(),
                    end=match.end(),
                    severity=severity,
                    allowlisted=_is_allowlisted(kind, match.group(0), rules),
                )
            )
    return findings


def redact_sensitive_text(text: str, allowlist: Iterable[AllowlistRule] | None = None) -> tuple[str, list[PrivacyFinding]]:
    findings = scan_sensitive_text(text, allowlist=allowlist)
    redacted = text
    for finding in sorted(findings, key=lambda item: item.start, reverse=True):
        if finding.allowlisted:
            continue
        replacement = f"[REDACTED:{finding.kind}]"
        redacted = redacted[:finding.start] + replacement + redacted[finding.end:]
    return redacted, findings


def has_high_risk(findings: list[PrivacyFinding]) -> bool:
    return any(finding.severity in {"high", "critical"} and not finding.allowlisted for finding in findings)


def effective_findings(findings: list[PrivacyFinding]) -> list[PrivacyFinding]:
    return [finding for finding in findings if not finding.allowlisted]


def _is_allowlisted(kind: str, text: str, rules: list[AllowlistRule]) -> bool:
    for rule in rules:
        if rule.kind and rule.kind != kind:
            continue
        if rule.text is not None and rule.text == text:
            return True
        if rule.pattern is not None and rule.pattern.search(text):
            return True
    return False

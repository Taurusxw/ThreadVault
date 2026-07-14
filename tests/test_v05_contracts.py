from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import SCHEMA_VERSION
from threadvault.parser import parse_session_file

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def assert_json_only(output: str):
    assert output.lstrip().startswith(("{", "["))
    return json.loads(output)


def test_pairing_warnings_are_not_duplicated() -> None:
    parsed = parse_session_file(FIXTURES / "sessions" / "privacy_pairing.jsonl")
    counts = Counter(warning.code for warning in parsed.warnings)
    assert counts["missing_function_call_output"] == 1
    assert counts["orphan_function_call_output"] == 1
    assert counts["duplicate_function_call_output"] == 1


def test_parser_warning_snapshot_for_fixture_shapes() -> None:
    current = parse_session_file(FIXTURES / "sessions" / "current.jsonl")
    fork = parse_session_file(FIXTURES / "sessions" / "fork.jsonl")
    legacy = parse_session_file(FIXTURES / "archived_sessions" / "legacy.jsonl", archived=True)
    assert Counter(warning.code for warning in current.warnings) == Counter({"unknown_current_type": 1, "invalid_json": 1})
    assert Counter(warning.code for warning in fork.warnings) == Counter()
    assert Counter(warning.code for warning in legacy.warnings) == Counter({"missing_function_call_output": 1})
    assert fork.session_id == "sess-fork"
    assert legacy.session_id == "sess-legacy"


def test_json_commands_emit_parseable_stdout(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    commands = [
        ["capabilities", "--json"],
        ["robot-docs", "guide", "--json"],
        ["robot-docs", "schemas", "--json"],
        ["list", "--db", str(db), "--json"],
        ["stats", "--db", str(db), "--json"],
        ["doctor", "--db", str(db), "--codex-home", str(FIXTURES), "--json"],
        ["warnings", "--db", str(db), "--summary", "--json"],
        ["privacy-scan", "--session", "sess-privacy", "--db", str(db), "--json"],
        ["summarize", "--session", "sess-current", "--db", str(db), "--json"],
        ["reindex", "--db", str(db), "--fts-only", "--json"],
        ["self-test", "--db", str(db), "--json"],
    ]
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, (command, result.output)
        assert_json_only(result.output)


def test_capabilities_and_robot_schemas_v05_contract() -> None:
    runner = CliRunner()
    caps = assert_json_only(runner.invoke(app, ["capabilities", "--json"]).output)
    assert caps["contract_version"] >= "0.5"
    assert "json_outputs" in caps
    assert caps["feature_flags"]["privacy_allowlist"] is True

    schemas = assert_json_only(runner.invoke(app, ["robot-docs", "schemas", "--json"]).output)
    assert schemas["contract_version"] >= "0.5"
    assert "schemas" in schemas
    assert "privacy_scan" in schemas["schemas"]
    assert "search_minimal" in schemas


def test_privacy_allowlist_affects_effective_findings_and_fail_mode(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    config = tmp_path / "threadvault.toml"
    config.write_text(
        """
[privacy]
allowlist = [
  { kind = "token_assignment", text = "api_key=supersecrettoken123" },
]
""".strip(),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["privacy-scan", "--session", "sess-privacy", "--db", str(db), "--privacy-config", str(config), "--json"],
    )
    assert result.exit_code == 0, result.output
    scan = assert_json_only(result.output)
    assert scan["rules_version"]
    assert scan["summary"]["allowlisted_count"] == 1
    assert scan["summary"]["effective_findings_count"] == scan["summary"]["total"] - 1

    out = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "export",
            "--session",
            "sess-privacy",
            "--db",
            str(db),
            "--out",
            str(out),
            "--privacy-mode",
            "fail",
            "--privacy-config",
            str(config),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert Path(assert_json_only(result.output)["path"]).exists()


def test_doctor_schema_objects_and_maintenance_fields(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    result = runner.invoke(app, ["doctor", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    payload = assert_json_only(result.output)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert "sessions" in payload["schema_objects"]["table"]
    assert "events_ai" in payload["schema_objects"]["trigger"]
    assert isinstance(payload["maintenance_suggestions"], list)


def test_v05_docs_and_gitignore_policy() -> None:
    required = [
        Path("docs/progress/archive/legacy-v0/phases/phase-05-quality-contracts-maintenance/plan.md"),
        Path("docs/progress/archive/legacy-v0/phases/phase-05-quality-contracts-maintenance/external-review.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
    ]
    for path in required:
        assert path.exists(), f"missing {path}"
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    for pattern in ["__pycache__/", ".pytest_cache/", ".ruff_cache/", "*.db", "threadvault-export/"]:
        assert pattern in gitignore

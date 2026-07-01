from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import SCHEMA_VERSION
from threadvault.schemas import get_schema, validate_payload

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"

REQUIRED_DOCTOR_FIELDS = [
    "ok",
    "checks",
    "stats",
    "parse_health",
    "schema_version",
    "schema_objects",
    "maintenance_suggestions",
    "python",
    "platform",
    "db_path",
    "codex_home",
    "session_dirs",
    "missing_session_dirs",
    "jsonl_files",
    "codex_state",
]


def doctor_payload(tmp_path: Path) -> dict:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["init", "--db", str(db)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["doctor", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def test_doctor_schema_requires_runtime_diagnostic_fields() -> None:
    schema = get_schema("doctor")

    for field in REQUIRED_DOCTOR_FIELDS:
        assert field in schema["required"]
        assert field in schema["properties"]


def test_real_doctor_output_validates_against_schema(tmp_path: Path) -> None:
    payload = doctor_payload(tmp_path)

    validation = validate_payload("doctor", payload)

    assert validation["ok"] is True
    assert payload["schema_version"] == SCHEMA_VERSION
    assert "table" in payload["schema_objects"]
    assert isinstance(payload["maintenance_suggestions"], list)
    assert isinstance(payload["parse_health"]["warning_codes_top"], list)


def test_doctor_schema_rejects_missing_parse_health(tmp_path: Path) -> None:
    payload = doctor_payload(tmp_path)
    payload.pop("parse_health")

    validation = validate_payload("doctor", payload)

    assert validation["ok"] is False
    assert any("parse_health" in error["message"] for error in validation["errors"])


def test_v29_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-29-doctor-schema-contract/plan.md"),
        Path("docs/v0/phases/phase-29-doctor-schema-contract/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"

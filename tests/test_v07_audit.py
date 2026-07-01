from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def test_ingest_sample_defaults_to_anonymous_output() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["ingest-sample", "--codex-home", str(FIXTURES), "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    text = json.dumps(payload, ensure_ascii=False)
    assert payload["include_paths"] is False
    assert payload["privacy_note"]
    assert payload["samples"]
    assert "sample_id" in payload["samples"][0]
    assert "path" not in payload["samples"][0]
    assert "session_id" not in payload["samples"][0]
    assert str(FIXTURES) not in text
    assert "sess-current" not in text


def test_audit_corpus_include_paths_is_explicit_opt_in() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["audit-corpus", "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    anonymous = json.loads(result.output)
    anonymous_text = json.dumps(anonymous, ensure_ascii=False)
    assert str(FIXTURES) not in anonymous_text
    assert "sess-current" not in anonymous_text

    result = runner.invoke(app, ["audit-corpus", "--codex-home", str(FIXTURES), "--include-paths", "--json"])
    assert result.exit_code == 0, result.output
    disclosed = json.loads(result.output)
    assert disclosed["include_paths"] is True
    assert any(str(FIXTURES) in sample["path"] for sample in disclosed["samples"])
    assert any(sample["session_id"] == "sess-current" for sample in disclosed["samples"])


def test_corpus_audit_schema_and_validation(tmp_path: Path) -> None:
    runner = CliRunner()
    payload_path = tmp_path / "audit.json"
    result = runner.invoke(app, ["audit-corpus", "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")

    result = runner.invoke(app, ["schemas", "show", "corpus_audit", "--json"])
    assert result.exit_code == 0, result.output
    schema = json.loads(result.output)
    assert schema["type"] == "object"

    result = runner.invoke(app, ["validate-json", "--schema", "corpus_audit", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    validation = json.loads(result.output)
    assert validation["ok"] is True


def test_v07_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-07-real-corpus-anonymous-audit/plan.md"),
        Path("docs/v0/phases/phase-07-real-corpus-anonymous-audit/external-review.md"),
        Path("docs/schemas/corpus_audit.schema.json"),
    ]:
        assert path.exists(), f"missing {path}"

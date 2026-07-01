from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_schema_commands_list_show_and_write(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["schemas", "list", "--json"])
    assert result.exit_code == 0, result.output
    names = json.loads(result.output)["schemas"]
    assert "search_minimal" in names
    assert "privacy_scan" in names

    result = runner.invoke(app, ["schemas", "show", "search_minimal", "--json"])
    assert result.exit_code == 0, result.output
    schema = json.loads(result.output)
    assert schema["$schema"].endswith("/2020-12/schema")
    assert schema["type"] == "array"

    out = tmp_path / "schemas"
    result = runner.invoke(app, ["schemas", "write", "--out", str(out), "--json"])
    assert result.exit_code == 0, result.output
    files = [Path(path) for path in json.loads(result.output)["files"]]
    assert out / "search_minimal.schema.json" in files
    assert (out / "capabilities.schema.json").exists()


def test_validate_json_pass_and_fail(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    good = tmp_path / "search.json"
    bad = tmp_path / "bad.json"

    result = runner.invoke(app, ["search", "pytest", "--db", str(db), "--json", "--fields", "minimal"])
    assert result.exit_code == 0, result.output
    good.write_text(result.output, encoding="utf-8")

    result = runner.invoke(app, ["validate-json", "--schema", "search_minimal", "--input", str(good), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["errors"] == []

    bad.write_text(json.dumps([{"event_id": "not-an-int"}]), encoding="utf-8")
    result = runner.invoke(app, ["validate-json", "--schema", "search_minimal", "--input", str(bad), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["errors"]


def test_v06_packaged_schema_docs_exist() -> None:
    for name in [
        "search_minimal",
        "search_standard",
        "search_full",
        "capabilities",
        "stats",
        "doctor",
        "privacy_scan",
        "warnings_summary",
    ]:
        path = Path("docs/schemas") / f"{name}.schema.json"
        assert path.exists(), f"missing {path}"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["$schema"].endswith("/2020-12/schema")

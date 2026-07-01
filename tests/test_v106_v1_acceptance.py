from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import validate_payload

FIXTURES = Path("tests/fixtures/codex_home")
PROJECT = "E:\\Codex\\ThreadVault"


def hook_payload() -> dict:
    return {
        "session_id": "sess-current",
        "transcript_path": str(FIXTURES / "sessions" / "current.jsonl"),
        "cwd": PROJECT,
        "hook_event_name": "Stop",
        "model": "gpt-test",
    }


def test_v1_end_to_end_personal_knowledge_layer_smoke(tmp_path: Path) -> None:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"

    hook_result = runner.invoke(
        app,
        ["codex-hook", "ingest", "--db", str(db), "--diagnostic-json"],
        input=json.dumps(hook_payload()),
    )
    assert hook_result.exit_code == 0, hook_result.output
    hook = json.loads(hook_result.output)
    assert validate_payload("codex_hook_ingest", hook)["ok"] is True
    assert hook["enqueue"]["enqueued"] is True

    process_result = runner.invoke(app, ["ingest-queue", "process", "--db", str(db), "--apply", "--json"])
    assert process_result.exit_code == 0, process_result.output
    process = json.loads(process_result.output)
    assert validate_payload("ingestion_process", process)["ok"] is True
    assert process["processed"] == 1
    assert process["requests"][0]["import_stats"]["imported"] >= 1

    list_result = runner.invoke(app, ["list", "--db", str(db), "--json"])
    assert list_result.exit_code == 0, list_result.output
    sessions = json.loads(list_result.output)
    assert any(session["session_id"] == "sess-current" for session in sessions)

    search_result = runner.invoke(app, ["search", "pytest", "--db", str(db), "--json", "--fields", "minimal"])
    assert search_result.exit_code == 0, search_result.output
    assert json.loads(search_result.output)

    markdown = _export_target(runner, db, tmp_path / "markdown", "markdown", ["--session", "sess-current"])
    assert validate_payload("export_target_manifest", markdown)["ok"] is True
    assert (tmp_path / "markdown" / "sessions" / "sess-current.md").exists()

    obsidian = _export_target(runner, db, tmp_path / "obsidian", "obsidian", ["--project", PROJECT])
    assert validate_payload("export_target_manifest", obsidian)["ok"] is True
    assert (tmp_path / "obsidian" / "index.md").exists()
    assert any(item["kind"] == "session_evidence" for item in obsidian["files"])

    skill = _export_target(
        runner,
        db,
        tmp_path / "skill",
        "skill",
        ["--project", PROJECT, "--skill-name", "ThreadVault Acceptance"],
    )
    assert validate_payload("export_target_manifest", skill)["ok"] is True
    assert (tmp_path / "skill" / "SKILL.md").exists()
    assert (tmp_path / "skill" / "references" / "sessions.md").exists()
    assert (tmp_path / "skill" / "references" / "evidence.md").exists()


def test_v1_capabilities_and_schema_discovery() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["capabilities", "--json"])
    assert result.exit_code == 0, result.output
    capabilities = json.loads(result.output)
    for flag in [
        "ingestion_queue",
        "codex_hook_adapter",
        "export_target_manifest",
        "obsidian_vault_target",
        "codex_skill_target",
    ]:
        assert capabilities["feature_flags"][flag] is True
    for output in [
        "ingest-queue process",
        "codex-hook ingest",
        "export-target markdown",
        "export-target obsidian",
        "export-target skill",
    ]:
        assert output in capabilities["json_outputs"]

    result = runner.invoke(app, ["schemas", "list", "--json"])
    assert result.exit_code == 0, result.output
    schemas = set(json.loads(result.output)["schemas"])
    for schema in [
        "ingestion_enqueue",
        "ingestion_queue_list",
        "ingestion_process",
        "codex_hook_ingest",
        "codex_hook_config",
        "export_target_manifest",
    ]:
        assert schema in schemas


def test_v1_docs_and_retired_report_policy() -> None:
    phase_dirs = [
        "phase-01-ingestion-automation-queue",
        "phase-02-codex-hook-adapter",
        "phase-03-export-target-manifest",
        "phase-04-obsidian-markdown-vault",
        "phase-05-codex-skill-target",
        "phase-06-v1-acceptance-smoke",
    ]
    for dirname in phase_dirs:
        phase = Path("docs/v1/phases") / dirname
        assert (phase / "plan.md").exists(), f"missing {phase / 'plan.md'}"
        if dirname != "phase-06-v1-acceptance-smoke":
            assert (phase / "acceptance.md").exists(), f"missing {phase / 'acceptance.md'}"
    for path in [
        Path("docs/v1/README.md"),
        Path("docs/THREADVAULT_USAGE_MANUAL.md"),
        Path("docs/development-progress.md"),
        Path("docs/roadmap/v1-personal-knowledge-layer.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()


def _export_target(runner: CliRunner, db: Path, out: Path, profile: str, extra_args: list[str]) -> dict:
    result = runner.invoke(
        app,
        ["export-target", profile, "--db", str(db), "--out", str(out), *extra_args, "--json"],
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.output)

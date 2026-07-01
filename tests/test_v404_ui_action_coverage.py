from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.personal_ui import ACTION_REGISTRY, APP_JS, PersonalUIServerConfig, handle_api_action
from threadvault.schemas import validate_payload
from threadvault.store import ArchiveStore, capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")
PHASE_DIR = Path("docs/v4/phases/phase-04-ui-action-coverage")


def import_fixture(tmp_path: Path) -> tuple[ArchiveStore, PersonalUIServerConfig]:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return ArchiveStore(db), PersonalUIServerConfig(db_path=db)


def action(store: ArchiveStore, config: PersonalUIServerConfig, name: str, params: dict | None = None, confirm: bool = False):
    response = handle_api_action(store, {"action": name, "params": params or {}, "confirm": confirm}, config)
    assert response["schema"] == "personal_ui_action"
    assert validate_payload("personal_ui_action", response["payload"])["ok"] is True
    return response


def test_personal_ui_action_registry_covers_required_phase_04_families() -> None:
    required = [
        "init",
        "import",
        "ingest_queue_enqueue",
        "ingest_queue_list",
        "ingest_queue_process",
        "sessions_list",
        "search",
        "retrieval_query",
        "hybrid_retrieval",
        "agent_retrieve",
        "summary_chunks",
        "summarize",
        "vector_status",
        "vector_index",
        "vector_query",
        "privacy_scan",
        "warnings",
        "export_session",
        "export_target_markdown",
        "export_target_obsidian",
        "export_target_skill",
        "client_overview",
        "client_session",
        "client_export_preview",
        "client_warnings",
        "config_init",
        "config_show",
        "config_doctor",
        "stats",
        "doctor",
        "self_test",
        "reindex",
        "vacuum",
        "backup",
        "backup_verify",
        "backup_history",
        "restore_plan",
        "restore_apply",
        "restore_history",
        "audit_corpus",
        "audit_history",
        "audit_diff",
        "schemas_list",
        "schemas_show",
        "validate_json",
        "schema_write",
        "capabilities",
        "robot_docs_guide",
        "robot_docs_schemas",
        "governance_status",
        "governance_v3_gap_audit",
        "governance_v3_acceptance_smoke",
        "governance_preflight",
        "governance_instrumentation",
    ]

    for name in required:
        assert name in ACTION_REGISTRY, f"missing {name}"
        assert ACTION_REGISTRY[name].implemented is True


def test_personal_ui_action_registry_runs_representative_safe_actions(tmp_path: Path) -> None:
    store, config = import_fixture(tmp_path)

    stats = action(store, config, "stats")
    overview = action(store, config, "client_overview", {"query": "pytest", "limit": 5})
    retrieve = action(store, config, "agent_retrieve", {"query": "pytest", "limit": 5})
    privacy = action(store, config, "privacy_scan", {"session": "sess-privacy"})
    schema_list = action(store, config, "schemas_list")
    validate = action(store, config, "validate_json", {"schema": "personal_ui_action", "payload": stats["payload"]})
    governance = action(store, config, "governance_status")

    assert stats["status_code"] == 200
    assert stats["payload"]["result"]["sessions"] >= 1
    assert overview["payload"]["result"]["contract_version"] == "client_overview.v1"
    assert retrieve["payload"]["result"]["contract_version"] == "agent_retrieval.v1"
    assert privacy["payload"]["result"]["summary"]["effective_findings_count"] >= 1
    assert "personal_ui_action" in schema_list["payload"]["result"]["schemas"]
    assert validate["payload"]["result"]["ok"] is True
    assert governance["payload"]["result"]["contract_version"].startswith("governance_status")


def test_personal_ui_action_registry_enforces_safety_rules(tmp_path: Path) -> None:
    store, config = import_fixture(tmp_path)

    for name in ["restore_apply", "vacuum", "reindex", "schema_write"]:
        response = action(store, config, name)
        assert response["status_code"] == 403
        assert response["payload"]["status"] == "confirm_required"
        assert response["payload"]["safety"]["dangerous_action"] is True
        assert response["payload"]["safety"]["confirm_required"] is True

    export_blocked = action(store, config, "export_target_markdown", {"session": "sess-current", "out": str(tmp_path / "out")})
    assert export_blocked["status_code"] == 403
    assert export_blocked["payload"]["status"] == "preview_required"
    assert export_blocked["payload"]["safety"]["preview_required"] is True

    prune_blocked = action(store, config, "backup_history_prune", {"dir": str(tmp_path), "keep": 1, "apply": True})
    assert prune_blocked["status_code"] == 403
    assert prune_blocked["payload"]["status"] == "confirm_required"


def test_personal_ui_action_registry_allows_confirmed_dangerous_and_previewed_safe_writes(tmp_path: Path) -> None:
    store, config = import_fixture(tmp_path)

    reindex = action(store, config, "reindex", confirm=True)
    schema_write = action(store, config, "schema_write", {"out": str(tmp_path / "schemas")}, confirm=True)
    export_preview = action(
        store,
        config,
        "client_export_preview",
        {"session": "sess-current", "out": str(tmp_path / "preview"), "profile": "markdown"},
    )
    backup = action(store, config, "backup", {"out": str(tmp_path / "backups")})

    assert reindex["status_code"] == 200
    assert reindex["payload"]["result"]["events_fts"] >= 1
    assert schema_write["status_code"] == 200
    assert any(path.endswith("personal_ui_action.schema.json") for path in schema_write["payload"]["result"]["files"])
    assert export_preview["status_code"] == 200
    assert export_preview["payload"]["result"]["diagnostics"]["writes_files"] is False
    assert backup["status_code"] == 200
    assert backup["payload"]["result"]["target_path"]


def test_personal_ui_registry_discovery_docs_and_ui_controls() -> None:
    caps = capabilities()
    guide = robot_guide()
    schemas = robot_schemas()

    assert caps["feature_flags"]["personal_ui_action_registry"] is True
    assert guide["personal_ui"]["action_registry"] == "POST /api/action"
    assert guide["personal_ui"]["action_registry_status"] == "implemented"
    assert "restore_apply" in guide["personal_ui"]["dangerous_actions_require_confirm"]
    assert "export_target_markdown" in guide["personal_ui"]["export_actions_require_preview"]
    assert "personal_ui_action" in schemas
    assert "paramsForAction" in APP_JS
    assert "preview_accepted" in APP_JS
    assert "window.confirm" in APP_JS

    for path in [
        PHASE_DIR / "plan.md",
        PHASE_DIR / "design-notes.md",
        PHASE_DIR / "acceptance.md",
        Path("docs/v4/README.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

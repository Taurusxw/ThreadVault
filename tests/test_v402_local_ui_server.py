from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.personal_ui import PersonalUIServerConfig, build_health_payload, handle_api_action, handle_api_get
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import ArchiveStore, capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")
PHASE_DIR = Path("docs/progress/archive/legacy-v4/phases/phase-02-local-ui-server")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_personal_ui_health_preserves_local_first_defaults(tmp_path: Path) -> None:
    config = PersonalUIServerConfig(db_path=tmp_path / "threadvault.db")

    payload = build_health_payload(config)

    assert validate_payload("personal_ui_health", payload)["ok"] is True
    assert payload["contract_version"] == "personal_ui_health.v1"
    assert payload["ok"] is True
    assert payload["server"]["host"] == "127.0.0.1"
    assert payload["server"]["port"] == 8766
    assert payload["server"]["loopback_default"] is True
    assert payload["server"]["public_network_default"] is False
    assert payload["server"]["authentication_required"] is False
    assert payload["defaults"]["local_first"] is True
    assert payload["defaults"]["cloud_sync"] is False
    assert payload["defaults"]["external_model_calls"] is False
    assert payload["defaults"]["team_enforcement"] is False
    assert payload["paths"]["default_export_dir"].endswith("threadvault-ui-output")


def test_personal_ui_health_uses_configured_archive_db_path(tmp_path: Path, monkeypatch) -> None:
    custom_db = tmp_path / "custom" / "threadvault.db"
    config_file = tmp_path / "threadvault.toml"
    config_file.write_text(f'[storage]\narchive_db = "{custom_db.as_posix()}"\n', encoding="utf-8")
    monkeypatch.delenv("THREADVAULT_DB", raising=False)

    payload = build_health_payload(PersonalUIServerConfig(config_path=config_file))

    assert payload["paths"]["db_path"] == str(custom_db)
    assert payload["paths"]["config_path"] == str(config_file)


def test_personal_ui_routes_reuse_existing_archive_interfaces(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    store = ArchiveStore(db)
    config = PersonalUIServerConfig(db_path=db)

    health = handle_api_get(store, "/api/health", config)
    caps = handle_api_get(store, "/api/capabilities", config)
    overview = handle_api_get(store, "/api/client/overview?query=pytest&limit=5", config)
    retrieve = handle_api_get(store, "/api/retrieve?q=pytest&limit=5", config)
    session = handle_api_get(store, "/api/client/session?session=sess-current&event_limit=2", config)
    warnings = handle_api_get(store, "/api/client/warnings?session=sess-current", config)

    assert health["ok"] is True
    assert health["schema"] == "personal_ui_health"
    assert caps["ok"] is True
    assert caps["payload"]["feature_flags"]["personal_web_ui"] is True
    assert overview["schema"] == "client_overview"
    assert validate_payload("client_overview", overview["payload"])["ok"] is True
    assert overview["payload"]["privacy"]["raw_paths_included"] is False
    assert retrieve["schema"] == "agent_retrieval"
    assert validate_payload("agent_retrieval", retrieve["payload"])["ok"] is True
    assert retrieve["payload"]["privacy"]["raw_paths_included"] is False
    assert session["schema"] == "client_session"
    assert validate_payload("client_session", session["payload"])["ok"] is True
    assert len(session["payload"]["events"]) <= 2
    assert warnings["schema"] == "client_warnings"
    assert validate_payload("client_warnings", warnings["payload"])["ok"] is True


def test_personal_ui_action_entrypoint_blocks_unconfirmed_dangerous_actions(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    response = handle_api_action(
        ArchiveStore(db),
        {"action": "restore_apply", "params": {}, "confirm": False},
        PersonalUIServerConfig(db_path=db),
    )

    assert response["status_code"] == 403
    assert response["schema"] == "personal_ui_action"
    assert validate_payload("personal_ui_action", response["payload"])["ok"] is True
    assert response["payload"]["ok"] is False
    assert response["payload"]["action"] == "restore_apply"
    assert response["payload"]["status"] == "confirm_required"
    assert response["payload"]["confirm"] is False
    assert response["payload"]["safety"]["dangerous_action"] is True
    assert response["payload"]["safety"]["confirm_required"] is True
    assert response["payload"]["safety"]["dry_run_default"] is False


def test_personal_ui_cli_discovery_schema_and_docs() -> None:
    runner = CliRunner()

    help_result = runner.invoke(app, ["ui", "serve", "--help"])

    assert help_result.exit_code == 0, help_result.output
    assert "--host" in help_result.output
    assert "127.0.0.1" in help_result.output
    assert "--port" in help_result.output
    assert "--open" in help_result.output

    caps = capabilities()
    assert "ui" in caps["commands"]
    assert "ui serve" not in caps["json_outputs"]
    assert caps["feature_flags"]["personal_web_ui"] is True
    assert caps["feature_flags"]["personal_ui_server"] is True
    assert caps["feature_flags"]["personal_ui_desktop_wrapper"] is False
    assert caps["feature_flags"]["personal_ui_team_mode"] is False
    assert caps["feature_flags"]["personal_ui_cloud_sync"] is False

    guide = robot_guide()
    assert "threadvault ui serve --host 127.0.0.1 --port 8766 --open" in guide["recommended_commands"]
    assert guide["personal_ui"]["module"] == "threadvault.personal_ui"
    assert guide["personal_ui"]["health_schema"] == "personal_ui_health"
    assert guide["personal_ui"]["action_schema"] == "personal_ui_action"
    assert guide["personal_ui"]["cloud_sync"] is False

    schemas = robot_schemas()
    assert "personal_ui_health" in schemas
    assert "personal_ui_action" in schemas
    assert get_schema("personal_ui_health")["type"] == "object"
    assert get_schema("personal_ui_action")["type"] == "object"

    for path in [
        PHASE_DIR / "plan.md",
        PHASE_DIR / "design-notes.md",
        PHASE_DIR / "acceptance.md",
        Path("docs/progress/archive/legacy-v4/README.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
        Path("docs/schemas/personal_ui_health.schema.json"),
        Path("docs/schemas/personal_ui_action.schema.json"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()


def test_personal_ui_routes_report_structured_errors(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    store = ArchiveStore(db)
    config = PersonalUIServerConfig(db_path=db)

    missing_query = handle_api_get(store, "/api/retrieve", config)
    missing_session = handle_api_get(store, "/api/client/session", config)
    missing_route = handle_api_get(store, "/api/not-real", config)

    assert missing_query["status_code"] == 400
    assert missing_query["payload"]["error"] == "query_required"
    assert missing_session["status_code"] == 400
    assert missing_session["payload"]["error"] == "session_required"
    assert missing_route["status_code"] == 404
    assert missing_route["payload"]["error"] == "route_not_found"

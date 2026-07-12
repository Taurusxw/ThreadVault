from __future__ import annotations

import importlib.util
from pathlib import Path

from typer.testing import CliRunner

import threadvault.desktop_app as desktop_app_module
from threadvault.cli import app
from threadvault.desktop_data import (
    DESKTOP_APP_CONTRACT_VERSION,
    DESKTOP_SMOKE_CONTRACT_VERSION,
    DesktopAppConfig,
    build_desktop_gateway,
    desktop_snapshot_payload,
    run_desktop_smoke,
)
from threadvault.store import capabilities, robot_guide

FIXTURES = Path("tests/fixtures/codex_home")
DESKTOP_LAUNCHER = Path("启动ThreadVault桌面版.cmd")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_desktop_data_gateway_uses_client_contracts_without_raw_paths(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    gateway = build_desktop_gateway(DesktopAppConfig(db_path=db, limit=5))

    snapshot = gateway.snapshot(query="pytest")
    payload = desktop_snapshot_payload(snapshot)

    assert payload["contract_version"] == DESKTOP_APP_CONTRACT_VERSION
    assert payload["sessions"]
    assert payload["search_rows"]
    assert payload["has_query"] is True
    assert payload["selected_session_id"]
    assert "raw_path" not in str(payload)
    assert payload["db_path"] == str(db)


def test_desktop_session_summary_is_small_text_surface(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    gateway = build_desktop_gateway(DesktopAppConfig(db_path=db))

    summary = gateway.session_summary("sess-current")

    assert isinstance(summary, str)
    assert summary.strip()
    assert len(summary) < 2000


def test_desktop_gateway_surfaces_preview_safety_and_integrations(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    gateway = build_desktop_gateway(DesktopAppConfig(db_path=db))

    preview = gateway.export_preview(
        session_id="sess-current",
        out_dir=str(tmp_path / "planned-export"),
        profile="skill",
        privacy_mode="warn",
    )
    warnings = gateway.warnings_summary("sess-current")
    integrations = gateway.integration_summary()
    advanced = gateway.advanced_summary()

    assert "Planned files:" in preview.text
    assert "threadvault export-target skill" in preview.text
    assert "Warnings:" in warnings.text
    assert "threadvault mcp serve" in integrations.text
    assert "threadvault_export_preview" in integrations.text
    assert "threadvault schemas list --json" in advanced.text
    assert "threadvault governance status --json" in advanced.text


def test_desktop_gateway_runs_safe_data_operations(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    gateway = build_desktop_gateway(DesktopAppConfig(db_path=db))
    backup_dir = tmp_path / "backups"

    backup_result = gateway.backup_database(str(backup_dir))
    backup_files = list(backup_dir.glob("*.db"))
    assert "OK: True" in backup_result.text
    assert backup_files

    backup_path = backup_files[0]
    verify_result = gateway.verify_backup(str(backup_path))
    restore_plan = gateway.restore_plan(str(backup_path), str(tmp_path / "restored.db"))
    restore_apply = gateway.restore_to_new_target(str(backup_path), str(tmp_path / "restored.db"))
    restore_refuse_overwrite = gateway.restore_to_new_target(str(backup_path), str(tmp_path / "restored.db"))
    reindex_result = gateway.reindex_search()
    vacuum_result = gateway.vacuum_database()

    assert "OK: True" in verify_result.text
    assert "Mode: read_only_plan" in restore_plan.text
    assert "Mode: applied" in restore_apply.text
    assert (tmp_path / "restored.db").exists()
    assert restore_apply.status == "恢复已执行"
    assert restore_refuse_overwrite.status == "恢复未执行：目标已存在"
    assert reindex_result.status == "索引已重建"
    assert vacuum_result.status == "数据库压缩完成"


def test_desktop_gateway_surfaces_advanced_read_only_panels(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    gateway = build_desktop_gateway(DesktopAppConfig(db_path=db))

    schema_result = gateway.schema_summary("search_minimal")
    robot_result = gateway.robot_docs_summary()
    governance_result = gateway.governance_summary()
    governance_diagnostics = gateway.governance_diagnostics_summary()

    assert "Schema count:" in schema_result.text
    assert "Selected: search_minimal" in schema_result.text
    assert "Recommended commands:" in robot_result.text
    assert "threadvault desktop launch" in robot_result.text
    assert "Server required:" in governance_result.text
    assert "External model calls:" in governance_result.text
    assert "enforcement_gaps:" in governance_diagnostics.text
    assert "v3_completion_gap_audit:" in governance_diagnostics.text


def test_desktop_gateway_writes_schema_files_with_explicit_call(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    gateway = build_desktop_gateway(DesktopAppConfig(db_path=db))
    out_dir = tmp_path / "schemas"

    result = gateway.write_schemas(str(out_dir))

    assert "Written files:" in result.text
    assert result.status.startswith("已写出")
    assert (out_dir / "search_minimal.schema.json").exists()


def test_desktop_smoke_checks_non_window_runtime(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)

    payload = run_desktop_smoke(DesktopAppConfig(db_path=db, limit=5))

    assert payload["contract_version"] == DESKTOP_SMOKE_CONTRACT_VERSION
    assert payload["ok"] is True
    assert payload["desktop"]["toolkit"] == "tkinter"
    assert payload["desktop"]["browser_required"] is False
    assert payload["snapshot"]["session_count"] > 0
    assert payload["snapshot"]["selected_session_id"]


def test_desktop_cli_discovery_does_not_launch_window() -> None:
    runner = CliRunner()

    help_result = runner.invoke(app, ["desktop", "launch", "--help"])
    smoke_help = runner.invoke(app, ["desktop", "smoke", "--help"])

    assert help_result.exit_code == 0, help_result.output
    assert smoke_help.exit_code == 0, smoke_help.output
    assert "--db" in help_result.output
    assert "--limit" in help_result.output
    assert "Launch the primary minimal native desktop app" in help_result.output
    assert "Run a non-window desktop app smoke check" in smoke_help.output

    caps = capabilities()
    assert "desktop" in caps["commands"]
    assert "desktop smoke" in caps["json_outputs"]
    assert caps["interface_policy"]["primary_local_interface"] == "native_desktop"
    assert caps["interface_policy"]["primary_command"] == "threadvault desktop launch"
    assert "retired_interface_status" not in caps["interface_policy"]
    assert "retired_interface_archive" not in caps["interface_policy"]
    assert caps["feature_flags"]["native_desktop_primary"] is True
    assert "personal_web_ui" not in caps["feature_flags"]
    assert "personal_web_ui_retired" not in caps["feature_flags"]

    guide = robot_guide()
    assert guide["interface_policy"]["primary_local_interface"] == "native_desktop"
    assert "retired_interfaces" not in guide
    assert "retired_commands" not in guide
    assert "legacy_fallback_commands" not in guide
    assert guide["desktop_app"]["module"] == "threadvault.desktop_app"
    assert guide["desktop_app"]["status"] == "primary_local_interface"
    assert guide["desktop_app"]["recommended_for_daily_use"] is True
    assert guide["desktop_app"]["toolkit"] == "tkinter"
    assert guide["desktop_app"]["smoke_contract_version"] == DESKTOP_SMOKE_CONTRACT_VERSION
    assert guide["desktop_app"]["server_required"] is False
    assert guide["desktop_app"]["background_worker_threads"] is True
    assert "client_export_preview" in guide["desktop_app"]["store_interface"]
    assert "client_warnings" in guide["desktop_app"]["store_interface"]
    assert "backup" in guide["desktop_app"]["store_interface"]
    assert "restore_plan" in guide["desktop_app"]["store_interface"]
    assert "restore" in guide["desktop_app"]["store_interface"]
    assert "governance_status" in guide["desktop_app"]["store_interface"]
    assert "governance_diagnostics" in guide["desktop_app"]["store_interface"]
    assert "write_schema_files" in guide["desktop_app"]["store_interface"]
    assert "threadvault desktop launch" in guide["recommended_commands"]
    assert "threadvault desktop smoke --json" in guide["recommended_commands"]


def test_v1000_removes_personal_web_ui_runtime_and_schemas() -> None:
    from threadvault.schemas import schema_names

    assert importlib.util.find_spec("threadvault.personal_ui") is None
    assert not Path("src/threadvault/personal_ui.py").exists()

    schemas = set(schema_names())
    assert "personal_ui_health" not in schemas
    assert "personal_ui_action" not in schemas
    assert "personal_ui_smoke" not in schemas
    assert not Path("docs/schemas/personal_ui_health.schema.json").exists()
    assert not Path("docs/schemas/personal_ui_action.schema.json").exists()
    assert not Path("docs/schemas/personal_ui_smoke.schema.json").exists()


def test_desktop_background_workers_do_not_read_tk_variables() -> None:
    source = Path(desktop_app_module.__file__).read_text(encoding="utf-8")

    assert "lambda: self.gateway.snapshot(query=self.query.get()" not in source
    assert "lambda: self.gateway.write_schemas(self.schema_out.get()" not in source
    assert "lambda: self.gateway.schema_summary(self.schema_name.get()" not in source
    assert "lambda: self.gateway.backup_database(self.backup_out.get()" not in source


def test_desktop_windows_launcher_uses_native_app_not_web_ui() -> None:
    text = DESKTOP_LAUNCHER.read_text(encoding="utf-8")

    assert "desktop smoke --json" in text
    assert "desktop launch" in text
    assert "ui serve" not in text
    assert "Start-Process" not in text
    assert not Path("启动ThreadVault中文界面.cmd").exists()

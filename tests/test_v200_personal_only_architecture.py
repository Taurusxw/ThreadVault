from __future__ import annotations

import importlib.util
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import schema_names
from threadvault.store import ArchiveStore, capabilities, robot_guide


def test_team_and_shared_runtime_are_absent() -> None:
    assert importlib.util.find_spec("threadvault.governance") is None
    assert importlib.util.find_spec("threadvault.shared_server") is None
    assert not Path("src/threadvault/governance.py").exists()
    assert not Path("src/threadvault/shared_server.py").exists()
    assert all(not name.startswith("governance_") for name in schema_names())

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    assert "governance" not in result.output.lower()


def test_personal_safety_gates_remain_discoverable() -> None:
    caps = capabilities()
    assert "governance" not in caps["commands"]
    assert {"privacy-scan", "backup", "backup-verify", "restore", "client"} <= set(caps["commands"])
    assert "client export-preview" in caps["json_outputs"]
    assert caps["feature_flags"]["local_first"] is True
    assert caps["feature_flags"]["mcp_read_only_tools"] is True

    manifest = ArchiveStore(Path("unused.db")).client_manifest()
    assert "governance" not in manifest
    assert manifest["interface"]["client_families"] == ["desktop", "ide", "tui"]
    assert manifest["integration_policy"]["do_not_bypass_privacy_scan_for_export"] is True

    guide = robot_guide()
    assert guide["desktop_app"]["server_required"] is False
    assert "client_export_preview" in guide["desktop_app"]["store_interface"]
    assert "backup" in guide["desktop_app"]["store_interface"]
    assert "restore_plan" in guide["desktop_app"]["store_interface"]

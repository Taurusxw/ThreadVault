from __future__ import annotations

import shutil
import subprocess
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.personal_ui import (
    APP_JS,
    APP_JS_ZH,
    INDEX_HTML,
    INDEX_HTML_ZH,
    PersonalUIServerConfig,
    build_personal_ui_server,
    start_personal_ui_close_monitor,
)
from threadvault.store import ArchiveStore

PHASE_DIR = Path("docs/progress/archive/legacy-v4/phases/phase-06-ui-chinese-localization")


def test_personal_ui_english_baseline_stays_default() -> None:
    assert 'lang="en"' in INDEX_HTML
    assert "ThreadVault Personal UI" in INDEX_HTML
    assert "Archive" in INDEX_HTML
    assert "/assets/app.js" in INDEX_HTML
    assert "/assets/app.zh.js" not in INDEX_HTML
    assert "ThreadVault 个人界面" not in INDEX_HTML
    assert "归档" not in APP_JS


def test_personal_ui_chinese_assets_are_additive() -> None:
    assert 'lang="zh-CN"' in INDEX_HTML_ZH
    assert "ThreadVault 个人界面" in INDEX_HTML_ZH
    assert "归档" in INDEX_HTML_ZH
    assert "搜索归档" in INDEX_HTML_ZH
    assert "普通模式" in INDEX_HTML_ZH
    assert "专业模式" in INDEX_HTML_ZH
    assert "JSON 输出" in INDEX_HTML_ZH
    assert "结构定义" in INDEX_HTML_ZH
    assert "/assets/app.zh.js" in INDEX_HTML_ZH
    assert "/assets/app.js" not in INDEX_HTML_ZH
    assert "归档" in APP_JS_ZH
    assert "从你要做的事开始" in APP_JS_ZH
    assert "搜索旧记录" in APP_JS_ZH
    assert "打开最近会话" in APP_JS_ZH
    assert "导出给 Codex 继续用" in APP_JS_ZH
    assert "准备技能包导出" in APP_JS_ZH
    assert "正在生成导出预览" in APP_JS_ZH
    assert "运行中" in APP_JS_ZH
    assert "正在搜索归档" in APP_JS_ZH
    assert "导出流程" in APP_JS_ZH
    assert "1. 选择会话和格式" in APP_JS_ZH
    assert "2. 生成预览" in APP_JS_ZH
    assert "3. 写入文件" in APP_JS_ZH
    assert "下一步：先生成预览" in APP_JS_ZH
    assert "下一步：检查预览" in APP_JS_ZH
    assert "执行前需要确认参数" in APP_JS_ZH
    assert "备份验证" in APP_JS_ZH
    assert "备份历史" in APP_JS_ZH
    assert "恢复计划" in APP_JS_ZH
    assert "恢复历史" in APP_JS_ZH
    assert "结构定义列表" in APP_JS_ZH
    assert "生成预览" in APP_JS_ZH
    assert "预览已生成" in APP_JS_ZH
    assert "写入文件前请先生成匹配的预览" in APP_JS_ZH
    assert "仅警告" in APP_JS_ZH
    assert "自动脱敏" in APP_JS_ZH
    assert "发现高风险则阻止" in APP_JS_ZH
    assert "隐私发现" in APP_JS_ZH
    assert "只读执行备份验证" in APP_JS_ZH
    assert "重建索引" in APP_JS_ZH
    assert "需要确认参数。" in APP_JS_ZH
    assert "Content-Type" in APP_JS_ZH
    assert "/api/action" in APP_JS_ZH
    assert "/api/ui-heartbeat" in APP_JS_ZH
    assert "restore_apply" in APP_JS_ZH
    assert "Basic Mode" not in INDEX_HTML_ZH
    assert "Pro Mode" not in INDEX_HTML_ZH
    assert "Search old records" not in APP_JS_ZH
    assert "Open latest session" not in APP_JS_ZH
    assert "Export for Codex reuse" not in APP_JS_ZH
    assert "Generating export preview" not in APP_JS_ZH
    assert "Choose session and format" not in APP_JS_ZH
    assert "Generate preview" not in APP_JS_ZH
    assert "Write files" not in APP_JS_ZH
    assert "写入文件s" not in APP_JS_ZH
    assert "Running..." not in APP_JS_ZH
    assert "Backup verify" not in APP_JS_ZH
    assert "Restore plan" not in APP_JS_ZH
    assert "Read-only" not in APP_JS_ZH
    assert "Schemas list" not in APP_JS_ZH
    assert "Content-类型" not in APP_JS_ZH
    assert "Doctor" not in APP_JS_ZH
    assert "Vacuum" not in APP_JS_ZH
    assert "dry-run" not in APP_JS_ZH
    assert "allowlist" not in APP_JS_ZH
    assert "agent retrieve" not in APP_JS_ZH
    assert "adapter" not in APP_JS_ZH
    assert ">Skill</option>" not in APP_JS_ZH
    assert "Codex Skill export preview" not in APP_JS_ZH
    assert "Writing Skill export" not in APP_JS_ZH
    assert "clean摘要" not in APP_JS_ZH
    assert "renderExport摘要" not in APP_JS_ZH
    assert "prepareBasic技能包Export" not in APP_JS_ZH
    assert "basic技能包Prompt" not in APP_JS_ZH
    assert "cleanSummary" in APP_JS_ZH
    assert "renderExportSummary" in APP_JS_ZH
    assert "prepareBasicSkillExport" in APP_JS_ZH
    assert "basicSkillPrompt" in APP_JS_ZH


def test_personal_ui_javascript_assets_are_syntax_valid(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        return

    for name, source in {"app.js": APP_JS, "app.zh.js": APP_JS_ZH}.items():
        path = tmp_path / name
        path.write_text(source, encoding="utf-8")
        result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr


def test_personal_ui_serves_english_and_chinese_static_routes(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    store = ArchiveStore(db)
    config = PersonalUIServerConfig(host="127.0.0.1", port=0, db_path=db)
    server = build_personal_ui_server(store, config)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    start_personal_ui_close_monitor(server, config)
    host, port = server.server_address
    base_url = f"http://{host}:{port}"

    try:
        english_html = urlopen(f"{base_url}/", timeout=5).read().decode("utf-8")
        english_js = urlopen(f"{base_url}/assets/app.js", timeout=5).read().decode("utf-8")
        chinese_html = urlopen(f"{base_url}/zh", timeout=5).read().decode("utf-8")
        chinese_js = urlopen(f"{base_url}/assets/app.zh.js", timeout=5).read().decode("utf-8")
        versioned_css_response = urlopen(f"{base_url}/assets/app.css?v=20260702-paths", timeout=5)
        versioned_css = versioned_css_response.read().decode("utf-8")
        heartbeat_response = urlopen(Request(f"{base_url}/api/ui-heartbeat", method="POST"), timeout=5)
        heartbeat_payload = heartbeat_response.read().decode("utf-8")
        heartbeat_seen = server.heartbeat_seen  # type: ignore[attr-defined]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert "ThreadVault Personal UI" in english_html
    assert "ThreadVault 个人界面" not in english_html
    assert "Archive" in english_js
    assert 'lang="zh-CN"' in chinese_html
    assert "ThreadVault 个人界面" in chinese_html
    assert "归档" in chinese_html
    assert "搜索归档" in chinese_html
    assert "普通模式" in chinese_html
    assert "专业模式" in chinese_html
    assert "JSON 输出" in chinese_html
    assert "混合" in chinese_html
    assert "结构定义" in chinese_html
    assert ">Schemas</button>" not in chinese_html
    assert "执行前需要确认参数" in chinese_js
    assert "备份验证" in chinese_js
    assert "从你要做的事开始" in chinese_js
    assert "导出给 Codex 继续用" in chinese_js
    assert "索引库" in chinese_js
    assert "导出目录" in chinese_js
    assert "生成预览" in chinese_js
    assert "仅警告" in chinese_js
    assert "Read-only" not in chinese_js
    assert "/assets/app.css?v=20260702-paths" in chinese_html
    assert "/assets/app.zh.js?v=20260702-paths" in chinese_html
    assert ".json-panel pre" in versioned_css
    assert versioned_css_response.headers["Cache-Control"] == "no-store, max-age=0"
    assert '"ok": true' in heartbeat_payload
    assert heartbeat_seen is True


def test_personal_ui_exit_on_close_stops_after_missing_heartbeat(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    store = ArchiveStore(db)
    config = PersonalUIServerConfig(host="127.0.0.1", port=0, db_path=db, exit_on_close=True, close_timeout_seconds=0.2)
    server = build_personal_ui_server(store, config)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address

    try:
        urlopen(Request(f"http://{host}:{port}/api/ui-heartbeat", method="POST"), timeout=5).read()

        deadline = time.monotonic() + 3
        while thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
    finally:
        if thread.is_alive():
            server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert thread.is_alive() is False


def test_personal_ui_serve_help_and_lang_open_behavior(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    help_result = runner.invoke(app, ["ui", "serve", "--help"])

    assert help_result.exit_code == 0, help_result.output
    assert "--lang" in help_result.output
    assert "en" in help_result.output
    assert "--exit-on-close" in help_result.output

    captured: dict[str, object] = {}

    def fake_serve_personal_ui(store: ArchiveStore, config: PersonalUIServerConfig, *, open_browser: bool = False) -> None:
        captured["config"] = config
        captured["open_browser"] = open_browser

    monkeypatch.setattr("threadvault.cli.serve_personal_ui", fake_serve_personal_ui)

    zh_result = runner.invoke(app, ["ui", "serve", "--db", str(tmp_path / "zh.db"), "--lang", "zh", "--open"])

    assert zh_result.exit_code == 0, zh_result.output
    zh_config = captured["config"]
    assert isinstance(zh_config, PersonalUIServerConfig)
    assert zh_config.language == "zh"
    assert zh_config.open_url == "http://127.0.0.1:8766/zh"
    assert zh_config.exit_on_close is True
    assert captured["open_browser"] is True

    captured.clear()
    en_result = runner.invoke(app, ["ui", "serve", "--db", str(tmp_path / "en.db"), "--open"])

    assert en_result.exit_code == 0, en_result.output
    en_config = captured["config"]
    assert isinstance(en_config, PersonalUIServerConfig)
    assert en_config.language == "en"
    assert en_config.open_url == "http://127.0.0.1:8766"
    assert en_config.exit_on_close is True
    assert captured["open_browser"] is True

    captured.clear()
    no_exit_result = runner.invoke(
        app,
        ["ui", "serve", "--db", str(tmp_path / "keep.db"), "--open", "--no-exit-on-close"],
    )

    assert no_exit_result.exit_code == 0, no_exit_result.output
    no_exit_config = captured["config"]
    assert isinstance(no_exit_config, PersonalUIServerConfig)
    assert no_exit_config.exit_on_close is False


def test_chinese_launcher_detects_and_restarts_stale_local_service() -> None:
    launcher = Path("启动ThreadVault中文界面.cmd").read_text(encoding="utf-8")

    assert "THREADVAULT_READY_MARKER=20260702-paths" in launcher
    assert "Invoke-WebRequest" in launcher
    assert "'Cache-Control'='no-cache'" in launcher
    assert "Stop-Process -Id $conn.OwningProcess -Force" in launcher
    assert "Stale local service was stopped" in launcher


def test_personal_ui_chinese_localization_docs_exist() -> None:
    for path in [
        PHASE_DIR / "plan.md",
        PHASE_DIR / "design-notes.md",
        PHASE_DIR / "acceptance.md",
        Path("docs/progress/archive/legacy-v4/README.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

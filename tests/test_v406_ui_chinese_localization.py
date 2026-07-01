from __future__ import annotations

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

PHASE_DIR = Path("docs/v4/phases/phase-06-ui-chinese-localization")


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
    assert "JSON 输出" in INDEX_HTML_ZH
    assert "/assets/app.zh.js" in INDEX_HTML_ZH
    assert "/assets/app.js" not in INDEX_HTML_ZH
    assert "归档" in APP_JS_ZH
    assert "执行前需要 confirm=true" in APP_JS_ZH
    assert "/api/action" in APP_JS_ZH
    assert "/api/ui-heartbeat" in APP_JS_ZH
    assert "restore_apply" in APP_JS_ZH


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
        versioned_css_response = urlopen(f"{base_url}/assets/app.css?v=20260701-scroll2", timeout=5)
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
    assert "JSON 输出" in chinese_html
    assert "执行前需要 confirm=true" in chinese_js
    assert "/assets/app.css?v=20260701-scroll2" in chinese_html
    assert "/assets/app.zh.js?v=20260701-scroll2" in chinese_html
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


def test_personal_ui_chinese_localization_docs_exist() -> None:
    for path in [
        PHASE_DIR / "plan.md",
        PHASE_DIR / "design-notes.md",
        PHASE_DIR / "acceptance.md",
        Path("docs/v4/README.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

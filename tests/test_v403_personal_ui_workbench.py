from __future__ import annotations

from pathlib import Path

from threadvault.personal_ui import APP_CSS, APP_JS, INDEX_HTML

PHASE_DIR = Path("docs/v4/phases/phase-03-personal-ui-workbench")


def test_personal_ui_workbench_contains_required_view_families() -> None:
    required_labels = [
        "Archive",
        "Search",
        "Session",
        "Export",
        "Privacy",
        "Maintenance",
        "Backup / Restore",
        "Config",
        "Schemas",
        "Governance",
    ]

    for label in required_labels:
        assert label in INDEX_HTML or label in APP_JS

    assert 'class="json-panel"' in INDEX_HTML
    assert 'id="global-search"' in INDEX_HTML
    assert 'id="db-path"' in INDEX_HTML
    assert 'data-view="archive"' in INDEX_HTML
    assert 'data-view="governance"' in INDEX_HTML


def test_personal_ui_workbench_references_existing_read_routes_and_json_panel() -> None:
    required_routes = [
        "/api/health",
        "/api/client/overview",
        "/api/client/session",
        "/api/client/warnings",
        "/api/retrieve",
        "/api/action",
    ]

    for route in required_routes:
        assert route in APP_JS

    assert "JSON.stringify(payload, null, 2)" in APP_JS
    assert "setJson(payload)" in APP_JS
    assert "fetchJson" in APP_JS
    assert "postAction" in APP_JS


def test_personal_ui_workbench_exposes_phase_03_capability_surfaces() -> None:
    required_terms = [
        "Standard search",
        "Retrieval query",
        "Hybrid retrieval",
        "Agent retrieve",
        "summary",
        "event previews",
        "evidence event ids",
        "Export Preview",
        "Privacy Scan",
        "Stats",
        "Doctor",
        "Self-test",
        "Backup verify",
        "Restore plan",
        "Config doctor",
        "Schemas list",
        "Validate JSON",
        "v3 gap audit",
        "v3 acceptance smoke",
        "Instrumentation diagnostics",
    ]

    for term in required_terms:
        assert term in APP_JS


def test_personal_ui_workbench_marks_deferred_dangerous_actions() -> None:
    required_safety_text = [
        "Preview must be generated before writing files.",
        "Requires confirm=true before Phase 04 execution.",
        "Requires confirm=true and a restore plan.",
        "Requires confirm=true before writing artifacts.",
        "Backup may execute directly but must display its target path.",
    ]
    required_actions = [
        "export_target_markdown",
        "export_target_obsidian",
        "export_target_skill",
        "reindex",
        "vacuum",
        "restore_apply",
        "schema_write",
    ]

    for text in required_safety_text:
        assert text in APP_JS
    for action in required_actions:
        assert action in APP_JS


def test_personal_ui_workbench_layout_is_stable_and_responsive() -> None:
    required_css = [
        "grid-template-columns: 220px minmax(420px, 1fr) minmax(320px, 34vw)",
        "height: 100vh",
        "overflow: hidden",
        "grid-template-rows: auto minmax(0, 1fr)",
        ".topbar",
        ".content",
        ".json-panel",
        ".json-panel pre",
        ".table-wrap",
        "@media (max-width: 900px)",
        "height: auto",
        "overflow-wrap: anywhere",
    ]

    for rule in required_css:
        assert rule in APP_CSS


def test_personal_ui_workbench_keeps_native_no_build_constraints_and_docs() -> None:
    combined = INDEX_HTML + APP_CSS + APP_JS

    for forbidden in ["ReactDOM", "createRoot", "vite", "node_modules", "webpack"]:
        assert forbidden not in combined

    for path in [
        PHASE_DIR / "plan.md",
        PHASE_DIR / "design-notes.md",
        PHASE_DIR / "acceptance.md",
        Path("docs/v4/README.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

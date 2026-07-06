from __future__ import annotations

from pathlib import Path

from threadvault.personal_ui import APP_CSS, APP_JS, INDEX_HTML

PHASE_DIR = Path("docs/progress/archive/legacy-v4/phases/phase-03-personal-ui-workbench")


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
    assert 'id="export-path"' in INDEX_HTML
    assert 'id="activity"' in INDEX_HTML
    assert 'data-view="archive"' in INDEX_HTML
    assert 'data-view="governance"' in INDEX_HTML
    assert 'data-ui-mode="basic"' in INDEX_HTML
    assert 'data-ui-mode="pro"' in INDEX_HTML
    assert "Basic Mode" in INDEX_HTML
    assert "Pro Mode" in INDEX_HTML


def test_personal_ui_workbench_exposes_basic_and_pro_modes() -> None:
    required_terms = [
        'const UI_MODE_KEY = "threadvault.uiMode"',
        'uiMode: "basic"',
        'state.activeView = "home"',
        "getStoredMode",
        "setStoredMode",
        "applyMode",
        "mode-basic",
        "mode-pro",
        "renderHome",
        "Search old records",
        "Open latest session",
        "Export for Codex reuse",
        "prepareBasicSkillExport",
        'profile: "skill"',
    ]

    for term in required_terms:
        assert term in APP_JS


def test_personal_ui_workbench_exposes_running_feedback() -> None:
    required_terms = [
        "runWithFeedback",
        "setActivity",
        "setButtonBusy",
        "is-running",
        "is-done",
        "is-failed",
        "aria-busy",
        "activity-steps",
        "actionProgress",
        "renderExportWorkflow",
        "renderExportPrimaryAction",
        "primary-write-action",
        "Export workflow",
        "Generating export preview",
        "Writing Skill export",
        "Searching archive",
        "Opening session",
        "Applying archive filters",
    ]

    for term in required_terms:
        assert term in APP_JS or term in INDEX_HTML or term in APP_CSS


def test_personal_ui_activity_completion_stops_spinner() -> None:
    assert ".activity.is-done .spinner" in APP_CSS
    assert "animation: none;" in APP_CSS
    assert 'node.classList.toggle("is-done", Boolean(done));' in APP_JS
    assert 'node.classList.toggle("is-running", !done && !failed);' in APP_JS


def test_personal_ui_export_summary_does_not_render_privacy_findings_as_paths() -> None:
    assert 'Array.isArray(result.result)) return result.result.map((item) => String(item))' not in APP_JS
    assert 'Array.isArray(result)) return result.map((item) => String(item))' not in APP_JS
    assert 'item && item.path ? item.path : null' in APP_JS
    assert "result.root" in APP_JS
    assert "Index DB" in APP_JS
    assert "Export folder" in APP_JS
    assert "default_export_dir" in APP_JS


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
        "Preview must match Markdown before writing files.",
        "Preview must match Obsidian before writing files.",
        "Preview must match Skill before writing files.",
        "data-disabled-reason",
        "aria-disabled",
        "disabled data-disabled-reason",
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
        "body.mode-basic",
        ".mode-switch",
        ".quick-actions",
        ".quick-action",
        ".result-card",
        ".activity",
        ".spinner",
        ".workflow-step",
        ".workflow-status",
        ".primary-write-action",
        "button.is-disabled",
        "@keyframes spin",
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
        Path("docs/progress/archive/legacy-v4/README.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

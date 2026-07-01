from pathlib import Path

from threadvault.store import capabilities

PHASE_DIR = Path("docs/v4/phases/phase-01-personal-ui-readiness")


def test_v4_phase_01_docs_and_navigation_exist() -> None:
    for path in [
        Path("docs/v4/README.md"),
        PHASE_DIR / "plan.md",
        PHASE_DIR / "design-notes.md",
        PHASE_DIR / "coverage-matrix.md",
        PHASE_DIR / "acceptance.md",
        Path("docs/v4/phases/phase-02-local-ui-server/plan.md"),
        Path("docs/v4/phases/phase-03-personal-ui-workbench/plan.md"),
        Path("docs/v4/phases/phase-04-ui-action-coverage/plan.md"),
        Path("docs/v4/phases/phase-05-v4-acceptance-smoke/plan.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"

    readme = Path("docs/v4/README.md").read_text(encoding="utf-8")
    plan = (PHASE_DIR / "plan.md").read_text(encoding="utf-8")
    notes = (PHASE_DIR / "design-notes.md").read_text(encoding="utf-8")

    assert "ThreadVault Personal Web UI" in readme
    assert "127.0.0.1" in readme
    assert "ArchiveStore" in readme
    assert "Do not rewrite the Codex JSONL parser" in readme
    assert "No Web server implementation" in plan
    assert "run_ui_action" in notes
    assert not Path("deep-research-report.md").exists()


def test_v4_future_phase_plans_preserve_requested_public_interfaces() -> None:
    phase_02 = Path("docs/v4/phases/phase-02-local-ui-server/plan.md").read_text(encoding="utf-8")
    phase_03 = Path("docs/v4/phases/phase-03-personal-ui-workbench/plan.md").read_text(encoding="utf-8")
    phase_04 = Path("docs/v4/phases/phase-04-ui-action-coverage/plan.md").read_text(encoding="utf-8")
    phase_05 = Path("docs/v4/phases/phase-05-v4-acceptance-smoke/plan.md").read_text(encoding="utf-8")

    assert "src/threadvault/personal_ui.py" in phase_02
    assert "threadvault ui serve --host 127.0.0.1 --port 8766 --open" in phase_02
    assert "POST /api/action" in phase_02
    assert "ArchiveStore" in phase_02
    assert "No shelling out" in phase_02
    assert "right JSON output panel" in phase_03
    assert "Advanced Governance" in phase_03
    assert "restore_apply" in phase_04
    assert "`vacuum` requires `confirm=true`" in phase_04
    assert "`schema_write` requires `confirm=true`" in phase_04
    assert "threadvault ui smoke --json" in phase_05
    assert "personal_ui_health" in phase_05
    assert "personal_web_ui: true" in phase_05
    assert "personal_ui_cloud_sync: false" in phase_05


def test_v4_coverage_matrix_covers_required_personal_ui_capabilities() -> None:
    matrix = (PHASE_DIR / "coverage-matrix.md").read_text(encoding="utf-8")

    required_terms = [
        "Initialize database",
        "Import Codex sessions",
        "Ingestion queue enqueue/list/process",
        "Session list",
        "Session detail",
        "Retrieval query",
        "Hybrid retrieval",
        "Agent retrieve",
        "Summary chunks",
        "Vector status/index/query",
        "Summarize",
        "Privacy scan",
        "Warnings",
        "Export session",
        "Export-target markdown",
        "Export-target obsidian",
        "Export-target skill",
        "Client overview",
        "Client export preview",
        "Config init/show/doctor",
        "Stats",
        "Doctor",
        "Self-test",
        "Reindex",
        "Vacuum",
        "Backup",
        "Restore plan",
        "Restore apply",
        "Audit corpus",
        "Audit history",
        "Schemas list/show/validate/write",
        "Capabilities",
        "Robot docs guide",
        "Robot docs schemas",
        "v3 governance status",
        "v3 governance gap audit",
        "v3 acceptance smoke",
        "Governance preflight",
        "Governance instrumentation diagnostics",
    ]
    for term in required_terms:
        assert term in matrix, f"coverage matrix missing {term}"

    for safety_term in [
        "Requires `confirm=true`",
        "Preview before execution",
        "Prune dry-run by default",
        "Show target path",
        "No parser rewrite",
    ]:
        assert safety_term in matrix


def test_v4_readiness_reuses_existing_discovery_surface() -> None:
    caps = capabilities()

    for command in [
        "init",
        "import",
        "ingest-queue",
        "retrieval",
        "summary-pipeline",
        "vector",
        "agent",
        "client",
        "governance",
        "export-target",
        "backup",
        "restore",
        "schemas",
        "config",
    ]:
        assert command in caps["commands"]

    flags = caps["feature_flags"]
    assert flags["local_first"] is True
    assert flags["cloud_sync"] is False
    assert flags["external_llm_summary"] is False
    assert flags["agent_retrieval_interface"] is True
    assert flags["client_interface_manifest"] is True
    assert flags["governance_v3_acceptance_smoke"] is True
    assert flags["local_vector_enabled_by_default"] is False

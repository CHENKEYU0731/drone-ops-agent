from pathlib import Path

from packages.platform_readiness import build_report_bundle_manifest, validate_platform_readiness


def test_build_report_bundle_manifest_lists_local_report_files(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    audit_dir = report_dir / "audit"
    audit_dir.mkdir(parents=True)
    for relative in [
        "flight_summary.json",
        "anomalies.json",
        "diagnosis.json",
        "maintenance_recommendations.json",
        "ops_report.md",
        "evidence_index.json",
        "report_validation.json",
        "audit/flight-log-analysis-RUN.json",
    ]:
        path = report_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    manifest = build_report_bundle_manifest(
        report_dir=report_dir,
        workspace_project_id="workspace-local-demo",
        bundle_id="bundle-local-test",
        drone_id="UAV-001",
    )

    assert manifest.bundle_id == "bundle-local-test"
    assert manifest.file_refs == sorted(manifest.file_refs)
    assert "ops_report.md" in manifest.file_refs
    assert "audit/flight-log-analysis-RUN.json" in manifest.file_refs
    assert manifest.safety_boundary["offline_only"] is True
    assert manifest.safety_boundary["no_external_upload"] is True


def test_validate_platform_readiness_passes_sample_fixtures() -> None:
    result = validate_platform_readiness(
        workspace_path=Path("data/sample_platform/workspace_project.json"),
        bundle_path=Path("data/sample_platform/report_bundle_manifest.json"),
        checklist_path=Path("data/sample_platform/platform_readiness_checklist.json"),
        adapter_paths=[],
    )

    assert result["status"] == "PASS"
    assert result["counts"]["findings"] == 0
    assert result["safety_boundary"]["offline_only"] is True
    assert result["human_review_required"] is True

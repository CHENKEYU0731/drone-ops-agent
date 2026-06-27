from pathlib import Path

from packages.drone_schemas import (
    OfflineAdapterContract,
    PlatformReadinessChecklist,
    ReportBundleManifest,
    ReviewerApproval,
    WorkspaceProject,
    load_model,
)


def test_platform_readiness_contracts_are_offline_and_reviewable() -> None:
    workspace = WorkspaceProject(
        project_id="workspace-local-demo",
        name="Local demo workspace",
        root_ref="data/sample_platform/workspace_project.json",
        asset_refs=["data/sample_assets/uav_001.json"],
        report_bundle_refs=["data/sample_platform/report_bundle_manifest.json"],
        reviewer_roles=["maintenance_lead", "safety_reviewer"],
        retention_policy={"classification": "sanitized_sample", "retain_days": 30},
        safety_boundary={"offline_only": True, "advisory_only": True},
    )
    bundle = ReportBundleManifest(
        bundle_id="bundle-uav-001-demo",
        workspace_project_id=workspace.project_id,
        source_report_dir="data/sample_reports",
        file_refs=["ops_report.md", "flight_summary.json", "audit/flight-log-analysis.json"],
        manifest_hash="sha256:sample",
        export_format="directory-json",
        safety_boundary={"offline_only": True, "no_external_upload": True},
    )
    approval = ReviewerApproval(
        approval_id="approval-uav-001-demo",
        subject_ref=bundle.bundle_id,
        reviewer_id="reviewer-local",
        reviewer_role="maintenance_lead",
        decision="REVIEW_REQUIRED",
        rationale="Sample bundle needs human review before any real workflow.",
        evidence_refs=[],
    )
    adapter = OfflineAdapterContract(
        adapter_id="mock-cmms-export",
        adapter_type="work_order_export",
        direction="export",
        allowed_operations=["render_local_file"],
        prohibited_operations=["api_call", "auto_dispatch", "mavlink_command"],
        safety_boundary={"offline_only": True, "no_real_platform_connection": True},
    )

    assert workspace.human_review_required is True
    assert bundle.file_count == 3
    assert approval.human_review_required is True
    assert approval.decision == "REVIEW_REQUIRED"
    assert adapter.human_review_required is True
    assert adapter.prohibited_operations == sorted(adapter.prohibited_operations)


def test_sample_platform_readiness_fixtures_load() -> None:
    workspace = load_model(Path("data/sample_platform/workspace_project.json"), WorkspaceProject)
    bundle = load_model(Path("data/sample_platform/report_bundle_manifest.json"), ReportBundleManifest)
    checklist = load_model(Path("data/sample_platform/platform_readiness_checklist.json"), PlatformReadinessChecklist)

    assert workspace.project_id == "workspace-local-demo"
    assert bundle.workspace_project_id == workspace.project_id
    assert checklist.checklist_id == "platform-readiness-v1-5"
    assert checklist.safety_boundary["offline_only"] is True
    assert [item["check_id"] for item in checklist.checks] == sorted(item["check_id"] for item in checklist.checks)

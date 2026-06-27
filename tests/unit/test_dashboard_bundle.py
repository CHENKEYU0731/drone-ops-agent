from pathlib import Path

from packages.dashboard import build_dashboard_bundle


def test_dashboard_bundle_collects_local_artifact_refs() -> None:
    bundle = build_dashboard_bundle(
        report_dir=Path("data/sample_reports"),
        fleet_summary=Path("data/sample_reports/fleet_health_summary.json"),
        fleet_report=Path("data/sample_reports/fleet_health_report.md"),
    )

    assert bundle["schema_version"] == 1
    assert bundle["bundle_id"] == "DASHBOARD-BUNDLE-OFFLINE"
    assert bundle["generated_at"] == "1970-01-01T00:00:00Z"
    assert bundle["safety_boundary"] == {
        "offline_only": True,
        "read_only": True,
        "advisory_only": True,
        "real_drone_connection": False,
        "external_platform_connection": False,
    }
    assert bundle["sections"] == [
        "report",
        "simulation",
        "work_orders",
        "fleet_health",
        "audit",
        "evidence",
    ]
    assert bundle["artifacts"]["report"]["ops_report_md"] == "data/sample_reports/ops_report.md"
    assert bundle["artifacts"]["simulation"]["simulation_run"] == "data/sample_reports/simulation_run.json"
    assert bundle["artifacts"]["fleet_health"]["fleet_health_summary"] == "data/sample_reports/fleet_health_summary.json"
    assert bundle["artifacts"]["fleet_health"]["fleet_health_report"] == "data/sample_reports/fleet_health_report.md"
    assert bundle["artifacts"]["evidence"]["evidence_index"] == "data/sample_reports/evidence_index.json"
    assert bundle["human_review_required"] is True


def test_dashboard_bundle_keeps_missing_optional_paths_null() -> None:
    bundle = build_dashboard_bundle(report_dir=Path("data/sample_reports"))

    assert bundle["artifacts"]["fleet_health"]["fleet_health_summary"] is None
    assert bundle["artifacts"]["fleet_health"]["fleet_health_report"] is None

from pathlib import Path

from scripts.generate_demo_outputs import generate_demo_outputs


def test_generate_demo_outputs_creates_showcase_package(tmp_path: Path) -> None:
    out_dir = tmp_path / "demo_outputs"

    generated = generate_demo_outputs(out_dir)

    expected_files = {
        "README.md",
        "reports/flight_summary.json",
        "reports/anomalies.json",
        "reports/diagnosis.json",
        "reports/maintenance_recommendations.json",
        "reports/ops_report.md",
        "reports/ops_report.pdf",
        "reports/evidence_index.json",
        "reports/report_validation.json",
        "reports/simulation_run.json",
        "reports/work_order_drafts.json",
        "reports/work_order_drafts.md",
        "reports/work_order_validation.json",
        "fleet/fleet_health_summary.json",
        "fleet/fleet_health_report.md",
        "dashboard/dashboard_bundle.json",
        "platform/platform_index_validation.json",
        "platform/operations_platform_validation.json",
    }

    assert expected_files.issubset({path.as_posix() for path in generated})
    assert (out_dir / "reports" / "audit").exists()
    readme = (out_dir / "README.md").read_text(encoding="utf-8")
    assert "无人机运维 Agent 示例成果包" in readme
    assert "offline-only" in readme
    assert "advisory-only" in readme
    assert "不连接真实无人机" in readme

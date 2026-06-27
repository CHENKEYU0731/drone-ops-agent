from pathlib import Path

from packages.fleet_health import build_fleet_health_summary, load_fleet_manifest, render_fleet_health_report


def test_render_fleet_health_report_includes_rankings_findings_and_safety_boundary() -> None:
    manifest = load_fleet_manifest(Path("data/sample_fleet/fleet_manifest.json"))
    summary = build_fleet_health_summary(manifest)

    report = render_fleet_health_report(summary)

    assert "# 机队健康趋势报告" in report
    assert "FLEET-DEMO" in report
    assert "## 2. 风险排名" in report
    assert "`UAV-002`" in report
    assert "`UAV-001`" in report
    assert "## 3. 机队级发现" in report
    assert "FLEET-FINDING-BATTERY-UAV-002" in report
    assert "FLEET_LOW_BATTERY_TREND" in report
    assert "## 5. 安全边界" in report
    assert "不连接真实无人机" in report
    assert "不代表真实飞行授权" in report

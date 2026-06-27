from pathlib import Path


def test_v1_1_release_readiness_document_covers_fleet_checks() -> None:
    path = Path("docs/v1.1.0_release_readiness.md")
    assert path.exists()

    text = path.read_text(encoding="utf-8")
    assert "fleet-summary" in text
    assert "fleet_health_summary.json" in text
    assert "fleet_health_report.md" in text
    assert "tests/unit/test_fleet_health_aggregation.py" in text
    assert "tests/unit/test_fleet_health_report.py" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text

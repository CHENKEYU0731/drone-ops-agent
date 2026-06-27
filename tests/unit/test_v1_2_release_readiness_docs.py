from pathlib import Path


def test_v1_2_release_readiness_doc_covers_dashboard_gate() -> None:
    text = Path("docs/v1.2.0_release_readiness.md").read_text(encoding="utf-8")

    assert "dashboard-bundle" in text
    assert "dashboard_bundle.json" in text
    assert "GET /health" in text
    assert "GET /api/dashboard/bundle" in text
    assert "无人机运维 Dashboard" in text
    assert "pytest" in text
    assert "GitHub Actions" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
    assert "MAVLink command execution" in text

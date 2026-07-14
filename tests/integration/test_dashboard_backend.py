from pathlib import Path

from starlette.testclient import TestClient

from packages.dashboard.backend import create_dashboard_app


def test_dashboard_backend_serves_read_only_bundle(tmp_path: Path) -> None:
    bundle_path = tmp_path / "dashboard_bundle.json"
    bundle_path.write_text(
        """
{
  "schema_version": 1,
  "bundle_id": "DASHBOARD-BUNDLE-OFFLINE",
  "generated_at": "1970-01-01T00:00:00Z",
  "human_review_required": true,
  "safety_boundary": {
    "offline_only": true,
    "read_only": true,
    "advisory_only": true,
    "real_drone_connection": false,
    "external_platform_connection": false
  },
  "sections": ["report", "simulation"],
  "artifacts": {
    "report": {"ops_report_md": "data/sample_reports/ops_report.md"},
    "simulation": {"simulation_run": "data/sample_reports/simulation_run.json"}
  }
}
""".strip(),
        encoding="utf-8",
    )

    client = TestClient(create_dashboard_app(bundle_path=bundle_path))

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "mode": "offline-read-only",
        "human_review_required": True,
    }

    response = client.get("/api/dashboard/bundle")
    assert response.status_code == 200
    payload = response.json()
    assert payload["bundle_id"] == "DASHBOARD-BUNDLE-OFFLINE"
    assert payload["safety_boundary"]["offline_only"] is True


def test_dashboard_backend_rejects_write_methods(tmp_path: Path) -> None:
    bundle_path = tmp_path / "dashboard_bundle.json"
    bundle_path.write_text('{"bundle_id": "DASHBOARD-BUNDLE-OFFLINE"}', encoding="utf-8")

    client = TestClient(create_dashboard_app(bundle_path=bundle_path))

    response = client.post("/api/dashboard/bundle", json={"unsafe": True})

    assert response.status_code == 405


def test_dashboard_backend_serves_minimal_dashboard_page(tmp_path: Path) -> None:
    bundle_path = tmp_path / "dashboard_bundle.json"
    bundle_path.write_text('{"bundle_id": "DASHBOARD-BUNDLE-OFFLINE"}', encoding="utf-8")

    client = TestClient(create_dashboard_app(bundle_path=bundle_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "无人机运维 Dashboard" in response.text
    assert "offline-only" in response.text
    assert "/api/dashboard/bundle" in response.text
    assert "innerHTML" not in response.text
    assert "content.textContent" in response.text

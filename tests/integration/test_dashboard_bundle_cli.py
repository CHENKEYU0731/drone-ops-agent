from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_dashboard_bundle_cli_writes_bundle(tmp_path: Path) -> None:
    out_path = tmp_path / "dashboard_bundle.json"

    result = runner.invoke(
        app,
        [
            "dashboard-bundle",
            "--report-dir",
            "data/sample_reports",
            "--fleet-summary",
            "data/sample_reports/fleet_health_summary.json",
            "--fleet-report",
            "data/sample_reports/fleet_health_report.md",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["bundle_id"] == "DASHBOARD-BUNDLE-OFFLINE"
    assert payload["artifacts"]["report"]["ops_report_md"] == "data/sample_reports/ops_report.md"
    assert payload["artifacts"]["fleet_health"]["fleet_health_summary"] == "data/sample_reports/fleet_health_summary.json"
    assert payload["safety_boundary"]["offline_only"] is True
    assert payload["human_review_required"] is True

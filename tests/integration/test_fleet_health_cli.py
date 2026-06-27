from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_fleet_summary_cli_writes_summary_and_audit(tmp_path: Path) -> None:
    out_dir = tmp_path / "fleet"

    result = runner.invoke(
        app,
        [
            "fleet-summary",
            "--manifest",
            "data/sample_fleet/fleet_manifest.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    summary_path = out_dir / "fleet_health_summary.json"
    assert summary_path.exists()
    payload = read_json_file(summary_path)
    assert isinstance(payload, dict)
    assert payload["fleet_id"] == "FLEET-DEMO"
    assert payload["highest_risk"] == "HIGH"
    assert [item["asset_id"] for item in payload["risk_rankings"]] == ["UAV-002", "UAV-001"]
    assert payload["human_review_required"] is True

    audits = sorted((out_dir / "audit").glob("fleet-health-analytics-*.json"))
    assert len(audits) == 1
    audit = read_json_file(audits[0])
    assert isinstance(audit, dict)
    assert audit["skill_name"] == "fleet-health-analytics"
    assert audit["human_review_required"] is True
    assert audit["metadata"]["safety_boundary"] == "offline-fleet-summary-only"

from pathlib import Path

from packages.drone_schemas import FleetRiskLevel
from packages.fleet_health import build_fleet_health_summary, load_fleet_manifest


def test_build_fleet_health_summary_from_local_manifest() -> None:
    manifest = load_fleet_manifest(Path("data/sample_fleet/fleet_manifest.json"))

    summary = build_fleet_health_summary(manifest)

    assert summary.fleet_id == "FLEET-DEMO"
    assert summary.asset_count == 2
    assert summary.flight_count == 3
    assert summary.highest_risk == FleetRiskLevel.HIGH
    assert summary.human_review_required is True
    assert [item["asset_id"] for item in summary.risk_rankings] == ["UAV-002", "UAV-001"]
    assert [item["risk_score"] for item in summary.risk_rankings] == [86, 59]
    assert [finding.finding_id for finding in summary.findings] == [
        "FLEET-FINDING-BATTERY-UAV-002",
        "FLEET-FINDING-GPS-UAV-001",
        "FLEET-FINDING-VIBRATION-UAV-002",
    ]
    assert all(finding.evidence_refs for finding in summary.findings)
    assert summary.source_refs == sorted(summary.source_refs)


def test_fleet_health_summary_is_deterministic() -> None:
    manifest = load_fleet_manifest(Path("data/sample_fleet/fleet_manifest.json"))

    first = build_fleet_health_summary(manifest).model_dump(mode="json")
    second = build_fleet_health_summary(manifest).model_dump(mode="json")

    assert first == second

from datetime import UTC, datetime

from pydantic import ValidationError
import pytest

from packages.drone_schemas import (
    EvidenceRef,
    FleetAsset,
    FleetHealthFinding,
    FleetHealthSummary,
    FleetRiskLevel,
)


def _evidence(rule_id: str = "FLEET_LOW_BATTERY_TREND") -> EvidenceRef:
    return EvidenceRef(
        source_type="flight_summary",
        source_id="reports/uav-001-flight-001/flight_summary.json",
        timestamp=datetime(2026, 6, 26, 10, 0, tzinfo=UTC),
        field="min_battery_soc_pct",
        measured_value=18,
        threshold=25,
        rule_id=rule_id,
        description="Fleet trend evidence from an offline flight summary.",
    )


def test_fleet_asset_contract_groups_local_assets() -> None:
    asset = FleetAsset(
        fleet_id="FLEET-DEMO",
        name="Demo maintenance fleet",
        asset_ids=["UAV-001", "UAV-002"],
        source_refs=["data/sample_assets/uav_001.json", "data/sample_assets/uav_002.json"],
        generated_by_skill="fleet-health-analytics",
        skill_version="1.1.0",
    )

    assert asset.fleet_id == "FLEET-DEMO"
    assert asset.asset_count == 2
    assert asset.human_review_required is True


def test_fleet_health_summary_requires_evidence_back_to_local_outputs() -> None:
    finding = FleetHealthFinding(
        finding_id="FLEET-FINDING-001",
        category="battery",
        risk_level=FleetRiskLevel.HIGH,
        affected_assets=["UAV-001"],
        affected_flights=["reports/uav-001-flight-001"],
        summary="UAV-001 repeatedly crossed the low battery threshold.",
        evidence_refs=[_evidence()],
        recommended_action="Review battery maintenance history before the next fleet assignment.",
    )
    summary = FleetHealthSummary(
        fleet_id="FLEET-DEMO",
        window_start=datetime(2026, 6, 24, tzinfo=UTC),
        window_end=datetime(2026, 6, 26, tzinfo=UTC),
        asset_count=2,
        flight_count=3,
        highest_risk=FleetRiskLevel.HIGH,
        risk_rankings=[{"asset_id": "UAV-001", "risk_score": 82, "risk_level": "HIGH"}],
        findings=[finding],
        evidence_refs=[_evidence()],
        source_refs=[
            "reports/uav-001-flight-001/flight_summary.json",
            "reports/uav-001-flight-001/maintenance_recommendations.json",
        ],
        generated_by_skill="fleet-health-analytics",
        skill_version="1.1.0",
    )

    assert summary.human_review_required is True
    assert summary.findings[0].evidence_refs[0].source_type == "flight_summary"
    assert summary.highest_risk == FleetRiskLevel.HIGH
    assert summary.source_refs == sorted(summary.source_refs)


def test_fleet_health_summary_rejects_reversed_window() -> None:
    with pytest.raises(ValidationError):
        FleetHealthSummary(
            fleet_id="FLEET-DEMO",
            window_start=datetime(2026, 6, 27, tzinfo=UTC),
            window_end=datetime(2026, 6, 26, tzinfo=UTC),
            asset_count=1,
            flight_count=1,
            highest_risk=FleetRiskLevel.LOW,
            risk_rankings=[],
            findings=[],
            evidence_refs=[],
            source_refs=[],
            generated_by_skill="fleet-health-analytics",
            skill_version="1.1.0",
        )

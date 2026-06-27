from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from packages.drone_schemas import (
    EvidenceRef,
    FleetHealthFinding,
    FleetHealthSummary,
    FleetRiskLevel,
    FlightLogSummary,
    MaintenanceRecommendation,
    MaintenancePriority,
    load_model,
    load_model_list,
)


DETERMINISTIC_CREATED_AT = datetime(1970, 1, 1, tzinfo=UTC)


class FleetFlightInput(BaseModel):
    asset_id: str
    flight_id: str
    summary: str
    maintenance: str | None = None


class FleetManifest(BaseModel):
    fleet_id: str
    name: str
    window_start: datetime
    window_end: datetime
    flights: list[FleetFlightInput] = Field(default_factory=list)


def load_fleet_manifest(path: Path) -> FleetManifest:
    return load_model(path, FleetManifest)


def build_fleet_health_summary(manifest: FleetManifest) -> FleetHealthSummary:
    summaries = [_LoadedFlight.from_input(item) for item in manifest.flights]
    by_asset: dict[str, list[_LoadedFlight]] = defaultdict(list)
    for item in summaries:
        by_asset[item.asset_id].append(item)

    findings: list[FleetHealthFinding] = []
    risk_rankings: list[dict[str, Any]] = []
    for asset_id in sorted(by_asset):
        asset_flights = sorted(by_asset[asset_id], key=lambda item: item.flight_id)
        asset_findings, score = _find_asset_risks(asset_id, asset_flights)
        findings.extend(asset_findings)
        risk_rankings.append(
            {
                "asset_id": asset_id,
                "risk_score": score,
                "risk_level": _risk_level(score).value,
                "flight_count": len(asset_flights),
            }
        )

    risk_rankings = sorted(risk_rankings, key=lambda item: (-int(item["risk_score"]), str(item["asset_id"])))
    sorted_findings = sorted(findings, key=lambda item: item.finding_id)
    evidence_refs = [ref for finding in sorted_findings for ref in finding.evidence_refs]
    source_refs = sorted({str(item.summary_path) for item in summaries} | {str(item.maintenance_path) for item in summaries if item.maintenance_path})
    highest_risk = _highest_risk(risk_rankings)

    return FleetHealthSummary(
        id=f"FLEETSUM-{manifest.fleet_id}",
        fleet_id=manifest.fleet_id,
        timestamp=DETERMINISTIC_CREATED_AT,
        window_start=manifest.window_start,
        window_end=manifest.window_end,
        asset_count=len(by_asset),
        flight_count=len(summaries),
        highest_risk=highest_risk,
        risk_rankings=risk_rankings,
        findings=sorted_findings,
        evidence_refs=evidence_refs,
        source_refs=source_refs,
        drone_id=None,
        human_review_required=True,
        generated_by_skill="fleet-health-analytics",
        skill_version="1.1.0",
    )


class _LoadedFlight:
    def __init__(
        self,
        *,
        asset_id: str,
        flight_id: str,
        summary_path: Path,
        summary: FlightLogSummary,
        maintenance_path: Path | None,
        maintenance: list[MaintenanceRecommendation],
    ) -> None:
        self.asset_id = asset_id
        self.flight_id = flight_id
        self.summary_path = summary_path
        self.summary = summary
        self.maintenance_path = maintenance_path
        self.maintenance = maintenance

    @classmethod
    def from_input(cls, item: FleetFlightInput) -> "_LoadedFlight":
        summary_path = Path(item.summary)
        maintenance_path = Path(item.maintenance) if item.maintenance else None
        return cls(
            asset_id=item.asset_id,
            flight_id=item.flight_id,
            summary_path=summary_path,
            summary=load_model(summary_path, FlightLogSummary),
            maintenance_path=maintenance_path,
            maintenance=load_model_list(maintenance_path, MaintenanceRecommendation) if maintenance_path else [],
        )


def _find_asset_risks(asset_id: str, flights: list[_LoadedFlight]) -> tuple[list[FleetHealthFinding], int]:
    findings: list[FleetHealthFinding] = []
    score = 0

    low_battery_flights = [item for item in flights if item.summary.min_battery_soc_pct < 25]
    if low_battery_flights:
        score += 40 + 10 * (len(low_battery_flights) - 1)
        findings.append(_finding(asset_id, "battery", "Battery reserve repeatedly crossed review thresholds.", low_battery_flights, "min_battery_soc_pct", 25, "FLEET_LOW_BATTERY_TREND"))

    gps_degraded_flights = [
        item
        for item in flights
        if float(item.summary.gps_summary.get("min_satellites", item.summary.gps_summary.get("min_sats", 99))) < 8
        or float(item.summary.gps_summary.get("max_hdop", 0)) > 1.8
    ]
    if gps_degraded_flights:
        score += 35
        findings.append(_finding(asset_id, "gps", "GPS quality degraded in one or more flights.", gps_degraded_flights, "gps_summary", "satellites>=8 hdop<=1.8", "FLEET_GPS_DEGRADATION_TREND"))

    vibration_flights = [
        item
        for item in flights
        if max(float(item.summary.vibration_summary.get(axis, 0)) for axis in ("max_x", "max_y", "max_z")) > 1.0
    ]
    if vibration_flights:
        score += 30
        findings.append(_finding(asset_id, "vibration", "Vibration exceeded fleet review thresholds.", vibration_flights, "vibration_summary", 1.0, "FLEET_VIBRATION_TREND"))

    if any(
        rec.priority in {MaintenancePriority.IMMEDIATE_GROUNDING, MaintenancePriority.BEFORE_NEXT_FLIGHT}
        for item in flights
        for rec in item.maintenance
    ):
        score += 16
    elif any(
        rec.priority == MaintenancePriority.POST_FLIGHT_INSPECTION
        for item in flights
        for rec in item.maintenance
    ):
        score += 24

    return findings, min(score, 100)


def _finding(
    asset_id: str,
    category: str,
    summary: str,
    flights: list[_LoadedFlight],
    field: str,
    threshold: float | int | str,
    rule_id: str,
) -> FleetHealthFinding:
    evidence_refs = [
        EvidenceRef(
            source_type="flight_summary",
            source_id=str(item.summary_path),
            timestamp=item.summary.end_time,
            field=field,
            measured_value=_measured_value(item.summary, field),
            threshold=threshold,
            rule_id=rule_id,
            description=f"{summary} Flight={item.flight_id}; asset={asset_id}.",
        )
        for item in flights
    ]
    return FleetHealthFinding(
        finding_id=f"FLEET-FINDING-{category.upper()}-{asset_id}",
        category=category,
        risk_level=_risk_level_for_category(category),
        affected_assets=[asset_id],
        affected_flights=[item.flight_id for item in flights],
        summary=summary,
        evidence_refs=evidence_refs,
        recommended_action="Review offline evidence and maintenance context before assigning future fleet missions.",
        human_review_required=True,
    )


def _measured_value(summary: FlightLogSummary, field: str) -> float | int | str:
    if field == "min_battery_soc_pct":
        return summary.min_battery_soc_pct
    if field == "vibration_summary":
        return max(float(summary.vibration_summary.get(axis, 0)) for axis in ("max_x", "max_y", "max_z"))
    return str(summary.gps_summary)


def _risk_level(score: int) -> FleetRiskLevel:
    if score >= 80:
        return FleetRiskLevel.HIGH
    if score >= 50:
        return FleetRiskLevel.REVIEW_REQUIRED
    if score > 0:
        return FleetRiskLevel.LOW
    return FleetRiskLevel.PASS


def _risk_level_for_category(category: str) -> FleetRiskLevel:
    if category in {"battery", "vibration"}:
        return FleetRiskLevel.HIGH
    return FleetRiskLevel.REVIEW_REQUIRED


def _highest_risk(rankings: list[dict[str, Any]]) -> FleetRiskLevel:
    if not rankings:
        return FleetRiskLevel.PASS
    return _risk_level(max(int(item["risk_score"]) for item in rankings))

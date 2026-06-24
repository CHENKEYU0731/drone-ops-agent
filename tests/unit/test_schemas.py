from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from packages.drone_schemas import (
    AnomalyEvent,
    DroneAsset,
    EvidenceRef,
    FaultHypothesis,
    FlightLogRecord,
    MaintenancePriority,
    MaintenanceRecommendation,
    PreflightCheckItem,
    PreflightCheckResult,
    Severity,
    SkillRunAudit,
)


def evidence() -> EvidenceRef:
    return EvidenceRef(
        source_type="log",
        source_id="example_flight.csv:4",
        timestamp=datetime(2026, 6, 24, 10, 0, tzinfo=UTC),
        field="battery_soc_pct",
        measured_value=18,
        threshold=25,
        rule_id="BATTERY_LOW_SOC",
        description="电池 SOC 低于阈值。",
    )


def test_drone_asset_requires_identifier() -> None:
    asset = DroneAsset(
        drone_id="UAV-001",
        model="Quad-X4",
        serial_number="SN-001",
        firmware_version="simulated",
        total_flight_hours=42.5,
        battery_ids=["BAT-001"],
        maintenance_history=["2026-06-01 更换桨叶"],
    )

    assert asset.drone_id == "UAV-001"
    assert asset.battery_ids == ["BAT-001"]


def test_flight_log_record_validates_numeric_ranges() -> None:
    with pytest.raises(ValidationError):
        FlightLogRecord(
            timestamp=datetime(2026, 6, 24, 10, 0, tzinfo=UTC),
            flight_mode="AUTO",
            altitude_m=12,
            battery_voltage_v=15.2,
            battery_current_a=18,
            battery_soc_pct=120,
            gps_satellites=12,
            gps_hdop=0.9,
            vibration_x=0.2,
            vibration_y=0.2,
            vibration_z=0.3,
            motor_1_output=45,
            motor_2_output=46,
            motor_3_output=44,
            motor_4_output=45,
            link_quality_pct=96,
            temperature_c=34,
        )


def test_output_models_carry_evidence_and_human_review() -> None:
    ref = evidence()
    anomaly = AnomalyEvent(
        anomaly_id="ANOM-001",
        type="LOW_BATTERY_SOC",
        severity=Severity.HIGH,
        timestamp=ref.timestamp,
        evidence_refs=[ref],
        human_readable_summary="电池电量偏低。",
        rule_id="BATTERY_LOW_SOC",
        measured_value=18,
        threshold=25,
        drone_id="UAV-001",
        generated_by_skill="flight-log-analysis",
        skill_version="1.0.0",
    )
    fault = FaultHypothesis(
        fault_id="FAULT-001",
        fault_name="电池健康衰退",
        confidence=0.8,
        severity=Severity.HIGH,
        supporting_evidence=[ref],
        evidence_refs=[ref],
        counter_evidence=[],
        recommended_next_steps=["人工复核电池循环次数和内阻。"],
        drone_id="UAV-001",
        generated_by_skill="fault-diagnosis",
        skill_version="1.0.0",
    )
    recommendation = MaintenanceRecommendation(
        recommendation_id="MAINT-001",
        component="battery",
        action="飞行前更换电池并检查电池健康。",
        priority=MaintenancePriority.BEFORE_NEXT_FLIGHT,
        reason="诊断显示电池风险较高。",
        evidence_refs=[ref],
        required_approval="maintenance_lead",
        estimated_effort="30 分钟",
        drone_id="UAV-001",
        generated_by_skill="maintenance-advisor",
        skill_version="1.0.0",
    )

    assert anomaly.human_review_required is True
    assert fault.human_review_required is True
    assert fault.evidence_refs[0].rule_id == "BATTERY_LOW_SOC"
    assert recommendation.human_review_required is True
    assert recommendation.evidence_refs[0].rule_id == "BATTERY_LOW_SOC"


def test_skill_run_audit_records_traceability() -> None:
    audit = SkillRunAudit(
        run_id="RUN-001",
        skill_name="flight-log-analysis",
        skill_version="1.0.0",
        input_refs=["data/sample_logs/example_flight.csv"],
        tools_called=["parse_flight_log", "detect_anomalies"],
        rules_triggered=["BATTERY_LOW_SOC"],
        output_refs=["data/sample_reports/flight_summary.json"],
        human_review_required=True,
        reviewer=None,
        status="success",
    )

    assert audit.created_at.tzinfo is not None
    assert audit.status == "success"


def test_preflight_check_result_carries_items_and_evidence() -> None:
    ref = EvidenceRef(
        source_type="battery",
        source_id="BAT-001",
        field="soc_pct",
        measured_value=18,
        threshold=25,
        rule_id="BATTERY_SOC_BLOCKING",
        description="电池 SOC 低于最低阈值。",
    )
    item = PreflightCheckItem(
        item="battery_soc",
        severity=Severity.HIGH,
        reason="电池 SOC 低于最低阈值。",
        measured_value=18,
        threshold=25,
        rule_id="BATTERY_SOC_BLOCKING",
        evidence_refs=[ref],
        recommendation="更换或充电后重新执行飞行前检查。",
    )
    result = PreflightCheckResult(
        status="NO_GO",
        blocking_items=[item],
        warnings=[],
        evidence_refs=[ref],
        human_review_required=True,
        drone_id="UAV-001",
        generated_by_skill="preflight-check",
        skill_version="1.0.0",
    )

    assert result.blocking_items[0].evidence_refs[0].rule_id == "BATTERY_SOC_BLOCKING"
    assert result.human_review_required is True

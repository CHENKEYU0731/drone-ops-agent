from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MaintenancePriority(str, Enum):
    IMMEDIATE_GROUNDING = "IMMEDIATE_GROUNDING"
    BEFORE_NEXT_FLIGHT = "BEFORE_NEXT_FLIGHT"
    POST_FLIGHT_INSPECTION = "POST_FLIGHT_INSPECTION"
    SCHEDULED_MAINTENANCE = "SCHEDULED_MAINTENANCE"
    MONITOR = "MONITOR"


class ReviewableOutput(BaseModel):
    id: str = Field(default_factory=lambda: new_id("OUT"))
    timestamp: datetime = Field(default_factory=utc_now)
    drone_id: str | None = None
    human_review_required: bool = True
    generated_by_skill: str
    skill_version: str

    model_config = ConfigDict(use_enum_values=False)


class EvidenceRef(BaseModel):
    source_type: str
    source_id: str
    timestamp: datetime | None = None
    field: str
    measured_value: float | int | str
    threshold: float | int | str
    rule_id: str
    description: str


class DroneAsset(BaseModel):
    drone_id: str
    model: str
    serial_number: str
    firmware_version: str
    total_flight_hours: float = Field(ge=0)
    battery_ids: list[str] = Field(default_factory=list)
    maintenance_history: list[str] = Field(default_factory=list)
    operational_status: str = "active"
    open_maintenance_items: list[dict[str, Any]] = Field(default_factory=list)


class BatteryAsset(BaseModel):
    battery_id: str
    chemistry: str = "LiPo"
    nominal_voltage_v: float = Field(gt=0)
    cycle_count: int = Field(ge=0)
    health_pct: float = Field(ge=0, le=100)
    soc_pct: float = Field(default=100, ge=0, le=100)
    voltage_v: float | None = None
    temperature_c: float | None = None


class MissionPlan(BaseModel):
    mission_id: str
    drone_id: str
    planned_start: datetime
    planned_end: datetime
    expected_modes: list[str]
    max_planned_altitude_m: float = Field(ge=0)
    return_to_home_altitude_m: float | None = Field(default=None, ge=0)
    planned_distance_km: float | None = Field(default=None, ge=0)
    estimated_flight_time_min: float | None = Field(default=None, ge=0)
    required_battery_reserve_pct: float | None = Field(default=None, ge=0, le=100)


class PreflightObservation(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("PFO"))
    checklist_item: str
    observed_value: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class PreflightCheckItem(BaseModel):
    item: str
    severity: Severity
    reason: str
    measured_value: float | int | str | None = None
    threshold: float | int | str | None = None
    rule_id: str
    evidence_refs: list[EvidenceRef]
    recommendation: str


class PreflightCheckResult(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("PFR"))
    status: str
    observations: list[PreflightObservation] = Field(default_factory=list)
    blocking_items: list[PreflightCheckItem] = Field(default_factory=list)
    warnings: list[PreflightCheckItem] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class TelemetrySnapshot(BaseModel):
    timestamp: datetime
    drone_id: str
    altitude_m: float
    battery_voltage_v: float
    battery_soc_pct: float = Field(ge=0, le=100)
    gps_satellites: int = Field(ge=0)
    gps_hdop: float = Field(ge=0)
    link_quality_pct: float = Field(ge=0, le=100)


class FlightLogRecord(BaseModel):
    timestamp: datetime
    flight_mode: str
    altitude_m: float
    battery_voltage_v: float
    battery_current_a: float
    battery_soc_pct: float = Field(ge=0, le=100)
    gps_satellites: int = Field(ge=0)
    gps_hdop: float = Field(ge=0)
    vibration_x: float
    vibration_y: float
    vibration_z: float
    motor_1_output: float = Field(ge=0, le=100)
    motor_2_output: float = Field(ge=0, le=100)
    motor_3_output: float = Field(ge=0, le=100)
    motor_4_output: float = Field(ge=0, le=100)
    link_quality_pct: float = Field(ge=0, le=100)
    temperature_c: float


class FlightLogSummary(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("SUM"))
    source_log_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    record_count: int
    min_battery_voltage_v: float
    max_battery_current_a: float
    min_battery_soc_pct: float
    gps_summary: dict[str, Any]
    vibration_summary: dict[str, Any]
    motor_imbalance_summary: dict[str, Any]
    link_quality_summary: dict[str, Any]
    flight_mode_timeline: list[dict[str, Any]]
    anomaly_count: int = 0
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class AnomalyEvent(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("ANOMOUT"))
    anomaly_id: str
    type: str
    severity: Severity
    timestamp: datetime
    end_timestamp: datetime | None = None
    evidence_refs: list[EvidenceRef]
    human_readable_summary: str
    rule_id: str
    measured_value: float | int | str
    threshold: float | int | str


class FaultHypothesis(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("FAULTOUT"))
    fault_id: str
    fault_name: str
    confidence: float = Field(ge=0, le=1)
    severity: Severity
    evidence_refs: list[EvidenceRef]
    supporting_evidence: list[EvidenceRef]
    counter_evidence: list[EvidenceRef] = Field(default_factory=list)
    recommended_next_steps: list[str]


class MaintenanceRecommendation(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("MAINTOUT"))
    recommendation_id: str
    component: str
    action: str
    priority: MaintenancePriority
    reason: str
    evidence_refs: list[EvidenceRef]
    required_approval: str
    estimated_effort: str


class SimulationScenario(BaseModel):
    scenario_id: str
    drone_id: str
    description: str
    input_refs: list[str] = Field(default_factory=list)


class SimulationRun(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("SIM"))
    scenario_id: str
    status: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    result_summary: str


class OpsReport(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("RPT"))
    report_path: str
    summary_ref: str
    diagnosis_ref: str
    maintenance_ref: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class SkillRunAudit(BaseModel):
    run_id: str = Field(default_factory=lambda: new_id("RUN"))
    skill_name: str
    skill_version: str
    input_refs: list[str]
    tools_called: list[str]
    rules_triggered: list[str]
    output_refs: list[str]
    human_review_required: bool
    reviewer: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    status: str

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


class FleetRiskLevel(str, Enum):
    PASS = "PASS"
    LOW = "LOW"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvalStatus(str, Enum):
    PASS = "PASS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FAIL = "FAIL"
    INVALID_INPUT = "INVALID_INPUT"


class RulePackScope(str, Enum):
    PREFLIGHT = "PREFLIGHT"
    MONITORING = "MONITORING"
    SIMULATION = "SIMULATION"
    REPORT_VALIDATION = "REPORT_VALIDATION"
    WORK_ORDER = "WORK_ORDER"
    FLEET_HEALTH = "FLEET_HEALTH"
    MIXED = "MIXED"


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


class FleetAsset(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("FLEET"))
    fleet_id: str
    name: str
    asset_ids: list[str]
    source_refs: list[str] = Field(default_factory=list)

    @property
    def asset_count(self) -> int:
        return len(self.asset_ids)


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
    flight_mode: str = "UNKNOWN"
    altitude_m: float
    vertical_speed_mps: float = 0
    ground_speed_mps: float = 0
    battery_voltage_v: float
    battery_current_a: float = 0
    battery_soc_pct: float = Field(ge=0, le=100)
    gps_satellites: int = Field(ge=0)
    gps_hdop: float = Field(ge=0)
    vibration_x: float = 0
    vibration_y: float = 0
    vibration_z: float = 0
    motor_1_output: float = Field(default=0, ge=0, le=100)
    motor_2_output: float = Field(default=0, ge=0, le=100)
    motor_3_output: float = Field(default=0, ge=0, le=100)
    motor_4_output: float = Field(default=0, ge=0, le=100)
    link_quality_pct: float = Field(ge=0, le=100)
    temperature_c: float = 0
    ekf_variance: float = Field(default=0, ge=0)
    failsafe_active: bool = False


class MonitoringEvent(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("MON"))
    timestamp: datetime
    event_type: str
    severity: Severity
    message: str
    measured_value: float | int | str
    threshold: float | int | str
    rule_id: str
    evidence_refs: list[EvidenceRef]


class MonitoringSummary(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("MONSUM"))
    source_refs: list[str]
    event_count: int
    highest_severity: Severity
    monitored_duration_s: int
    samples_processed: int


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


class FleetHealthFinding(BaseModel):
    finding_id: str
    category: str
    risk_level: FleetRiskLevel
    affected_assets: list[str] = Field(default_factory=list)
    affected_flights: list[str] = Field(default_factory=list)
    summary: str
    evidence_refs: list[EvidenceRef]
    recommended_action: str
    human_review_required: bool = True


class FleetHealthSummary(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("FLEETSUM"))
    fleet_id: str
    window_start: datetime
    window_end: datetime
    asset_count: int = Field(ge=0)
    flight_count: int = Field(ge=0)
    highest_risk: FleetRiskLevel
    risk_rankings: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[FleetHealthFinding] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if self.window_end < self.window_start:
            raise ValueError("FleetHealthSummary.window_end must be greater than or equal to window_start")
        self.source_refs = sorted(self.source_refs)


class RulePackRule(BaseModel):
    rule_id: str
    version: str
    scope: RulePackScope
    description: str
    severity: str
    inputs: list[str] = Field(default_factory=list)
    thresholds: dict[str, Any] = Field(default_factory=dict)
    evidence_fields: list[str] = Field(default_factory=list)
    human_review_required: bool = True


class RulePack(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("RULEPACK"))
    pack_id: str
    name: str
    version: str
    scope: RulePackScope
    rules: list[RulePackRule] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    safety_boundary: dict[str, bool] = Field(default_factory=dict)
    generated_by_skill: str = "rule-pack-management"
    skill_version: str = "1.3.0"

    @property
    def rule_count(self) -> int:
        return len(self.rules)

    def model_post_init(self, __context: Any) -> None:
        rule_ids = [rule.rule_id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("RulePack contains duplicate rule_id values")
        self.rules = sorted(self.rules, key=lambda rule: rule.rule_id)
        self.source_refs = sorted(self.source_refs)


class WorkOrderDraft(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("WOD"))
    work_order_id: str
    asset_id: str
    component: str
    priority: MaintenancePriority
    action: str
    reason: str
    evidence_refs: list[EvidenceRef]
    required_approval: str
    estimated_effort: str
    reviewer: str | None = None
    status: str = "DRAFT"
    source_recommendation_id: str


class EvalMetric(BaseModel):
    metric_id: str
    name: str
    description: str
    weight: float = Field(gt=0, le=1)
    pass_threshold: float = Field(ge=0, le=1)
    review_threshold: float = Field(ge=0, le=1)
    required_evidence_refs: list[str] = Field(default_factory=list)


class EvalExpectedOutput(BaseModel):
    expected_status: EvalStatus
    required_diagnosis_ids: list[str] = Field(default_factory=list)
    required_recommendation_ids: list[str] = Field(default_factory=list)
    required_report_sections: list[str] = Field(default_factory=list)
    required_evidence_refs: list[str] = Field(default_factory=list)


class EvalCase(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("EVALCASE"))
    case_id: str
    title: str
    input_refs: dict[str, str]
    metrics: list[EvalMetric]
    expected_output: EvalExpectedOutput
    safety_boundary: dict[str, bool] = Field(default_factory=dict)
    generated_by_skill: str = "diagnosis-report-evaluation"
    skill_version: str = "1.4.0"

    def model_post_init(self, __context: Any) -> None:
        metric_ids = [metric.metric_id for metric in self.metrics]
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("EvalCase contains duplicate metric_id values")
        self.metrics = sorted(self.metrics, key=lambda metric: metric.metric_id)
        self.input_refs = dict(sorted(self.input_refs.items()))


class EvalResult(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("EVAL"))
    case_id: str
    status: EvalStatus
    score: float = Field(ge=0, le=1)
    metric_results: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    generated_by_skill: str = "diagnosis-report-evaluation"
    skill_version: str = "1.4.0"

    def model_post_init(self, __context: Any) -> None:
        self.metric_results = sorted(
            self.metric_results,
            key=lambda item: (str(item.get("metric_id", "")), str(item.get("status", ""))),
        )
        self.findings = sorted(
            self.findings,
            key=lambda item: (str(item.get("metric_id", "")), str(item.get("code", "")), str(item.get("message", ""))),
        )
        self.output_refs = sorted(self.output_refs)


class WorkspaceProject(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("WORKSPACE"))
    project_id: str
    name: str
    root_ref: str
    asset_refs: list[str] = Field(default_factory=list)
    report_bundle_refs: list[str] = Field(default_factory=list)
    reviewer_roles: list[str] = Field(default_factory=list)
    retention_policy: dict[str, Any] = Field(default_factory=dict)
    safety_boundary: dict[str, bool] = Field(default_factory=dict)
    generated_by_skill: str = "platform-readiness"
    skill_version: str = "1.5.0"

    def model_post_init(self, __context: Any) -> None:
        self.asset_refs = sorted(self.asset_refs)
        self.report_bundle_refs = sorted(self.report_bundle_refs)
        self.reviewer_roles = sorted(self.reviewer_roles)
        self.retention_policy = dict(sorted(self.retention_policy.items()))


class ReportBundleManifest(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("BUNDLE"))
    bundle_id: str
    workspace_project_id: str
    source_report_dir: str
    file_refs: list[str] = Field(default_factory=list)
    manifest_hash: str
    export_format: str = "directory-json"
    safety_boundary: dict[str, bool] = Field(default_factory=dict)
    generated_by_skill: str = "platform-readiness"
    skill_version: str = "1.5.0"

    @property
    def file_count(self) -> int:
        return len(self.file_refs)

    def model_post_init(self, __context: Any) -> None:
        self.file_refs = sorted(self.file_refs)


class ReviewerApproval(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("APPROVAL"))
    approval_id: str
    subject_ref: str
    reviewer_id: str
    reviewer_role: str
    decision: str
    rationale: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    generated_by_skill: str = "platform-readiness"
    skill_version: str = "1.5.0"


class OfflineAdapterContract(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("ADAPTER"))
    adapter_id: str
    adapter_type: str
    direction: str
    allowed_operations: list[str] = Field(default_factory=list)
    prohibited_operations: list[str] = Field(default_factory=list)
    safety_boundary: dict[str, bool] = Field(default_factory=dict)
    generated_by_skill: str = "platform-readiness"
    skill_version: str = "1.5.0"

    def model_post_init(self, __context: Any) -> None:
        self.allowed_operations = sorted(self.allowed_operations)
        self.prohibited_operations = sorted(self.prohibited_operations)


class PlatformReadinessChecklist(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("PLATFORMCHECK"))
    checklist_id: str
    title: str
    checks: list[dict[str, Any]] = Field(default_factory=list)
    safety_boundary: dict[str, bool] = Field(default_factory=dict)
    generated_by_skill: str = "platform-readiness"
    skill_version: str = "1.5.0"

    def model_post_init(self, __context: Any) -> None:
        self.checks = sorted(self.checks, key=lambda item: str(item.get("check_id", "")))


class DatasetCase(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("DATASETCASE"))
    case_id: str
    case_type: str
    title: str
    source_refs: list[str] = Field(default_factory=list)
    sanitized_status: str
    capabilities: list[str] = Field(default_factory=list)
    recommended_commands: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    safety_boundary: dict[str, bool] = Field(default_factory=dict)
    generated_by_skill: str = "dataset-registry"
    skill_version: str = "1.6.0"

    def model_post_init(self, __context: Any) -> None:
        self.source_refs = sorted(self.source_refs)
        self.capabilities = sorted(self.capabilities)
        self.expected_outputs = sorted(self.expected_outputs)


class DatasetRegistry(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("DATASETREG"))
    registry_id: str
    version: str
    cases: list[DatasetCase] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    safety_boundary: dict[str, bool] = Field(default_factory=dict)
    generated_by_skill: str = "dataset-registry"
    skill_version: str = "1.6.0"

    @property
    def case_count(self) -> int:
        return len(self.cases)

    def model_post_init(self, __context: Any) -> None:
        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("DatasetRegistry contains duplicate case_id values")
        self.cases = sorted(self.cases, key=lambda case: case.case_id)
        self.source_refs = sorted(self.source_refs)


class SimulationScenario(BaseModel):
    scenario_id: str
    drone_id: str
    description: str
    input_refs: list[str] = Field(default_factory=list)


class SimulationRuleResult(BaseModel):
    rule_id: str
    status: str
    field: str
    measured_value: float | int | str
    threshold: float | int | str
    message: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    human_review_required: bool = True


class SimulationRun(ReviewableOutput):
    id: str = Field(default_factory=lambda: new_id("SIM"))
    scenario_id: str
    status: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    rule_results: list[SimulationRuleResult] = Field(default_factory=list)
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
    metadata: dict[str, Any] = Field(default_factory=dict)

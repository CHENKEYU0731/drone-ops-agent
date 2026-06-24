from __future__ import annotations

from packages.drone_schemas import (
    DroneAsset,
    FaultHypothesis,
    FlightLogSummary,
    MaintenancePriority,
    MaintenanceRecommendation,
    Severity,
)


SKILL_NAME = "maintenance-advisor"
SKILL_VERSION = "1.0.0"


ACTION_MAP = {
    "桨叶损伤或动平衡异常": ("propulsion", "飞行前检查并更换可疑桨叶，完成动平衡复核。", "45 分钟"),
    "电机性能衰退": ("motor", "检查电机轴承、温升和输出一致性，必要时更换电机。", "60 分钟"),
    "电池健康衰退": ("battery", "更换本次任务电池，检测循环次数、内阻和单体压差。", "30 分钟"),
    "GPS 接收问题": ("navigation", "检查 GPS 天线安装、遮挡和电磁干扰，复测定位质量。", "30 分钟"),
    "传感器振动问题": ("sensor", "检查 IMU 固定、减震结构和机体松动点。", "40 分钟"),
    "通信链路问题": ("radio_link", "检查遥控链路、天线方向、接收机连接和干扰源。", "35 分钟"),
    "热异常问题": ("thermal", "检查电机、电调和电池温度来源，清理散热路径。", "45 分钟"),
}


def generate_maintenance_recommendations(
    hypotheses: list[FaultHypothesis],
    asset: DroneAsset,
    summary: FlightLogSummary,
) -> list[MaintenanceRecommendation]:
    recommendations: list[MaintenanceRecommendation] = []
    for index, hypothesis in enumerate(hypotheses, start=1):
        component, action, effort = ACTION_MAP.get(
            hypothesis.fault_name,
            ("airframe", "安排人工复核该故障假设并记录检查结果。", "30 分钟"),
        )
        priority = _priority_for(hypothesis)
        recommendations.append(
            MaintenanceRecommendation(
                recommendation_id=f"MAINT-{index:03d}",
                component=component,
                action=action,
                priority=priority,
                reason=f"故障假设“{hypothesis.fault_name}”置信度 {hypothesis.confidence:.2f}，需要人工确认。",
                evidence_refs=hypothesis.supporting_evidence,
                required_approval="maintenance_lead",
                estimated_effort=effort,
                drone_id=asset.drone_id or summary.drone_id,
                generated_by_skill=SKILL_NAME,
                skill_version=SKILL_VERSION,
            )
        )
    if not recommendations:
        recommendations.append(
            MaintenanceRecommendation(
                recommendation_id="MAINT-001",
                component="fleet",
                action="继续监控下一次飞行日志，保持常规维护计划。",
                priority=MaintenancePriority.MONITOR,
                reason="当前没有足够证据支持具体故障假设。",
                evidence_refs=summary.evidence_refs,
                required_approval="ops_engineer",
                estimated_effort="10 分钟",
                drone_id=asset.drone_id or summary.drone_id,
                generated_by_skill=SKILL_NAME,
                skill_version=SKILL_VERSION,
            )
        )
    return recommendations


def _priority_for(hypothesis: FaultHypothesis) -> MaintenancePriority:
    if hypothesis.severity in {Severity.CRITICAL, Severity.HIGH} and hypothesis.confidence >= 0.85:
        return MaintenancePriority.IMMEDIATE_GROUNDING
    if hypothesis.severity == Severity.HIGH and hypothesis.confidence >= 0.35:
        return MaintenancePriority.BEFORE_NEXT_FLIGHT
    if hypothesis.confidence >= 0.4:
        return MaintenancePriority.POST_FLIGHT_INSPECTION
    if hypothesis.confidence >= 0.25:
        return MaintenancePriority.SCHEDULED_MAINTENANCE
    return MaintenancePriority.MONITOR

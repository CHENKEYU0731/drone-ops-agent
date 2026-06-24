from __future__ import annotations

from collections import defaultdict

from packages.drone_schemas import (
    AnomalyEvent,
    DroneAsset,
    EvidenceRef,
    FaultHypothesis,
    FlightLogSummary,
    Severity,
)


SKILL_NAME = "fault-diagnosis"
SKILL_VERSION = "1.0.0"


RULE_MAP = {
    "HIGH_VIBRATION": [
        ("PROP_BALANCE", "桨叶损伤或动平衡异常", 0.34, Severity.HIGH, "检查桨叶缺口、裂纹和安装方向。"),
        ("SENSOR_VIBRATION", "传感器振动问题", 0.24, Severity.MEDIUM, "检查 IMU 固定和减震结构。"),
    ],
    "MOTOR_OUTPUT_IMBALANCE": [
        ("MOTOR_DEGRADATION", "电机性能衰退", 0.34, Severity.HIGH, "检查电机轴承、桨夹和 ESC 输出一致性。"),
        ("PROP_BALANCE", "桨叶损伤或动平衡异常", 0.18, Severity.HIGH, "复核对应电机桨叶平衡。"),
    ],
    "LOW_BATTERY_SOC": [
        ("BATTERY_HEALTH", "电池健康衰退", 0.28, Severity.HIGH, "检查电池循环次数、内阻和单体压差。"),
    ],
    "BATTERY_VOLTAGE_DROP": [
        ("BATTERY_HEALTH", "电池健康衰退", 0.28, Severity.HIGH, "复核负载下电压跌落和电池内阻。"),
    ],
    "HIGH_CURRENT": [
        ("BATTERY_HEALTH", "电池健康衰退", 0.14, Severity.HIGH, "检查高负载电流与电池状态是否匹配。"),
        ("MOTOR_DEGRADATION", "电机性能衰退", 0.14, Severity.HIGH, "检查是否存在机械阻力导致电流升高。"),
    ],
    "GPS_QUALITY_DEGRADED": [
        ("GPS_RECEPTION", "GPS 接收问题", 0.2, Severity.MEDIUM, "检查天线遮挡、安装位置和周边电磁环境。"),
    ],
    "HIGH_HDOP": [
        ("GPS_RECEPTION", "GPS 接收问题", 0.2, Severity.MEDIUM, "复核 HDOP 异常时段和卫星分布。"),
    ],
    "LOW_GPS_SATELLITES": [
        ("GPS_RECEPTION", "GPS 接收问题", 0.2, Severity.MEDIUM, "检查卫星数量下降原因。"),
    ],
    "LOW_LINK_QUALITY": [
        ("LINK_QUALITY", "通信链路问题", 0.36, Severity.HIGH, "检查遥控链路、天线方向和干扰源。"),
    ],
    "HIGH_TEMPERATURE": [
        ("THERMAL_ANOMALY", "热异常问题", 0.36, Severity.HIGH, "检查散热路径、电机/电调温度和环境温度。"),
    ],
    "UNEXPECTED_FLIGHT_MODE": [
        ("LINK_QUALITY", "通信链路问题", 0.16, Severity.HIGH, "复核 failsafe 触发条件和链路记录。"),
        ("GPS_RECEPTION", "GPS 接收问题", 0.12, Severity.MEDIUM, "复核模式切换时定位质量。"),
    ],
}


def generate_fault_hypotheses(
    summary: FlightLogSummary,
    anomalies: list[AnomalyEvent],
    asset: DroneAsset,
) -> list[FaultHypothesis]:
    scores: dict[str, float] = defaultdict(float)
    names: dict[str, str] = {}
    severities: dict[str, Severity] = {}
    next_steps: dict[str, list[str]] = defaultdict(list)
    evidence: dict[str, list[EvidenceRef]] = defaultdict(list)

    for anomaly in anomalies:
        for fault_id, name, score, severity, step in RULE_MAP.get(anomaly.type, []):
            scores[fault_id] += score
            names[fault_id] = name
            severities[fault_id] = _max_severity(severities.get(fault_id), severity)
            next_steps[fault_id].append(step)
            evidence[fault_id].extend(anomaly.evidence_refs)

    hypotheses: list[FaultHypothesis] = []
    for index, fault_id in enumerate(sorted(scores, key=lambda item: scores[item], reverse=True), start=1):
        unique_steps = list(dict.fromkeys(next_steps[fault_id]))
        unique_evidence = _unique_evidence(evidence[fault_id])
        confidence = min(round(scores[fault_id], 2), 0.95)
        hypotheses.append(
            FaultHypothesis(
                fault_id=f"FAULT-{index:03d}",
                fault_name=names[fault_id],
                confidence=confidence,
                severity=severities[fault_id],
                evidence_refs=unique_evidence,
                supporting_evidence=unique_evidence,
                counter_evidence=[],
                recommended_next_steps=unique_steps,
                drone_id=asset.drone_id or summary.drone_id,
                generated_by_skill=SKILL_NAME,
                skill_version=SKILL_VERSION,
            )
        )
    return hypotheses


def _max_severity(left: Severity | None, right: Severity) -> Severity:
    order = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
    if left is None:
        return right
    return order[max(order.index(left), order.index(right))]


def _unique_evidence(refs: list[EvidenceRef]) -> list[EvidenceRef]:
    result: list[EvidenceRef] = []
    seen: set[tuple[str, str, str]] = set()
    for ref in refs:
        key = (ref.source_id, ref.field, ref.rule_id)
        if key not in seen:
            result.append(ref)
            seen.add(key)
    return result

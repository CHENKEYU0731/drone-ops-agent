from __future__ import annotations

from packages.drone_schemas import (
    AnomalyEvent,
    DroneAsset,
    FaultHypothesis,
    FlightLogSummary,
    MaintenanceRecommendation,
    SkillRunAudit,
)


SKILL_NAME = "ops-report-generation"
SKILL_VERSION = "1.0.0"


def render_ops_report(
    summary: FlightLogSummary,
    anomalies: list[AnomalyEvent],
    diagnosis: list[FaultHypothesis],
    maintenance: list[MaintenanceRecommendation],
    asset: DroneAsset,
    audits: list[SkillRunAudit],
) -> str:
    lines: list[str] = [
        "# 无人机运维报告",
        "",
        "## 1. 执行摘要",
        f"- 无人机：`{asset.drone_id}`（{asset.model}）",
        f"- 飞行时长：{summary.duration_seconds} 秒，日志记录数：{summary.record_count}",
        f"- 检测异常：{len(anomalies)} 条；故障假设：{len(diagnosis)} 条；维护建议：{len(maintenance)} 条。",
        "- 本报告仅用于运维支持和决策辅助，不包含任何真实飞控命令。",
        "",
        "## 2. 飞行概况",
        f"- 开始时间：{summary.start_time.isoformat()}",
        f"- 结束时间：{summary.end_time.isoformat()}",
        f"- 来源日志：`{summary.source_log_id}`",
        "- 飞行模式时间线：",
    ]
    for item in summary.flight_mode_timeline:
        lines.append(f"  - {item['timestamp']}：{item['flight_mode']}")

    lines.extend(
        [
            "",
            "## 3. 资产概况",
            f"- 机型：{asset.model}",
            f"- 序列号：{asset.serial_number}",
            f"- 固件版本：{asset.firmware_version}",
            f"- 累计飞行小时：{asset.total_flight_hours}",
            f"- 关联电池：{', '.join(asset.battery_ids) if asset.battery_ids else '未记录'}",
            "",
            "## 4. 关键指标",
            f"- 最低电压：{summary.min_battery_voltage_v} V",
            f"- 最大电流：{summary.max_battery_current_a} A",
            f"- 最低 SOC：{summary.min_battery_soc_pct}%",
            f"- 最低 GPS 卫星数：{summary.gps_summary['min_satellites']}",
            f"- 最大 HDOP：{summary.gps_summary['max_hdop']}",
            f"- 最大振动幅值：{summary.vibration_summary['max_magnitude']}",
            f"- 最大电机输出差：{summary.motor_imbalance_summary['max_spread']}",
            f"- 最低链路质量：{summary.link_quality_summary['min_link_quality_pct']}%",
            "",
            "## 5. 异常事件时间线",
        ]
    )
    for anomaly in anomalies:
        lines.append(
            f"- `{anomaly.timestamp.isoformat()}` `{anomaly.type}` "
            f"{anomaly.severity.value}：{anomaly.human_readable_summary}"
        )
        lines.append(f"  - 证据：{_brief_refs(anomaly.evidence_refs)}")
    if not anomalies:
        lines.append("- 未检测到异常事件。")

    lines.extend(["", "## 6. 故障假设"])
    for hypothesis in diagnosis:
        lines.append(
            f"- `{hypothesis.fault_id}` {hypothesis.fault_name}："
            f"置信度 {hypothesis.confidence:.2f}，严重级别 {hypothesis.severity.value}。"
        )
        for step in hypothesis.recommended_next_steps:
            lines.append(f"  - 下一步：{step}")
        lines.append(f"  - 证据：{_brief_refs(hypothesis.evidence_refs)}")
    if not diagnosis:
        lines.append("- 没有足够证据生成故障假设。")

    lines.extend(["", "## 7. 维护建议"])
    for recommendation in maintenance:
        lines.append(
            f"- `{recommendation.recommendation_id}` [{recommendation.priority.value}] "
            f"{recommendation.component}：{recommendation.action}"
        )
        lines.append(f"  - 原因：{recommendation.reason}")
        lines.append(f"  - 审批：{recommendation.required_approval}；预计工作量：{recommendation.estimated_effort}")
        lines.append(f"  - 证据：{_brief_refs(recommendation.evidence_refs)}")
    if not maintenance:
        lines.append("- 暂无维护建议。")

    lines.extend(
        [
            "",
            "## 8. 安全说明",
            "- 系统只提供运维分析、故障假设和维护建议。",
            "- 系统不得解锁电机、启动电机、执行起飞、降落、返航、航线飞行、固件上传或飞控参数修改。",
            "",
            "## 9. 人工复核要求",
            "- 所有诊断结论和维护建议都必须由具备资质的运维或维修负责人复核。",
            "- 涉及飞行安全、维护安全或飞控参数的任何操作必须人工批准后在线下执行。",
            "",
            "## 10. 审计记录",
        ]
    )
    if audits:
        for audit in audits:
            lines.append(
                f"- `{audit.run_id}` {audit.skill_name}@{audit.skill_version}："
                f"{audit.status}，human_review_required={audit.human_review_required}"
            )
    else:
        lines.append("- 本次单元渲染未传入审计记录。")

    lines.extend(["", "## 11. 证据引用附录"])
    evidence_lines = _evidence_lines(anomalies, diagnosis, maintenance)
    lines.extend(evidence_lines or ["- 无证据引用。"])
    lines.append("")
    return "\n".join(lines)


def _evidence_lines(
    anomalies: list[AnomalyEvent],
    diagnosis: list[FaultHypothesis],
    maintenance: list[MaintenanceRecommendation],
) -> list[str]:
    refs = []
    for anomaly in anomalies:
        refs.extend(anomaly.evidence_refs)
    for hypothesis in diagnosis:
        refs.extend(hypothesis.supporting_evidence)
    for recommendation in maintenance:
        refs.extend(recommendation.evidence_refs)

    lines: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for ref in refs:
        key = (ref.source_id, ref.field, ref.rule_id)
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"- `{ref.rule_id}` {ref.source_type}:{ref.source_id} "
            f"字段 `{ref.field}`={ref.measured_value}，阈值 `{ref.threshold}`。{ref.description}"
        )
    return lines


def _brief_refs(refs) -> str:
    if not refs:
        return "无"
    parts = [f"{ref.rule_id}@{ref.source_id}" for ref in refs[:3]]
    if len(refs) > 3:
        parts.append(f"另 {len(refs) - 3} 条")
    return "；".join(parts)

from __future__ import annotations

from packages.drone_schemas import (
    AnomalyEvent,
    DroneAsset,
    FaultHypothesis,
    FlightLogSummary,
    MaintenanceRecommendation,
    SimulationRun,
    SkillRunAudit,
    WorkOrderDraft,
)
from packages.work_orders.validation import WorkOrderValidationResult


SKILL_NAME = "ops-report-generation"
SKILL_VERSION = "1.0.0"


def render_ops_report(
    summary: FlightLogSummary,
    anomalies: list[AnomalyEvent],
    diagnosis: list[FaultHypothesis],
    maintenance: list[MaintenanceRecommendation],
    asset: DroneAsset,
    audits: list[SkillRunAudit],
    simulation: SimulationRun | None = None,
    work_orders: list[WorkOrderDraft] | None = None,
    work_order_validation: WorkOrderValidationResult | None = None,
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

    if simulation is not None:
        lines.extend(_simulation_section(simulation))

    lines.extend(_audit_summary_section(audits))
    lines.extend(_parser_metadata_section(audits))
    lines.extend(_human_review_checklist(anomalies, diagnosis, maintenance, simulation))
    if work_orders is not None:
        lines.extend(_work_order_section(work_orders))
    if work_order_validation is not None:
        lines.extend(_work_order_validation_section(work_order_validation))

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
    evidence_lines = _evidence_lines(anomalies, diagnosis, maintenance, simulation)
    lines.extend(evidence_lines or ["- 无证据引用。"])
    lines.append("")
    return "\n".join(lines)


def _simulation_section(simulation: SimulationRun) -> list[str]:
    lines = [
        "",
        "## 7.5 仿真验证",
        f"- 场景 ID：`{simulation.scenario_id}`",
        f"- 仿真状态：`{simulation.status}`",
        f"- 人工复核：`{str(simulation.human_review_required).lower()}`",
        "- 说明：该结果只来自离线/mock 仿真结果导入，不代表真实飞行授权。",
        "- 规则命中详情：",
    ]
    for rule in simulation.rule_results[:8]:
        lines.append(
            f"  - `{rule.rule_id}` `{rule.status}`：{rule.field}={rule.measured_value}，阈值 `{rule.threshold}`"
        )
        lines.append(f"    - 证据：{_brief_refs(rule.evidence_refs)}")
    if len(simulation.rule_results) > 8:
        lines.append(f"  - 另有 {len(simulation.rule_results) - 8} 条规则结果未在摘要中展开。")
    lines.append(f"- 仿真证据：{_brief_refs(simulation.evidence_refs)}")
    return lines


def _work_order_section(work_orders: list[WorkOrderDraft]) -> list[str]:
    lines = [
        "",
        "## 7.9 工单草稿",
        "- 说明：本章节只展示离线工单草稿，不会自动派单，不会连接真实 CMMS/Jira/飞书/企业微信，也不会执行维护动作。",
    ]
    if not work_orders:
        lines.append("- 暂无工单草稿。")
        return lines
    for draft in work_orders:
        lines.extend(
            [
                f"- `{draft.work_order_id}` `{draft.status}` [{draft.priority.value}] {draft.component}：{draft.action}",
                f"  - 来源维护建议：`{draft.source_recommendation_id}`",
                f"  - 审批要求：{draft.required_approval}；预计工作量：{draft.estimated_effort}",
                f"  - 人工复核：`{str(draft.human_review_required).lower()}`",
                f"  - 证据：{_brief_refs(draft.evidence_refs)}",
            ]
        )
    return lines


def _work_order_validation_section(validation: WorkOrderValidationResult) -> list[str]:
    lines = [
        "",
        "## 7.10 工单验证",
        f"- 验证状态：`{validation.status}`",
        f"- 已验证草稿：{validation.counts.validated_drafts}",
        f"- 证据引用：{validation.counts.evidence_refs}",
        "- 说明：验证通过只表示草稿结构和证据链满足离线质量门禁，不代表真实派单或维护授权。",
    ]
    for error in validation.errors:
        lines.append(f"- 错误：{error}")
    for warning in validation.warnings:
        lines.append(f"- 警告：{warning}")
    return lines


def _audit_summary_section(audits: list[SkillRunAudit]) -> list[str]:
    lines = ["", "## 7.6 审计摘要"]
    if not audits:
        lines.append("- 本次报告未传入可汇总的审计记录。")
        return lines
    for audit in _sorted_audits(audits):
        triggered = ", ".join(audit.rules_triggered) if audit.rules_triggered else "无"
        lines.append(
            f"- `{audit.skill_name}@{audit.skill_version}`：状态 `{audit.status}`，"
            f"人工复核 `{str(audit.human_review_required).lower()}`，触发规则：{triggered}。"
        )
    return lines


def _parser_metadata_section(audits: list[SkillRunAudit]) -> list[str]:
    lines = ["", "## 7.7 日志解析元数据"]
    parser_audits = [audit for audit in _sorted_audits(audits) if _parser_metadata(audit)]
    if not parser_audits:
        lines.append("- 未找到 flight-log-analysis 解析元数据。")
        return lines
    for audit in parser_audits:
        metadata = audit.metadata
        parser_name = metadata.get("parser_name", "unknown")
        parser_version = metadata.get("parser_version", "unknown")
        lines.append(
            f"- `{audit.run_id}` 请求格式：`{metadata.get('requested_format', 'unknown')}`；"
            f"实际格式：`{metadata.get('actual_format', 'unknown')}`；"
            f"解析器：`{parser_name}@{parser_version}`。"
        )
        warnings = metadata.get("warnings") or []
        lines.append(f"  - warnings：{', '.join(str(item) for item in warnings) if warnings else '无'}")
        parser_metadata = metadata.get("parser_metadata") or {}
        lines.append(f"  - parser metadata：{_format_metadata(parser_metadata)}")
    return lines


def _human_review_checklist(
    anomalies: list[AnomalyEvent],
    diagnosis: list[FaultHypothesis],
    maintenance: list[MaintenanceRecommendation],
    simulation: SimulationRun | None = None,
) -> list[str]:
    lines = ["", "## 7.8 人工复核清单"]
    if anomalies:
        lines.append(f"- [ ] 复核异常事件证据链：{len(anomalies)} 条异常。")
    else:
        lines.append("- [ ] 确认本次报告未检测到异常事件。")
    if diagnosis:
        lines.append(f"- [ ] 复核故障假设和反证：{len(diagnosis)} 条假设。")
    else:
        lines.append("- [ ] 确认本次报告未生成故障假设。")
    if maintenance:
        lines.append(f"- [ ] 复核维护建议审批要求：{len(maintenance)} 条建议。")
    else:
        lines.append("- [ ] 确认本次报告暂无维护建议。")
    if simulation is not None:
        lines.append(f"- [ ] 复核离线仿真结论：`{simulation.status}`。")
    lines.append("- [ ] 确认本报告不代表真实飞行授权，所有安全相关动作必须在线下人工批准。")
    return lines


def _sorted_audits(audits: list[SkillRunAudit]) -> list[SkillRunAudit]:
    return sorted(audits, key=lambda audit: (audit.created_at.isoformat(), audit.skill_name, audit.run_id))


def _parser_metadata(audit: SkillRunAudit) -> bool:
    return bool(audit.metadata.get("parser_name") or audit.metadata.get("parser_metadata"))


def _format_metadata(metadata: object) -> str:
    if not isinstance(metadata, dict) or not metadata:
        return "无"
    parts: list[str] = []
    for key in sorted(metadata):
        value = metadata[key]
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value)
        elif isinstance(value, dict):
            rendered = ", ".join(f"{sub_key}={value[sub_key]}" for sub_key in sorted(value))
        else:
            rendered = str(value)
        parts.append(f"{key}={rendered}")
    return "；".join(parts)


def _evidence_lines(
    anomalies: list[AnomalyEvent],
    diagnosis: list[FaultHypothesis],
    maintenance: list[MaintenanceRecommendation],
    simulation: SimulationRun | None = None,
) -> list[str]:
    refs = []
    for anomaly in anomalies:
        refs.extend(anomaly.evidence_refs)
    for hypothesis in diagnosis:
        refs.extend(hypothesis.supporting_evidence)
    for recommendation in maintenance:
        refs.extend(recommendation.evidence_refs)
    if simulation is not None:
        refs.extend(simulation.evidence_refs)

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
        parts.append(f"另有 {len(refs) - 3} 条")
    return "；".join(parts)

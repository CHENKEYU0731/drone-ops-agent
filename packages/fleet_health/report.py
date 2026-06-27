from __future__ import annotations

from packages.drone_schemas import FleetHealthSummary


def render_fleet_health_report(summary: FleetHealthSummary) -> str:
    lines: list[str] = [
        "# 机队健康趋势报告",
        "",
        "## 1. 执行摘要",
        f"- 机队：`{summary.fleet_id}`",
        f"- 时间窗口：{summary.window_start.isoformat()} 至 {summary.window_end.isoformat()}",
        f"- 资产数量：{summary.asset_count}",
        f"- 飞行数量：{summary.flight_count}",
        f"- 最高风险：`{summary.highest_risk.value}`",
        f"- 人工复核：`{str(summary.human_review_required).lower()}`",
        "- 说明：本报告仅基于本地离线样例/脱敏 JSON 聚合，不代表真实飞行授权。",
        "",
        "## 2. 风险排名",
    ]
    if not summary.risk_rankings:
        lines.append("- 暂无风险排名。")
    for index, item in enumerate(summary.risk_rankings, start=1):
        lines.append(
            f"{index}. `{item['asset_id']}` risk_score={item['risk_score']} "
            f"risk_level=`{item['risk_level']}` flights={item['flight_count']}"
        )

    lines.extend(["", "## 3. 机队级发现"])
    if not summary.findings:
        lines.append("- 未发现机队级风险趋势。")
    for finding in summary.findings:
        lines.append(
            f"- `{finding.finding_id}` [{finding.risk_level.value}] {finding.category}：{finding.summary}"
        )
        lines.append(f"  - 受影响资产：{', '.join(finding.affected_assets)}")
        lines.append(f"  - 受影响飞行：{', '.join(finding.affected_flights)}")
        lines.append(f"  - 建议动作：{finding.recommended_action}")
        lines.append(f"  - 证据：{_brief_refs(finding.evidence_refs)}")

    lines.extend(["", "## 4. 数据来源"])
    for source in summary.source_refs:
        lines.append(f"- `{source}`")
    if not summary.source_refs:
        lines.append("- 暂无数据来源。")

    lines.extend(
        [
            "",
            "## 5. 安全边界",
            "- 本报告不连接真实无人机。",
            "- 本报告不读取实时遥测，不连接真实 fleet platform。",
            "- 本报告不执行 MAVLink command，不启动 PX4、ArduPilot、Gazebo、SITL 或外部仿真器。",
            "- 本报告不连接真实 CMMS、Jira、飞书或企业微信，不自动派单，也不执行维护动作。",
            "- 本报告不代表真实飞行授权或真实维护授权，所有结论都需要人工复核。",
            "",
        ]
    )
    return "\n".join(lines)


def _brief_refs(refs) -> str:
    if not refs:
        return "无"
    parts = [f"{ref.rule_id}@{ref.source_id}" for ref in refs[:3]]
    if len(refs) > 3:
        parts.append(f"另有 {len(refs) - 3} 条")
    return "；".join(parts)

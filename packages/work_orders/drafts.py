from __future__ import annotations

from packages.drone_schemas import DroneAsset, MaintenanceRecommendation, WorkOrderDraft


SKILL_NAME = "work-order-drafting"
SKILL_VERSION = "1.0.0"


def generate_work_order_drafts(
    recommendations: list[MaintenanceRecommendation],
    asset: DroneAsset,
) -> list[WorkOrderDraft]:
    drafts: list[WorkOrderDraft] = []
    for index, recommendation in enumerate(recommendations, start=1):
        drafts.append(
            WorkOrderDraft(
                work_order_id=f"WO-{asset.drone_id}-{index:03d}",
                asset_id=asset.drone_id,
                drone_id=asset.drone_id,
                component=recommendation.component,
                priority=recommendation.priority,
                action=recommendation.action,
                reason=recommendation.reason,
                evidence_refs=recommendation.evidence_refs,
                required_approval=recommendation.required_approval,
                estimated_effort=recommendation.estimated_effort,
                reviewer=None,
                status="DRAFT",
                source_recommendation_id=recommendation.recommendation_id,
                human_review_required=True,
                generated_by_skill=SKILL_NAME,
                skill_version=SKILL_VERSION,
            )
        )
    return drafts


def render_work_order_drafts_markdown(drafts: list[WorkOrderDraft]) -> str:
    lines = [
        "# 工单草稿",
        "",
        "本文件仅供人工复核，不会自动派单，不会连接真实 CMMS/Jira/飞书/企业微信，也不会执行任何维护动作。",
        "",
    ]
    if not drafts:
        lines.append("- 暂无工单草稿。")
        lines.append("")
        return "\n".join(lines)

    for draft in drafts:
        lines.extend(
            [
                f"## {draft.work_order_id}",
                f"- 资产：`{draft.asset_id}`",
                f"- 组件：{draft.component}",
                f"- 优先级：`{draft.priority.value}`",
                f"- 状态：`{draft.status}`",
                f"- 来源维护建议：`{draft.source_recommendation_id}`",
                f"- 动作：{draft.action}",
                f"- 原因：{draft.reason}",
                f"- 审批要求：{draft.required_approval}",
                f"- 预计工作量：{draft.estimated_effort}",
                f"- 人工复核：`{str(draft.human_review_required).lower()}`",
                f"- 证据：{_brief_refs(draft)}",
                "",
            ]
        )
    return "\n".join(lines)


def _brief_refs(draft: WorkOrderDraft) -> str:
    if not draft.evidence_refs:
        return "无"
    refs = [f"{ref.rule_id}@{ref.source_id}" for ref in draft.evidence_refs[:3]]
    if len(draft.evidence_refs) > 3:
        refs.append(f"另有 {len(draft.evidence_refs) - 3} 条")
    return "；".join(refs)

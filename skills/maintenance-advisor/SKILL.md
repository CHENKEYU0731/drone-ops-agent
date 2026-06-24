# Skill: maintenance-advisor

## Purpose

把 `FaultHypothesis` 转换为可执行但必须人工复核的 `MaintenanceRecommendation`。该 skill 由 `drone-ops diagnose` 串联触发，核心函数是 `generate_maintenance_recommendations`。

## Inputs

- `diagnosis.json`
- `DroneAsset`
- `FlightLogSummary`

## Outputs

- `maintenance_recommendations.json`
- `audit/maintenance-advisor-<run_id>.json`

## Hard Rules

- 每条维护建议必须包含 `evidence_refs`。
- 每条维护建议必须包含 `required_approval`。
- 所有维护建议必须 `human_review_required=true`。
- 建议只描述检查、复核、维护动作，不执行真实硬件控制。

## Procedure

1. 读取故障假设、资产和摘要。
2. 根据故障名称、严重级别和置信度选择维护优先级。
3. 生成 component、action、reason、estimated_effort 和 required_approval。
4. 继承故障假设证据。
5. 写出维护建议和审计记录。

## Evidence Requirements

- 维护建议的 evidence refs 必须来自对应故障假设。
- 报告中必须能从维护建议追溯到日志字段和规则。

## Audit Requirements

- rules triggered 记录维护优先级。
- output refs 指向 `maintenance_recommendations.json`。

## Test Cases

- 生成 IMMEDIATE_GROUNDING、BEFORE_NEXT_FLIGHT 和 POST_FLIGHT_INSPECTION 等优先级。
- 每条建议包含证据、审批人、人工复核和预计工作量。

## Known Limitations

- 当前不连接 CMMS 或工单系统。
- 工时估计为规则默认值。

## Future Extensions

- 连接工单系统。
- 引入备件库存和维护人员排班。

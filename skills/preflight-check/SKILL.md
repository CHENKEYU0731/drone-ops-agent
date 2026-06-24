# Skill: preflight-check

## Purpose

提供飞行前检查 skill 的结构化 skeleton。MVP 不执行真实硬件检查，只定义未来如何记录人工检查观察和结论。

## Inputs

- `DroneAsset`
- `MissionPlan`
- 人工录入的 `PreflightObservation`

## Outputs

- `PreflightCheckResult`
- audit JSON

## Hard Rules

- 不连接真实无人机。
- 不解锁电机、不启动电机、不执行任何飞行动作。
- 任何不通过项必须 `human_review_required=true`。

## Procedure

1. 读取资产和任务计划。
2. 接收人工检查观察。
3. 根据 checklist 规则生成检查结果。
4. 写出结果和审计记录。

## Evidence Requirements

- 每个不通过项必须引用人工观察或资产字段。

## Audit Requirements

- 记录 checklist 输入、输出和人工复核要求。

## Test Cases

- checklist 缺项时生成需要复核的结果。
- 所有不通过项包含 evidence refs。

## Known Limitations

- MVP 不实现可运行 CLI。

## Future Extensions

- 增加预检 CLI。
- 增加可配置 checklist。

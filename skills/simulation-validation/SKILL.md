# Skill: simulation-validation

## Purpose

提供仿真验证 skill 的结构化 skeleton。MVP 不运行 SITL，只定义未来如何把诊断和维护建议放入隔离仿真中验证。

## Inputs

- `SimulationScenario`
- `MissionPlan`
- `FaultHypothesis`
- `MaintenanceRecommendation`

## Outputs

- `SimulationRun`
- audit JSON

## Hard Rules

- 仿真必须与真实硬件隔离。
- 不向真实飞控发送命令。
- 仿真结论不能自动批准维护或飞行操作。

## Procedure

1. 读取仿真场景。
2. 验证输入引用。
3. 在隔离环境中运行或记录待运行仿真。
4. 写出仿真结果和审计记录。

## Evidence Requirements

- 仿真结果必须引用 scenario、mission、rule 或 simulation source。

## Audit Requirements

- 记录仿真输入、工具、输出和人工复核要求。

## Test Cases

- 无效场景会失败并给出清晰错误。
- 仿真结果包含 evidence refs。

## Known Limitations

- MVP 不包含 SITL 执行器。

## Future Extensions

- 增加 PX4/ArduPilot SITL。
- 增加仿真结果对比报告。

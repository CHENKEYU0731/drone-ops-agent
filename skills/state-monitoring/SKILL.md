# Skill: state-monitoring

## Purpose

提供状态监控 skill 的结构化 skeleton。MVP 不接入实时遥测，只定义未来只读监控的输入输出边界。

## Inputs

- `TelemetrySnapshot` 列表。
- `DroneAsset`。

## Outputs

- 状态摘要。
- 异常事件。
- audit JSON。

## Hard Rules

- 只读遥测，不发送控制命令。
- 不执行返航、降落、航线切换或参数写入。
- 所有安全相关告警必须要求人工复核。

## Procedure

1. 读取 telemetry snapshot。
2. 验证字段范围。
3. 应用状态规则。
4. 写出告警和审计记录。

## Evidence Requirements

- 告警必须引用 telemetry 字段、时间戳和阈值。

## Audit Requirements

- 记录输入快照、触发规则和输出告警。

## Test Cases

- 低电量遥测触发告警。
- 链路质量下降触发告警。

## Known Limitations

- MVP 不实现实时连接。

## Future Extensions

- 增加 MAVLink 只读遥测导入。
- 增加 Dashboard 状态页。

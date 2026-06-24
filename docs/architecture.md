# 架构说明

## 总体架构

MVP 采用离线 CLI 架构。CLI 位于 `apps/cli`，负责读取文件、调用规则模块、写出结果和审计记录。领域逻辑位于 `packages/`，每个包只负责一个清晰职责。

## 数据流

1. `log_parsers` 读取 CSV 或 JSON 飞行日志，生成 `FlightLogRecord`。
2. `telemetry_rules` 生成 `FlightLogSummary`。
3. `anomaly_detection` 生成带证据引用的 `AnomalyEvent`。
4. `diagnosis_rules` 根据摘要、异常和资产生成 `FaultHypothesis`。
5. `maintenance_rules` 生成 `MaintenanceRecommendation`。
6. `report_templates` 渲染 Markdown 运维报告。
7. `audit_logger` 为每次 skill 执行写入 audit JSON。

## Agent 与 Skill 边界

`agents/` 目录描述编排角色，MVP 中保持轻量。`skills/` 目录描述可复用能力的输入、输出、硬规则、证据要求和审计要求。可运行逻辑在 `packages/` 中实现，便于测试和复用。

## 扩展点

后续可以增加 PX4 ULog、ArduPilot BIN、MAVLink 遥测、SITL 仿真、PDF 报告、Web Dashboard 和工单系统集成。所有扩展必须保持安全边界，不得执行真实飞控控制命令。

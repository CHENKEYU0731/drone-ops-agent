# 数据契约

核心 schema 位于 `packages/drone_schemas/models.py`。

## 资产对象

- `DroneAsset`：无人机资产信息、序列号、固件版本、累计飞行小时、电池和维护历史。
- `DroneAsset.operational_status`：离线资产状态，支持 `active`、`maintenance_due`、`grounded` 等状态。
- `BatteryAsset`：电池化学类型、标称电压、循环次数、健康度、SOC、电压和温度。
- `FleetAsset`：离线机队资产集合，包含 fleet id、名称、资产 ID 列表和本地 source refs。
- `MissionPlan`：任务计划、预期模式、计划高度、返航高度、计划航程、预计飞行时间和电池余量要求。

## 日志与摘要

- `FlightLogRecord`：单条飞行日志记录。
- `FlightLogSummary`：飞行时长、最低电压、最大电流、最低 SOC、GPS、振动、电机不平衡、链路和模式切换摘要。
- `TelemetrySnapshot`：离线状态监控回放的单条遥测记录，包含飞行模式、高度、速度、电池、GPS、振动、电机输出、链路质量、温度、EKF 方差和 failsafe 状态。

## 运维输出

- `AnomalyEvent`：规则触发的异常事件。
- `FaultHypothesis`：按置信度排序的故障假设。
- `MaintenanceRecommendation`：带优先级、审批和证据的维护建议。
- `FleetHealthSummary`：机队健康趋势摘要，聚合本地 flight summary、维护建议、工单和验证输出。
- `FleetHealthFinding`：机队级健康发现，包含风险等级、受影响资产、受影响飞行和 evidence refs。
- `PreflightCheckResult`：离线飞行前检查结果，包含 `GO`、`REVIEW_REQUIRED` 或 `NO_GO` 状态。
- `PreflightCheckItem`：飞行前检查 warning 或 blocking item，包含 item、severity、reason、measured value、threshold、rule id、evidence refs 和 recommendation。
- `MonitoringSummary`：离线遥测回放摘要，包含 source refs、event count、highest severity、monitored duration、samples processed 和 human review 标记。
- `MonitoringEvent`：状态监控事件，包含 event type、severity、message、measured value、threshold、rule id 和 evidence refs。
- `OpsReport`：报告产物引用。

## 可追溯对象

- `EvidenceRef`：证据引用。
- `SkillRunAudit`：skill 执行审计记录。

重要输出对象必须包含证据、生成 skill、skill version 和人工复核标记。

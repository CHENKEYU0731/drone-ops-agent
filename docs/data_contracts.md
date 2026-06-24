# 数据契约

核心 schema 位于 `packages/drone_schemas/models.py`。

## 资产对象

- `DroneAsset`：无人机资产信息、序列号、固件版本、累计飞行小时、电池和维护历史。
- `BatteryAsset`：电池化学类型、标称电压、循环次数和健康度。
- `MissionPlan`：任务计划、预期模式和计划高度。

## 日志与摘要

- `FlightLogRecord`：单条飞行日志记录。
- `FlightLogSummary`：飞行时长、最低电压、最大电流、最低 SOC、GPS、振动、电机不平衡、链路和模式切换摘要。

## 运维输出

- `AnomalyEvent`：规则触发的异常事件。
- `FaultHypothesis`：按置信度排序的故障假设。
- `MaintenanceRecommendation`：带优先级、审批和证据的维护建议。
- `OpsReport`：报告产物引用。

## 可追溯对象

- `EvidenceRef`：证据引用。
- `SkillRunAudit`：skill 执行审计记录。

重要输出对象必须包含证据、生成 skill、skill version 和人工复核标记。

# monitor-replay 测试用例

- CSV telemetry 能被解析为按时间排序的 `TelemetrySnapshot`。
- JSON telemetry 能被解析为同等事件覆盖。
- 正常 telemetry 不触发监控事件，summary `human_review_required=false`。
- 样例 telemetry 至少触发电池、GPS、振动、电机不平衡、链路、温度、EKF、failsafe 和异常模式转换事件。
- 每个 `MonitoringEvent` 都包含 `evidence_refs`。
- `HIGH` 和 `CRITICAL` 事件必须 `human_review_required=true`。
- 存在 `HIGH` 或 `CRITICAL` 事件时，summary 必须 `human_review_required=true`。
- CLI 缺失 telemetry 文件时返回清晰错误，不显示 traceback。
- 每次成功运行 CLI 都生成 `audit/state-monitoring-*.json`。

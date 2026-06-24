# Skill: state-monitoring

## Purpose

`state-monitoring` 用于离线回放本地 telemetry CSV/JSON，并基于 YAML 规则生成状态监控事件、监控摘要和审计记录。该 skill 只做运维分析和人工复核建议，不连接真实无人机，不执行真实飞控动作。

## Inputs

- `--telemetry`：本地 CSV 或 JSON telemetry 文件。
- `--asset`：无人机资产 JSON。
- `--rules`：状态监控规则 YAML。
- `--out`：输出目录。

示例：

```bash
drone-ops monitor-replay --telemetry data/sample_logs/example_telemetry.csv --asset data/sample_assets/uav_001.json --rules data/sample_rules/monitoring_rules.yaml --out data/sample_reports/
```

## Outputs

- `monitoring_summary.json`：状态监控摘要。
- `monitoring_events.json`：规则触发事件列表。
- `audit/state-monitoring-*.json`：skill run 审计记录。

## Hard Rules

- 必须保持 advisory-only。
- 不得连接真实无人机。
- 不得 arm/disarm、启动电机、起飞、降落、返航或执行航线。
- 不得上传固件、写入飞控参数或执行 MAVLink command。
- 只能读取本地样例 telemetry、资产和规则配置。
- 任何 `HIGH` 或 `CRITICAL` 监控事件必须设置 `human_review_required=true`。
- 若摘要中存在 `HIGH` 或 `CRITICAL` 事件，summary 也必须设置 `human_review_required=true`。

## Procedure

1. 读取无人机资产和 telemetry 文件。
2. 使用 `parse_telemetry_replay` 验证 CSV/JSON 字段完整性和数值范围。
3. 按时间顺序排序 telemetry snapshot。
4. 从 YAML 加载规则阈值、severity、rule id 和允许模式转换。
5. 使用 `run_monitoring_replay` 执行规则型监控，生成 `MonitoringEvent`。
6. 汇总事件数量、最高严重级别、回放时长和样本数量。
7. 写出 `monitoring_summary.json`、`monitoring_events.json` 和 audit JSON。

## Rule Coverage

当前规则覆盖：

- low battery SOC
- battery voltage sag
- high current draw
- GPS degradation
- high HDOP
- low satellite count
- high vibration
- motor output imbalance
- communication link quality drop
- high temperature
- EKF variance high
- failsafe active
- unexpected mode transition

关键阈值、severity、rule id 和允许模式转换必须来自 YAML，不得写死在业务逻辑中。

## Evidence Requirements

每个 `MonitoringEvent` 必须包含 `evidence_refs`，至少记录：

- telemetry source
- source row 或 source id
- timestamp
- field
- measured_value
- threshold
- rule_id
- description

工程师必须能从输出 JSON 追溯事件为何触发。

## Audit Requirements

每次 `monitor-replay` 成功运行都必须生成 audit JSON，包含：

- `skill_name: state-monitoring`
- `skill_version`
- `input_refs`
- `output_refs`
- `tools_called`
- `rules_triggered`
- `human_review_required`
- `status`
- `created_at`

## Test Cases

- CSV telemetry parsing。
- JSON telemetry parsing。
- 正常 telemetry 不触发事件。
- 每类监控规则至少一个触发 case。
- `HIGH` / `CRITICAL` 事件要求人工复核。
- summary 汇总人工复核要求。
- 每个 event 都有 evidence refs。
- CLI 缺失文件错误清晰且无 traceback。
- audit JSON 创建成功。

## Known Limitations

- 当前仅支持本地 CSV/JSON 样例 telemetry。
- 不接入真实无人机硬件。
- 不支持 PX4 ULog、ArduPilot BIN、SITL 或 MAVLink 在线连接。
- 输出为 JSON 事件和摘要，尚未生成独立监控报告。

## Future Extensions

- 增加 PX4 ULog 和 ArduPilot BIN 的只读解析。
- 增加 MAVLink read-only telemetry 导入，但必须与 command execution 严格隔离。
- 增加 dashboard 状态页和更丰富的回放可视化。

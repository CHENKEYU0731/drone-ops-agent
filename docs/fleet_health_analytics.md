# v1.1.0 Fleet Health Analytics 契约

v1.1.0 的目标是把 v1.0.0 的单次离线运维能力扩展到多资产、多任务的本地健康趋势分析。

本阶段只定义 fleet analytics 的稳定输入、输出和安全边界，不接入真实机队平台，不做实时遥测，
不做 Web Dashboard，也不连接真实 CMMS / Jira / 飞书 / 企业微信。

## 范围

v1.1.0 Fleet Health Analytics 关注：

- 多架无人机的本地资产集合。
- 多次 `flight_summary.json` 的离线聚合。
- 电池、GPS、震动、链路、温度和维护建议的趋势信号。
- 机队级风险排序。
- 每个机队级发现都能追溯到单次飞行或本地运维输出。

## 稳定契约基线

新增 schema：

- `FleetRiskLevel`
- `FleetAsset`
- `FleetHealthFinding`
- `FleetHealthSummary`

这些 schema 只表示本地分析结果，不代表真实飞行授权、维修授权或自动调度。

## 输出语义

`FleetHealthSummary` 应包含：

- `fleet_id`
- `window_start`
- `window_end`
- `asset_count`
- `flight_count`
- `highest_risk`
- `risk_rankings`
- `findings`
- `evidence_refs`
- `source_refs`
- `human_review_required=true`

`FleetHealthFinding` 应包含：

- `finding_id`
- `category`
- `risk_level`
- `affected_assets`
- `affected_flights`
- `summary`
- `evidence_refs`
- `recommended_action`
- `human_review_required=true`

## 风险等级

Fleet 风险等级使用：

- `PASS`
- `LOW`
- `REVIEW_REQUIRED`
- `HIGH`
- `CRITICAL`

`PASS` 只表示本地导入数据未触发已知风险，不代表真实飞行安全许可。
`REVIEW_REQUIRED`、`HIGH` 和 `CRITICAL` 都需要人工复核。

## 安全边界

v1.1.0 继续保持 offline-only 和 advisory-only。

不得新增：

- 真实无人机连接
- 实时遥测连接
- MAVLink command execution
- PX4、ArduPilot、Gazebo、SITL 或外部仿真器启动或连接
- 真实 fleet platform API 调用
- 真实 CMMS、Jira、飞书、企业微信 API 调用
- 自动派单
- 自动执行维护动作
- 真实、敏感或未经确认允许的二进制飞行日志

## 后续阶段

## Offline Fleet Aggregation Baseline

`fleet-summary` CLI 可以读取本地 fleet manifest，并写出确定性的 `fleet_health_summary.json`：

```bash
python -m apps.cli.main fleet-summary \
  --manifest data/sample_fleet/fleet_manifest.json \
  --out <tmp-fleet-dir>
```

输入 manifest 只引用本地文件，例如：

- `flight_summary.json`
- `maintenance_recommendations.json`

输出包括：

- `fleet_health_summary.json`
- `audit/fleet-health-analytics-*.json`

当前 baseline 聚合以下离线信号：

- 低电量趋势
- GPS 降级趋势
- 振动异常趋势
- 高优先级维护建议

所有 finding 都保留 `evidence_refs`，可追溯到单次飞行 summary 或维护建议。

## 后续阶段

后续 v1.1.0 小阶段可以在本契约基础上增加：

1. fleet summary Markdown 报告。
2. v1.1.0 release readiness checklist。

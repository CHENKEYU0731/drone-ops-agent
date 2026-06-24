# Skill: flight-log-analysis

## Purpose

解析离线 CSV/JSON 飞行日志，生成 `FlightLogSummary` 和 `AnomalyEvent` 列表。该 skill 对应 CLI 命令 `drone-ops analyze-log`，核心函数包括 `parse_flight_log`、`summarize_flight` 和 `detect_anomalies`。

## Inputs

- `--log`：CSV 或 JSON 飞行日志。
- `--asset`：`DroneAsset` JSON 文件。
- 日志字段必须包含 timestamp、flight_mode、altitude_m、电池、GPS、振动、电机输出、链路质量和温度字段。

## Outputs

- `flight_summary.json`：飞行摘要。
- `anomalies.json`：异常事件列表。
- `audit/flight-log-analysis-<run_id>.json`：审计记录。

## Hard Rules

- 只读取离线文件，不连接真实无人机。
- 不执行 arm/disarm、起飞、降落、返航、航线执行、启动电机、上传固件或写飞控参数。
- 每个异常必须包含 `evidence_refs`。
- 触发异常时必须设置 `human_review_required=true`。

## Procedure

1. 调用 `parse_flight_log` 读取并验证日志。
2. 调用 `detect_anomalies` 执行确定性异常规则。
3. 调用 `summarize_flight` 计算飞行时长、电池、GPS、振动、电机、链路和模式切换摘要。
4. 写出 `flight_summary.json` 和 `anomalies.json`。
5. 写出审计记录，记录输入、输出、调用函数和触发规则。

## Evidence Requirements

- 每个异常的 `EvidenceRef` 必须指向原始日志 source id、timestamp、field、measured value、threshold 和 rule id。
- 摘要必须包含至少一条指向原始日志的 source evidence。

## Audit Requirements

- 审计记录必须包含 skill name、skill version、input refs、output refs、tools called、rules triggered、created_at、human_review_required 和 status。

## Test Cases

- CSV 和 JSON 日志均可解析。
- 空日志和字段缺失会返回清晰错误。
- 所有 MVP 异常规则可被样例日志触发。
- 每个异常都有证据引用。

## Known Limitations

- MVP 只支持 CSV/JSON，不支持 PX4 ULog 或 ArduPilot BIN。
- 阈值当前写在规则代码中，尚未配置化。

## Future Extensions

- 增加 ULog/BIN 只读解析。
- 增加规则阈值配置文件。
- 增加更多 golden case。

# Skill: flight-log-analysis

## Purpose

解析离线 CSV/JSON/PX4 ULog 飞行日志，生成 `FlightLogSummary` 和 `AnomalyEvent` 列表。该 skill 对应 CLI 命令 `drone-ops analyze-log`，核心函数包括 `parse_flight_log_details`、`parse_flight_log`、`summarize_flight` 和 `detect_anomalies`。

## Inputs

- `--log`：CSV、JSON 或本地 `.ulg` 飞行日志。
- `--format`：日志格式，默认 `auto`；支持 `csv`、`json`、`px4-ulog`，并保留 `ardupilot-bin` 自动识别契约。
- `--asset`：`DroneAsset` JSON 文件。
- 日志字段必须包含 timestamp、flight_mode、altitude_m、电池、GPS、振动、电机输出、链路质量和温度字段。
- PX4 ULog 真实解析依赖可选 extra：`pip install -e .[px4]`。缺少依赖时 CLI 必须给出清晰提示且不显示 traceback。

## Outputs

- `flight_summary.json`：飞行摘要。
- `anomalies.json`：异常事件列表。
- `audit/flight-log-analysis-<run_id>.json`：审计记录。

## Hard Rules

- 只读取离线文件，不连接真实无人机。
- 不执行 arm/disarm、起飞、降落、返航、航线执行、启动电机、上传固件或写飞控参数。
- PX4 ULog 支持仅限本地 `.ulg` 文件；不得执行 MAVLink command，不得修改飞控参数，不得上传固件。
- 每个异常必须包含 `evidence_refs`。
- 触发异常时必须设置 `human_review_required=true`。

## Procedure

1. 调用 `parse_flight_log_details` 读取并验证日志，记录 parser name、parser version、requested format 和 actual format。
2. 调用 `detect_anomalies` 执行确定性异常规则。
3. 调用 `summarize_flight` 计算飞行时长、电池、GPS、振动、电机、链路和模式切换摘要。
4. 写出 `flight_summary.json` 和 `anomalies.json`。
5. 写出审计记录，记录输入、输出、调用函数、触发规则、parser metadata 和 format metadata。

## Evidence Requirements

- 每个异常的 `EvidenceRef` 必须指向原始日志 source id、timestamp、field、measured value、threshold 和 rule id。
- 摘要必须包含至少一条指向原始日志路径、规范化字段和 parser 的 source evidence。

## Audit Requirements

- 审计记录必须包含 skill name、skill version、input refs、output refs、tools called、rules triggered、created_at、human_review_required 和 status。
- 对 PX4 ULog 或其他格式化解析，审计 metadata 必须包含 requested format、actual format、parser name、parser version、warnings、source metadata 和 parser metadata。

## Test Cases

- CSV、JSON 和 PX4 `.ulg` mock fixture 均可解析。
- `--format auto` 按扩展名识别 `.csv -> csv`、`.json -> json`、`.ulg -> px4-ulog`、`.bin -> ardupilot-bin`。
- 空日志和字段缺失会返回清晰错误。
- 缺少 PX4 ULog 可选依赖时提示 `pip install -e .[px4]` 且不显示 traceback。
- 所有 MVP 异常规则可被样例日志触发。
- 每个异常都有证据引用。

## Known Limitations

- PX4 ULog 初版只覆盖最小可用 topic/字段映射；未覆盖完整 ULog topic。
- ArduPilot BIN 仍由独立适配器实现，本 worktree 只保留扩展名契约。
- 阈值当前写在规则代码中，尚未配置化。

## Future Extensions

- 增加 ULog/BIN 只读解析。
- 增加规则阈值配置文件。
- 增加更多 golden case。

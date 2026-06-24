# Skill: preflight-check

## Purpose

执行离线飞行前检查，基于样例无人机资产、电池、任务计划、人工观测和 YAML 规则生成 advisory-only 的 `PreflightCheckResult`。该 skill 不连接真实无人机，不授权真实飞行。

CLI 入口是 `drone-ops preflight-check`，核心函数是 `run_preflight_check`。

## Inputs

- `DroneAsset` JSON，例如 `data/sample_assets/uav_001.json`。
- `BatteryAsset` JSON，例如 `data/sample_assets/battery_001.json`。
- `MissionPlan` JSON，例如 `data/sample_missions/example_mission.json`。
- 飞行前观测 JSON，例如 `data/sample_missions/preflight_observations_ok.json`。
- YAML 规则配置，例如 `data/sample_rules/preflight_rules.yaml`。

## Outputs

- `preflight_check_result.json`
- `audit/preflight-check-<run_id>.json`

## Hard Rules

- 不连接真实无人机。
- 不执行 arm/disarm、解锁或启动电机、起飞、降落、返航、航线执行、固件上传、飞控参数写入或 MAVLink command execution。
- 只要存在 blocking item，status 必须是 `NO_GO`。
- 存在 warning 且无 blocking item 时，status 必须是 `REVIEW_REQUIRED`。
- 无 warning 且无 blocking item 时，status 才能是 `GO`。
- `NO_GO` 和 `REVIEW_REQUIRED` 必须 `human_review_required=true`。
- `GO` 可以 `human_review_required=false`，但仍是离线建议，不代表自动授权真实飞行。

## Procedure

1. 读取资产、电池、任务、观测和 YAML 规则。
2. 检查资产状态、电池 SOC/电压/循环次数/温度、传感器、通信链路、任务约束和维护状态。
3. 为每个 warning 或 blocking item 生成 evidence refs。
4. 按 blocking > warning > clear 的优先级生成状态。
5. 写出 `preflight_check_result.json` 和 audit JSON。

## Evidence Requirements

- 每个 warning 和 blocking item 必须包含 `evidence_refs`。
- 每个 evidence ref 必须记录 source type、source id、field、measured value、threshold、rule id 和 description。
- 结果级 `evidence_refs` 汇总所有 warning 和 blocking item 的证据；GO case 也必须包含通过检查的规则证据。

## Audit Requirements

- audit 必须包含 skill name、skill version、input refs、output refs、tools called、rules triggered、created_at、human_review_required 和 status。
- `rules_triggered` 来自 warning 和 blocking item 的 rule id。

## Test Cases

- 正常可飞样例输出 `GO`。
- 警告样例输出 `REVIEW_REQUIRED`。
- 阻断样例输出 `NO_GO`。
- blocking item 必须导致 `NO_GO`。
- warning 必须导致 `REVIEW_REQUIRED`。
- warning 和 blocking item 都必须包含 evidence refs。
- CLI 缺失文件错误清晰且无 traceback。
- audit JSON 创建成功。

## Known Limitations

- 仅支持本项目样例 YAML 规则格式。
- 不读取真实硬件状态。
- 不支持 MAVLink、PX4 ULog、ArduPilot BIN 或 SITL 控制。

## Future Extensions

- 增加更完整的规则配置 schema 校验。
- 增加更多真实运维场景样例。
- 增加 PDF 或 Web Dashboard 中的飞行前检查视图。

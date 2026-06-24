# drone-ops-agent

`drone-ops-agent` 是一个离线优先的无人机运维 Copilot / Agent MVP。它基于样例飞行日志和样例资产数据，完成日志解析、异常检测、故障假设、维护建议、Markdown 运维报告和审计记录生成。

## 安全边界

本项目只做运维支持和决策辅助，不直接控制真实无人机。系统不得解锁电机、启动电机、执行起飞、降落、返航、航线飞行、上传固件、修改飞控关键参数、arm/disarm 飞行器或执行任何真实飞控命令。

所有涉及飞行安全、维护安全或飞控参数变更的建议，都必须由人工复核和批准。

## 安装

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

也可以在已有 Python 3.11+ 环境中直接安装：

```bash
pip install -e .[dev]
```

## 运行 MVP

完整离线流程：

```bash
drone-ops run-mvp --log data/sample_logs/example_flight.csv --asset data/sample_assets/uav_001.json --out data/sample_reports/
```

分步运行：

```bash
drone-ops analyze-log --log data/sample_logs/example_flight.csv --asset data/sample_assets/uav_001.json --out data/sample_reports/
drone-ops diagnose --summary data/sample_reports/flight_summary.json --asset data/sample_assets/uav_001.json --out data/sample_reports/
drone-ops generate-report --summary data/sample_reports/flight_summary.json --diagnosis data/sample_reports/diagnosis.json --maintenance data/sample_reports/maintenance_recommendations.json --out data/sample_reports/ops_report.md
```

未安装 CLI 入口时，可以使用：

```bash
python -m apps.cli.main run-mvp --log data/sample_logs/example_flight.csv --asset data/sample_assets/uav_001.json --out data/sample_reports/
```

## 飞行前检查

`preflight-check` 是离线 advisory-only 检查，不会连接真实无人机，也不会授权真实飞行。它读取样例资产、电池、任务、人工观测和 YAML 规则，输出 `GO`、`REVIEW_REQUIRED` 或 `NO_GO`。

```bash
drone-ops preflight-check --asset data/sample_assets/uav_001.json --battery data/sample_assets/battery_001.json --mission data/sample_missions/example_mission.json --observations data/sample_missions/preflight_observations_ok.json --rules data/sample_rules/preflight_rules.yaml --out data/sample_reports/
```

未安装 CLI 入口时：

```bash
python -m apps.cli.main preflight-check --asset data/sample_assets/uav_001.json --battery data/sample_assets/battery_001.json --mission data/sample_missions/example_mission.json --observations data/sample_missions/preflight_observations_ok.json --rules data/sample_rules/preflight_rules.yaml --out data/sample_reports/
```

输出文件为 `preflight_check_result.json` 和 `audit/preflight-check-*.json`。存在 blocking item 时结果为 `NO_GO`；只有 warning 时为 `REVIEW_REQUIRED`；没有 warning 和 blocking item 时才是 `GO`。`NO_GO` 和 `REVIEW_REQUIRED` 必须人工复核，`GO` 也只是离线建议，不代表自动批准真实飞行。

## 输出文件

运行后会生成：

- `flight_summary.json`
- `anomalies.json`
- `diagnosis.json`
- `maintenance_recommendations.json`
- `ops_report.md`
- `preflight_check_result.json`，仅在运行 `preflight-check` 时生成
- `audit/*.json`

## 运行测试

```bash
pytest
```

## 添加新的 skill

1. 在 `skills/<skill-name>/` 下创建 `SKILL.md`、`schema.json`、`examples/` 和 `tests/`。
2. 在 `SKILL.md` 中明确 Purpose、Inputs、Outputs、Hard Rules、Procedure、Evidence Requirements、Audit Requirements、Test Cases、Known Limitations 和 Future Extensions。
3. 在 `packages/` 中实现可测试的 Python 模块。
4. 为 schema、规则、报告或 CLI 工作流添加 pytest 测试。
5. 确保所有重要输出都包含 evidence refs、skill version 和 human review 标记。

## 查看审计日志

审计日志位于输出目录的 `audit/` 子目录。每条记录包含 skill 名称、版本、输入文件、输出文件、调用工具、触发规则、时间戳、人工复核要求和执行状态。

## 当前限制

- 仅支持 CSV 和 JSON 样例飞行日志。
- 仅使用确定性规则，不使用机器学习。
- 不包含真实硬件、MAVLink、PX4 ULog、ArduPilot BIN 或 SITL 集成。
- 报告为 Markdown，PDF 生成留作后续扩展。

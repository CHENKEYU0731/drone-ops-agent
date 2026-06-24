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
drone-ops export-pdf --markdown data/sample_reports/ops_report.md --out data/sample_reports/ops_report.pdf
```

未安装 CLI 入口时，可以使用：

```bash
python -m apps.cli.main run-mvp --log data/sample_logs/example_flight.csv --asset data/sample_assets/uav_001.json --out data/sample_reports/
```

## PDF 报告导出

Markdown 运维报告可以导出为本地 PDF。PDF 导出只读取本地 Markdown 报告并写出 PDF 文件，不改变 advisory-only 安全边界，也不会连接真实无人机或执行任何真实动作。

```bash
drone-ops export-pdf --markdown data/sample_reports/ops_report.md --out data/sample_reports/ops_report.pdf
```

未安装 CLI 入口时：

```bash
python -m apps.cli.main export-pdf --markdown data/sample_reports/ops_report.md --out data/sample_reports/ops_report.pdf
```

也可以在生成 Markdown 报告时同步导出 PDF：

```bash
drone-ops generate-report --summary data/sample_reports/flight_summary.json --diagnosis data/sample_reports/diagnosis.json --maintenance data/sample_reports/maintenance_recommendations.json --out data/sample_reports/ops_report.md --pdf data/sample_reports/ops_report.pdf
```

当前 PDF 以可读和结构清楚为目标，支持标题、段落、列表和代码块的基础渲染；复杂 Markdown 表格和精细排版留作后续扩展。

PDF 导出会优先使用环境变量 `DRONE_OPS_PDF_FONT_PATH` 指定的可嵌入 CJK TrueType/OpenType 字体；未设置时会搜索常见 Linux、Windows 和 macOS 系统字体。若环境中没有可用中文字体，请先安装 Noto CJK 等字体，或设置 `DRONE_OPS_PDF_FONT_PATH=/path/to/font.ttf`。

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

## 状态监控回放

`monitor-replay` 是离线 advisory-only 遥测回放，不会连接真实无人机，也不会执行任何真实动作。它读取本地 telemetry CSV/JSON、无人机资产和 YAML 规则，按时间顺序生成监控事件、状态摘要和 audit JSON。

```bash
drone-ops monitor-replay --telemetry data/sample_logs/example_telemetry.csv --asset data/sample_assets/uav_001.json --rules data/sample_rules/monitoring_rules.yaml --out data/sample_reports/
```

未安装 CLI 入口时：

```bash
python -m apps.cli.main monitor-replay --telemetry data/sample_logs/example_telemetry.csv --asset data/sample_assets/uav_001.json --rules data/sample_rules/monitoring_rules.yaml --out data/sample_reports/
```

输出文件为 `monitoring_summary.json`、`monitoring_events.json` 和 `audit/state-monitoring-*.json`。每个监控事件都包含 `evidence_refs`，可追溯到 telemetry 来源、字段、测量值、阈值和规则 ID。任何 `HIGH` 或 `CRITICAL` 事件都会要求人工复核；即使未来扩展到 MAVLink 遥测，也只能作为 read-only 导入，必须与 MAVLink command execution 严格隔离。

## 离线日志格式扩展

`analyze-log` 支持统一的 `--format` 参数。默认 `auto` 按扩展名识别日志格式：

- `.csv` -> `csv`
- `.json` -> `json`
- `.ulg` -> `px4-ulog`
- `.bin` -> `ardupilot-bin`

```bash
drone-ops analyze-log --log data/sample_logs/example_flight.csv --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
drone-ops analyze-log --log data/sample_logs/example_flight.json --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
drone-ops analyze-log --log data/sample_logs/example_px4_mock.ulg --asset data/sample_assets/uav_001.json --out data/sample_reports --format px4-ulog
drone-ops analyze-log --log data/sample_logs/example_ardupilot.bin --asset data/sample_assets/uav_001.json --out data/sample_reports --format ardupilot-bin
```

PX4 ULog 和 ArduPilot BIN 初版只做本地离线解析适配，不连接真实无人机，不执行 MAVLink command，不写飞控参数，也不上传固件。真实 `.ulg` 解析依赖可选 extra：

```bash
pip install -e .[px4]
```

真实 `.bin` 解析依赖可选 extra：

```bash
pip install -e .[ardupilot]
```

默认安装和 `pip install -e .[dev]` 不会强制安装这些可选飞控日志解析库。缺少可选依赖时，CLI 会给出安装提示并退出，不显示 traceback。

## 离线仿真验证

`validate-simulation` 是 simulation-validation skill 的离线 MVP。它只导入 mock/exported simulation result JSON，并基于规则输出 `PASS`、`FAIL` 或 `REVIEW_REQUIRED`，不会启动 PX4、ArduPilot、Gazebo 或真实 SITL 环境。

```bash
drone-ops validate-simulation --scenario data/sample_simulation/example_scenario.json --result data/sample_simulation/example_simulation_result.json --out data/sample_reports/
```

输出文件为 `simulation_run.json` 和 `audit/simulation-validation-*.json`。所有仿真验证输出都包含 `evidence_refs`，并固定要求 `human_review_required=true`。`PASS` 只表示离线仿真导入结果未发现阻断项，不代表真实飞行授权。

## 输出文件

运行后会生成：

- `flight_summary.json`
- `anomalies.json`
- `diagnosis.json`
- `maintenance_recommendations.json`
- `ops_report.md`
- `ops_report.pdf`，仅在运行 `export-pdf` 或 `generate-report --pdf` 时生成
- `preflight_check_result.json`，仅在运行 `preflight-check` 时生成
- `monitoring_summary.json` 和 `monitoring_events.json`，仅在运行 `monitor-replay` 时生成
- `simulation_run.json`，仅在运行 `validate-simulation` 时生成
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

- CSV/JSON、PX4 ULog 和 ArduPilot BIN 支持仍以离线样例和最小字段映射为主。
- 仅使用确定性规则，不使用机器学习。
- 不包含真实硬件连接、实时 MAVLink、真实 SITL 启动或任何飞控命令执行。
- PX4 ULog / ArduPilot BIN 真实日志解析依赖为可选 extra，默认安装不包含。
- SITL validation 初版只支持 mock/offline simulation result import。
- PDF 报告当前为基础可读排版，复杂 Markdown 表格和高级版式留作后续扩展。

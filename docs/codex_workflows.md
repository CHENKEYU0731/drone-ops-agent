# Codex 后续工作流

可以把以下任务继续交给 Codex：

- PX4 ULog 只读解析支持已具备 MVP：`drone-ops analyze-log --format px4-ulog --log <local.ulg> ...`，真实 ULog 解析需安装 `pip install -e .[px4]`，mock fixture 可用于离线测试。
- ArduPilot BIN 只读解析支持已具备 MVP：`drone-ops analyze-log --format ardupilot-bin --log <local.bin> ...`，真实 BIN 解析需安装 `pip install -e .[ardupilot]`，mock fixture 可用于离线测试。
- 增加 MAVLink 遥测只读导入。
- 扩展 `monitor-replay` 规则和样例 telemetry 数据，但必须保持离线 advisory-only，不得连接真实无人机或执行真实动作。
- 增加 SITL 仿真验证，但保持真实硬件隔离。
- 扩展 PDF 报告高级排版、表格渲染和模板版本管理。
- 增加 Web Dashboard。
- 增加工单系统或 CMMS 集成。
- 增加失败运行审计。
- 增加规则阈值配置文件。
- 扩展飞行前检查规则和样例，但必须保持 advisory-only，不得接入真实飞控控制动作。
- 增强报告验证和证据索引：使用 `drone-ops validate-report --report-dir data/sample_reports/` 检查结构化 JSON、Markdown 报告和 audit JSON 的证据链；如需写出 `evidence_index.json` 和 `report_validation.json`，添加 `--write-index`。该流程只做离线可信度检查，不代表真实飞行安全许可。

每个任务都应先更新安全边界和测试，再实现代码。

报告验证工作流约束：

- `validate-report` 必须保持离线，只读取本地 `flight_summary.json`、`anomalies.json`、`diagnosis.json`、`maintenance_recommendations.json`、`ops_report.md` 和 `audit/*.json`。
- 不得连接真实无人机，不得执行 MAVLink command、arm/disarm、takeoff、land、RTL、mission execution、firmware upload 或 parameter write。
- 验证规则只能加强维护/飞行安全输出的 `human_review_required=true` 要求，不得静默放宽。
- diagnosis evidence 必须能追溯到 summary 或 anomaly evidence；maintenance evidence 必须能追溯到 summary、anomaly 或 diagnosis evidence。
- `--write-index` 输出应保持确定性，便于 golden/snapshot 风格测试。
- CLI 失败时必须输出清晰错误并返回非 0 exit code，不显示 traceback。

PX4 ULog 工作流约束：

- 仅处理本地 `.ulg` 文件，禁止连接真实无人机。
- 禁止执行 MAVLink command、arm/disarm、takeoff、land、RTL、mission execution、firmware upload 或 parameter write。
- `--format auto` 必须按 `.ulg -> px4-ulog` 识别；CSV/JSON 旧流程必须保持可用。
- `flight-log-analysis` audit JSON 需记录 parser name、parser version、requested format、actual format 和 parser metadata。

ArduPilot BIN 工作流约束：

- 仅处理本地 `.bin` 文件，禁止连接真实无人机。
- 禁止执行 MAVLink command、arm/disarm、takeoff、land、RTL、mission execution、firmware upload 或 parameter write。
- `--format auto` 必须按 `.bin -> ardupilot-bin` 识别；CSV/JSON 旧流程必须保持可用。
- 真实 BIN 解析使用可选 `pymavlink` 依赖：`pip install -e .[ardupilot]`。
- 仓库只保留小型 mock BIN fixture，不提交大体积真实飞行日志。
- `flight-log-analysis` audit JSON 需记录 parser name、parser version、requested format、actual format 和 parser metadata。

v0.6.0 real sample log validation 工作流：

- 先使用 `docs/log_parser_coverage.md` 和 `data/sample_logs/README.md` 判断字段覆盖、fixture 来源、脱敏状态和体积限制。
- 真实或脱敏 `.ulg` 应放入 `data/sample_logs/px4/`，真实或脱敏 `.bin` 应放入 `data/sample_logs/ardupilot/`。
- 如果无法确认授权、脱敏或文件大小，不要提交真实日志；使用 mock fixture、fake real-path tests 或 documented placeholder。
- 默认测试必须能在没有真实 `.ulg` / `.bin` 的情况下通过；真实 fixture 测试应 skip 并提示 README。
- 可选依赖仍只能通过 `pip install -e .[px4]` 或 `pip install -e .[ardupilot]` 安装，不得加入默认或 dev 依赖。

v0.7.0 release readiness 工作流：

- 使用 `docs/v0.7.0_release_readiness.md` 作为发布前质量门禁清单。
- 运行 `pytest`。
- 使用 `python -m apps.cli.main run-mvp --log data/sample_logs/example_flight.csv --asset data/sample_assets/uav_001.json --out <tmp-report-dir>` 生成临时报表目录。
- 运行 `python -m apps.cli.main validate-report --report-dir <tmp-report-dir> --write-index`。
- 确认 `<tmp-report-dir>/evidence_index.json` 和 `<tmp-report-dir>/report_validation.json` 已生成。
- 运行 `python -m apps.cli.main validate-simulation --scenario data/sample_simulation/example_scenario.json --result data/sample_simulation/example_simulation_result.json --out <tmp-simulation-dir>`。
- 确认最新 `main` GitHub Actions 在 Python 3.11 和 Python 3.12 上均为 success。
- 保持 offline-only 和 advisory-only；不得添加真实无人机控制、MAVLink command execution、真实仿真器启动或敏感/二进制飞行日志。

v1.0.0 release readiness 工作流：

- 使用 `docs/v1.0.0_release_readiness.md` 作为发布前主清单。
- 运行 `pytest`。
- 运行 `pytest tests/unit/test_v1_safety_regression_gate.py`。
- 使用 `python -m apps.cli.main run-mvp --log data/sample_logs/example_flight.csv --asset data/sample_assets/uav_001.json --out <tmp-report-dir>` 生成临时报表目录。
- 运行 `python -m apps.cli.main validate-report --report-dir <tmp-report-dir> --write-index`。
- 运行 `python -m apps.cli.main validate-simulation --scenario data/sample_simulation/example_scenario.json --result data/sample_simulation/example_simulation_result.json --out <tmp-simulation-dir>`。
- 运行 `python -m apps.cli.main generate-work-orders --maintenance <tmp-report-dir>/maintenance_recommendations.json --asset data/sample_assets/uav_001.json --out <tmp-report-dir>`。
- 运行 `python -m apps.cli.main validate-work-orders --drafts <tmp-report-dir>/work_order_drafts.json --out <tmp-report-dir>`。
- 可选运行 `python -m apps.cli.main export-pdf --markdown <tmp-report-dir>/ops_report.md --out <tmp-report-dir>/ops_report.pdf`。
- 确认 GitHub Actions Python 3.11 和 Python 3.12 均为 success。
- 保持 offline-only、mock-import-only 和 advisory-only；不得添加真实无人机连接、MAVLink command execution、真实仿真器启动、真实工单系统调用或自动派单。

v1.4.0 diagnosis/report evaluation 工作流：

- 使用 `docs/v1.4.0_release_readiness.md` 作为发布前质量门禁清单。
- 运行 `pytest`。
- 运行 `pytest tests/unit/test_eval_contracts.py tests/unit/test_eval_runner.py tests/integration/test_eval_cli.py tests/unit/test_v1_4_release_readiness_docs.py`。
- 运行 `python -m apps.cli.main run-evals --case data/sample_evals/diagnosis_report_eval_case.json --out <tmp-eval-dir>`。
- 确认 `<tmp-eval-dir>/eval_results.json`、`<tmp-eval-dir>/eval_report.md` 和 `audit/diagnosis-report-evaluation-*.json` 已生成。
- 确认 eval status 为 `PASS`，输出保持确定性，且所有结论默认 `human_review_required=true`。
- 保持 offline-only 和 advisory-only；不得调用外部模型，不得连接真实无人机、飞控、MAVLink endpoint、真实仿真器、fleet platform 或真实维修系统。

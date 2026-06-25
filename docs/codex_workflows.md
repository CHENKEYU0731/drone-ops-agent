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

每个任务都应先更新安全边界和测试，再实现代码。

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

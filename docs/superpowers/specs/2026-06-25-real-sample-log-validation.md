# v0.6.0 Real Sample Log Validation 实现计划

日期：2026-06-25

目标版本：v0.6.0 - Real Sample Log Validation

基线版本：v0.5.0

基线 commit：`913b9609e5e1deff7342a5a938c83d2570496907`

## 目标

在 v0.5.0 已有 PX4 ULog / ArduPilot BIN parser framework 基础上，补充小型真实或脱敏日志样例验证策略、parser coverage 文档、错误处理测试和 CLI 验证流程。该阶段仍然只做本地离线日志读取、风险分析、报告和人工复核辅助，不引入任何真实无人机连接或控制能力。

## 1. 当前 v0.5.0 parser 能力盘点

### 统一入口

- `packages/log_parsers/base.py` 定义 `FlightLogParser`、`ParsedFlightLog`、`ParserFormat`、`detect_log_format(path)` 和 `resolve_log_format(path, requested_format)`。
- `packages/log_parsers/registry.py` 统一注册 CSV / JSON / PX4 ULog / ArduPilot BIN parser。
- `analyze-log --format auto` 按扩展名识别：
  - `.csv` -> `csv`
  - `.json` -> `json`
  - `.ulg` -> `px4-ulog`
  - `.bin` -> `ardupilot-bin`
- `apps/cli/main.py` 的 `analyze-log` 输出 `flight_summary.json`、`anomalies.json` 和 `audit/*.json`，audit metadata 已记录 requested format、actual format、parser name、parser version、warnings、source metadata 和 parser metadata。

### PX4 ULog

- `packages/log_parsers/px4_ulog.py` 当前支持两条路径：
  - mock `.ulg`：读取 JSON mock fixture，`format=px4-ulog-mock`。
  - 真实 `.ulg`：通过可选依赖 `pyulog` 读取本地 ULog 文件。
- 真实路径当前需要 topic：
  - `battery_status`
  - `vehicle_status`
  - `vehicle_local_position`
  - `vehicle_gps_position`
  - `vehicle_imu_status`
  - `actuator_outputs`
  - `telemetry_status`
  - `sensor_combined`
- 当前映射最小字段到 `FlightLogRecord`，并通过现有 `summarize_flight` / `detect_anomalies` 生成摘要和异常。

### ArduPilot BIN

- `packages/log_parsers/ardupilot_bin.py` 当前支持两条路径：
  - mock `.bin`：以 `DRONE_OPS_ARDUPILOT_BIN_MOCK_V1` magic line 标识，payload 为 JSON。
  - 真实 `.bin`：通过可选依赖 `pymavlink` 的 `DFReader_binary` 读取本地 DataFlash 日志。
- 真实路径当前读取 message：
  - `BAT` / `BAT2`
  - `GPS` / `GPS2`
  - `VIBE`
  - `RCOU`
  - `MODE` / `MODE2`
- 当前 `_DefaultingRecordBuilder` 用受控默认值拼装最小 `FlightLogRecord`，如果没有可用 snapshot 则报错。

## 2. 需要新增或调整的文件

计划新增：

- `docs/log_parser_coverage.md`
- `docs/releases/v0.6.0-draft.md`
- `data/sample_logs/px4/README.md`
- `data/sample_logs/ardupilot/README.md`
- `tests/unit/test_px4_real_fixture_parser.py`
- `tests/unit/test_ardupilot_real_fixture_parser.py`
- `tests/integration/test_real_log_parser_flow.py`

计划修改：

- `packages/log_parsers/px4_ulog.py`
- `packages/log_parsers/ardupilot_bin.py`
- `README.md`
- `docs/codex_workflows.md`
- `skills/flight-log-analysis/SKILL.md`

只有在 fixture policy 明确且文件体积、版权、隐私满足要求时，才新增小型脱敏二进制 fixture：

- `data/sample_logs/px4/<small-redacted>.ulg`
- `data/sample_logs/ardupilot/<small-redacted>.bin`

## 3. 小型真实/脱敏 fixture 策略

### 允许提交的 fixture 条件

真实或脱敏日志必须同时满足：

- 文件来源明确，可公开放入仓库。
- 不包含个人位置轨迹、客户信息、设备序列号、操作者信息、无线链路标识或敏感时间地点。
- 单个文件建议不超过 256 KB；硬上限 512 KB。
- 只保留解析验证所需最短片段。
- 文件名不得包含真实客户、地点或机体身份。
- 提供旁注 README，说明来源类型、脱敏方式、字段覆盖范围、限制和 license/permission 状态。

### 不允许提交的 fixture

- 来源不明的真实飞行日志。
- 包含精确 GPS 轨迹或敏感地理位置的日志。
- 大体积完整飞行日志。
- 商业客户、竞赛队伍或第三方未经许可日志。
- 任何包含真实控制命令执行意图或飞控写操作脚本的文件。

### 脱敏方式

- 截取短时间窗口。
- 移除或扰动 GPS 坐标，仅保留卫星数、HDOP 等非位置字段。
- 移除 serial number、vehicle id、operator id、mission name。
- 保留 battery、mode、altitude、vibration、motor output、temperature 等解析字段。
- 在 README 中记录脱敏动作，不伪装成完整真实飞行。

## 4. 暂时没有真实日志时的 placeholder 流程

如果本阶段没有可安全提交的真实 `.ulg` / `.bin`：

- 不随意下载或加入来源不明日志。
- 保留现有 mock fixture。
- 增加 `data/sample_logs/px4/README.md` 和 `data/sample_logs/ardupilot/README.md`，明确真实 fixture 接收标准。
- 新增 deterministic mini fixture 或 documented placeholder，但文件名必须明确标记 `mock`、`mini` 或 `placeholder`。
- 单元测试使用 monkeypatch / fake `pyulog` / fake `pymavlink` 对象模拟真实解析库输出，验证真实解析路径的字段映射、缺失 topic/message 和错误处理。
- 集成测试在没有真实依赖时验证缺依赖错误；在有依赖和安全 fixture 时启用真实样例测试。

该策略避免为了追求“真实样例”而污染仓库或引入隐私风险。

## 5. parser coverage 文档结构

新增 `docs/log_parser_coverage.md`，建议结构：

- 概述：支持格式、入口 CLI、安全边界。
- CSV / JSON coverage：字段要求与现有稳定能力。
- PX4 ULog coverage：
  - required topics
  - topic field -> `FlightLogRecord` field 映射表
  - fallback / missing behavior
  - optional dependency
  - fixture policy
- ArduPilot BIN coverage：
  - consumed message types
  - message field -> `FlightLogRecord` field 映射表
  - fallback / missing behavior
  - optional dependency
  - fixture policy
- Evidence / audit metadata：source_metadata、parser_metadata、evidence_refs。
- Known limitations：最小字段映射、非完整飞控日志覆盖、无真实控制能力。
- Adding new fixtures：文件体积、脱敏、license、测试命令。

## 6. PX4 ULog 字段映射计划

当前映射继续保持最小可用，不扩展到完整 ULog topic。

计划明确和测试以下映射：

- `battery_status.voltage_v` / `voltage_filtered_v` -> `battery_voltage_v`
- `battery_status.current_a` / `current_filtered_a` -> `battery_current_a`
- `battery_status.remaining` 或 mock `battery_soc_pct` -> `battery_soc_pct`
- `vehicle_status.nav_state` / `flight_mode` -> `flight_mode`
- `vehicle_local_position.z` / `altitude_m` -> `altitude_m`
- `vehicle_gps_position.satellites_used` / `gps_satellites` -> `gps_satellites`
- `vehicle_gps_position.hdop` / `eph` -> `gps_hdop`
- `vehicle_imu_status.accel_vibration_metric` 等 -> `vibration_x/y/z`
- `actuator_outputs.outputs` 或 `output_0..3` -> `motor_1_output..motor_4_output`
- `telemetry_status.link_quality_pct` / `rssi` -> `link_quality_pct`
- `sensor_combined.temperature_c` / `temperature` -> `temperature_c`

计划增强：

- 对缺失 required topic 给出清晰错误，包含 topic 名和文件路径。
- 对 topic 存在但 sample 不可用给出清晰错误。
- 对字段缺失给出清晰错误，包含 field、sample index 和文件路径。
- 对真实 pyulog path 的 parser_metadata 增加 `topics_used` 和 `sample_count`。

## 7. ArduPilot BIN 字段映射计划

当前映射继续保持最小可用，不追求完整 DataFlash message 覆盖。

计划明确和测试以下映射：

- `MODE.Mode` / `MODE.ModeNum` -> `flight_mode`
- `GPS.Alt` / `GPS.RelAlt` / `GPS.HAGL` -> `altitude_m`
- `GPS.NSats` / `GPS.Sats` -> `gps_satellites`
- `GPS.HDop` / `GPS.HDOP` -> `gps_hdop`
- `BAT.Volt` / `BAT.VoltR` -> `battery_voltage_v`
- `BAT.Curr` / `BAT.CurrTot` -> `battery_current_a`
- `BAT.RemPct` / `BAT.SoC` -> `battery_soc_pct`
- `BAT.Temp` / `BAT.Temp2` -> `temperature_c`
- `VIBE.VibeX/Y/Z` -> `vibration_x/y/z`
- `RCOU.C1..C4` -> `motor_1_output..motor_4_output`
- link quality 暂无稳定 DataFlash message 映射时继续使用受控默认值，并在 warnings 或 parser_metadata 中记录。

计划增强：

- 记录 consumed message count 和 snapshot count。
- 当没有可用 snapshot 时，错误包含 consumed messages 和缺失方向。
- 对字段缺失但使用默认值的场景增加 warnings，避免静默误读。
- 保留 mock fixture magic line 兼容 CRLF / LF。

## 8. 错误处理计划

### 缺少 optional dependency

- PX4：缺少 `pyulog` 时抛出 `LogParserDependencyError`，CLI 输出包含 `pip install -e .[px4]`，不显示 traceback。
- ArduPilot：缺少 `pymavlink` 时抛出 `LogParserDependencyError`，CLI 输出包含 `pip install -e .[ardupilot]`，不显示 traceback。

### 缺失字段 / topic / message

- PX4 required topic 缺失：`PX4 ULog missing required topic <topic>: <path>`。
- PX4 required field 缺失：`PX4 ULog missing required field <field> at sample <index>: <path>`。
- ArduPilot 无 usable records：`ArduPilot BIN log produced no usable records: <path>`，并尽量附带 message coverage context。
- ArduPilot mock fixture 缺字段：保留当前 `record <index> missing fields [...]`。

### 输入与格式错误

- `--format auto` 无法识别扩展名时返回支持规则。
- `--format px4-ulog` 指向非 `.ulg` 时返回清晰错误。
- `--format ardupilot-bin` 指向非 `.bin` 时返回清晰错误。
- 空文件返回清晰错误。

## 9. 测试计划

### 单元测试

`tests/unit/test_px4_real_fixture_parser.py`：

- fake `pyulog.ULog` dataset rows 可以走 `_parse_pyulog` 真实路径映射。
- 缺少 `battery_status` topic 报错清晰。
- 缺少 required field 报错清晰。
- parser_metadata 包含 `mock_fixture=false`、`topics_used`、`sample_count`。
- 缺少 `pyulog` optional dependency 的错误包含安装提示且无控制能力。

`tests/unit/test_ardupilot_real_fixture_parser.py`：

- fake `pymavlink.DFReader.DFReader_binary` 可以走 DataFlash 路径映射。
- 缺少可用 message 时报错清晰。
- 使用默认值时 warnings 或 parser_metadata 明确。
- parser_metadata 包含 `mock_fixture=false`、`messages_used`、snapshot count。
- 缺少 `pymavlink` optional dependency 的错误包含安装提示且无 traceback。

### 集成测试

`tests/integration/test_real_log_parser_flow.py`：

- `analyze-log --format auto` CSV 仍通过。
- `analyze-log --format auto` JSON 仍通过。
- mock `.ulg` 仍通过。
- mock `.bin` 仍通过。
- 如果存在安全真实/脱敏 `.ulg`，则真实/脱敏 PX4 fixture 通过。
- 如果存在安全真实/脱敏 `.bin`，则真实/脱敏 ArduPilot fixture 通过。
- fixture 缺失时用 pytest skip，并提示如何添加安全 fixture。

### golden test

- 不新增大体积 golden 输出。
- 仅在真实/脱敏 fixture 被接受后，考虑增加最小 snapshot 断言，例如 record_count、parser_metadata、evidence_refs 和 audit metadata。

## 10. CLI 验证命令

基础回归：

```bash
pytest
python -m apps.cli.main run-mvp --log data/sample_logs/example_flight.csv --asset data/sample_assets/uav_001.json --out data/sample_reports
python -m apps.cli.main analyze-log --log data/sample_logs/example_flight.csv --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
python -m apps.cli.main analyze-log --log data/sample_logs/example_flight.json --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
python -m apps.cli.main analyze-log --log data/sample_logs/example_px4_mock.ulg --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
python -m apps.cli.main analyze-log --log data/sample_logs/example_ardupilot.bin --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
python -m apps.cli.main validate-simulation --scenario data/sample_simulation/example_scenario.json --result data/sample_simulation/example_simulation_result.json --out data/sample_reports
python -m apps.cli.main export-pdf --markdown data/sample_reports/ops_report.md --out data/sample_reports/ops_report.pdf
```

真实/脱敏 fixture 可用时：

```bash
python -m apps.cli.main analyze-log --log data/sample_logs/px4/<small-redacted>.ulg --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
python -m apps.cli.main analyze-log --log data/sample_logs/ardupilot/<small-redacted>.bin --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
```

缺依赖验证：

```bash
python -m apps.cli.main analyze-log --log <non-mock>.ulg --asset data/sample_assets/uav_001.json --out data/sample_reports --format px4-ulog
python -m apps.cli.main analyze-log --log <non-mock>.bin --asset data/sample_assets/uav_001.json --out data/sample_reports --format ardupilot-bin
```

## 11. 安全扫描计划

运行关键词扫描：

```bash
rg -n -i "mavlink|command_long|mavutil|arm|disarm|takeoff|land|return_to_home|rtl|mission upload|mission execution|motor start|firmware upload|parameter write|param_set" apps packages tests skills docs README.md pyproject.toml
rg -n -i "mavutil\\.mavlink_connection|command_long_send|param_set_send|set_mode_send|mission_item|ftp_upload|arm\\(|disarm\\(|takeoff\\(|land\\(" apps packages tests
```

接受的命中：

- 安全禁止说明。
- 测试 forbidden list。
- 可选解析库导入，如 `pymavlink.DFReader`。
- 既有飞行模式文本，如 `LAND`。

阻断命中：

- 任何真实连接 API。
- 任何 MAVLink command execution。
- 任何 arm/disarm/takeoff/land/RTL/mission execution/firmware upload/parameter write 调用。

## 12. 验收标准

- `pytest` 全部通过。
- `run-mvp` 不回归。
- `analyze-log --format auto` CSV 通过。
- `analyze-log --format auto` JSON 通过。
- `analyze-log --format auto` mock `.ulg` 通过。
- `analyze-log --format auto` mock `.bin` 通过。
- 如果提供真实/脱敏 `.ulg`，则真实/脱敏 PX4 fixture 通过。
- 如果提供真实/脱敏 `.bin`，则真实/脱敏 ArduPilot fixture 通过。
- 缺少 optional dependency 时错误清晰，无 traceback。
- 输出仍包含 `evidence_refs`。
- audit JSON 仍包含 parser/format metadata。
- 不包含真实无人机控制能力。
- 默认安装和 `.[dev]` 不强制安装 `pyulog` / `pymavlink`。
- 不提交来源、隐私或体积不合规的真实日志。

## 13. 风险和限制

- 真实 ULog/BIN 文件可能包含敏感 GPS、序列号、操作者或场地信息，必须先脱敏。
- 小型真实日志可能无法覆盖所有 topic/message，不能把通过测试误读成完整飞控日志支持。
- `pyulog` 和 `pymavlink` 是 optional extras；CI 默认不应依赖它们。
- 没有安全真实样例时，v0.6.0 可能先完成 fixture policy、fake real-path tests 和 placeholder 流程，而不是提交真实二进制日志。
- ArduPilot DataFlash message 在不同固件版本中字段名可能变化，初版只承诺文档列出的最小映射。
- PX4 ULog topic 在不同 PX4 版本中可能变化，初版只承诺文档列出的最小映射。
- 本阶段不得扩展到 MAVLink live telemetry、SITL launcher、真实硬件连接或任何飞控命令。

## 是否需要真实样例日志

实现阶段可以不阻塞于真实日志文件：如果用户暂时无法提供来源明确、体积小、可公开、已脱敏的 `.ulg` / `.bin`，则按 placeholder 流程推进。

如果用户能提供样例，建议提供：

- PX4 `.ulg`：不超过 256 KB，去除敏感 GPS/serial/operator 信息，覆盖 battery、status、position、gps、imu、actuator、telemetry、temperature topic。
- ArduPilot `.bin`：不超过 256 KB，去除敏感 GPS/serial/operator 信息，覆盖 BAT、GPS、VIBE、RCOU、MODE message。

任何不满足来源、许可、隐私或体积要求的日志都不应提交到仓库。

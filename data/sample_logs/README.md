# 样例日志 Fixture 策略

本目录保存无人机运维 Agent 的小型离线日志 fixture。Fixture 只能用于本地解析、分析、测试、报告和审计记录，不得引入真实无人机连接或控制能力。

## 现有 fixture

- `example_flight.csv`：确定性 CSV 飞行日志 fixture。
- `example_flight.json`：确定性 JSON 飞行日志 fixture。
- `example_telemetry.csv` / `example_telemetry.json`：离线状态监控回放 fixture。
- `example_px4_mock.ulg`：带 `.ulg` 扩展名的 JSON-backed PX4 mock fixture。
- `example_ardupilot.bin`：带 `.bin` 扩展名的 magic-line JSON-backed ArduPilot mock fixture。

mock fixture 不是原始飞控日志。它们是确定性测试输入，用于在不安装可选 parser 依赖的情况下验证归一化流程。

## 可提交真实/脱敏 fixture 的条件

真实或脱敏 `.ulg` / `.bin` 必须同时满足：

- 来源明确，并允许公开提交到仓库。
- 单文件建议小于 256 KB。
- 已截取为 parser 验证所需的最短片段。
- 已移除或脱敏 GPS 坐标、真实地点、操作者姓名、客户名称、机体序列号、无线链路标识、任务名称等敏感信息。
- 文件名不暴露个人、客户、地点、事件或机体身份。
- 在格式专用目录的 README 中记录来源类型、脱敏方式、字段覆盖范围、已知限制和授权状态。

如果无法确认授权或脱敏状态，不得提交该日志。

## 放置路径

- PX4 ULog 真实/脱敏 fixture 放入 `data/sample_logs/px4/`。
- ArduPilot BIN 真实/脱敏 fixture 放入 `data/sample_logs/ardupilot/`。

## 没有真实 fixture 时如何运行

测试套件必须能在没有真实 `.ulg` 或 `.bin` 样例时通过。真实 fixture 测试在样例缺失时会 skip，并提示查看格式专用 README。mock fixture 继续覆盖 parser registry、auto format detection、evidence refs 和 audit metadata。

## 验证命令

```bash
python -m apps.cli.main analyze-log --log data/sample_logs/example_px4_mock.ulg --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
python -m apps.cli.main analyze-log --log data/sample_logs/example_ardupilot.bin --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
```

当已有合规真实/脱敏 fixture 时：

```bash
python -m apps.cli.main analyze-log --log data/sample_logs/px4/real_sample.ulg --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
python -m apps.cli.main analyze-log --log data/sample_logs/ardupilot/real_sample.bin --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
```

## 安全边界

所有 fixture 都只是本地文件，用于 offline advisory 分析。不得新增会连接飞行器、执行 MAVLink command、arm/disarm、起飞、降落、返航、执行航线、启动电机、上传固件或写入飞控参数的脚本、日志或辅助工具。

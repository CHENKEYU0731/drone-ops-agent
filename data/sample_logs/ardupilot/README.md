# ArduPilot BIN Fixture Placeholder

本目录预留给小型、已授权、已脱敏的 ArduPilot DataFlash BIN fixture。

仓库默认不提交真实 `.bin` 文件。当前使用 `data/sample_logs/example_ardupilot.bin` 作为 deterministic magic-line mock fixture，在不安装 `pymavlink` 的情况下验证 ArduPilot parser 归一化流程。

## 接收条件

真实或脱敏 ArduPilot `.bin` fixture 必须满足：

- 单文件建议小于 256 KB。
- 来源明确，可公开提交或属于项目可用资产。
- 已截取为 parser 验证所需的最短片段。
- 已移除或脱敏 GPS 坐标、机体标识、序列号、操作者姓名、客户名称、任务名称和敏感地点。
- 覆盖当前 parser 所需最小 message：
  - `BAT` / `BAT2`
  - `GPS` / `GPS2`
  - `VIBE`
  - `RCOU`
  - `MODE` / `MODE2`

如果不满足这些条件，不要提交真实日志；请继续使用 fake real-path tests 或 mock fixture。

## 可选依赖

真实 ArduPilot BIN 解析需要：

```bash
pip install -e .[ardupilot]
```

缺少 `pymavlink` 时，CLI 必须给出清晰错误且不显示 traceback。

## 验证命令

当合规 fixture 位于 `data/sample_logs/ardupilot/real_sample.bin` 时，运行：

```bash
python -m apps.cli.main analyze-log --log data/sample_logs/ardupilot/real_sample.bin --asset data/sample_assets/uav_001.json --out data/sample_reports --format auto
```

输出必须包含 `flight_summary.json`、`anomalies.json`、audit JSON、parser metadata 和 evidence refs。

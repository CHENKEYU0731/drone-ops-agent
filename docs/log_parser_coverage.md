# 日志解析器覆盖范围

本文档说明 `drone-ops analyze-log` 当前支持的离线日志格式、标准字段映射、真实/脱敏样例策略、证据链和审计约束。

## 安全边界

所有日志解析器都只能读取本地文件，用于离线 advisory 分析。解析器不得连接真实无人机，不得执行 MAVLink command，不得 arm/disarm，不得起飞、降落、返航，不得执行航线，不得启动电机，不得上传固件，不得写入飞控参数，也不得启动 PX4、ArduPilot、Gazebo 或真实 SITL 环境。

## 支持格式

`analyze-log --format auto` 按扩展名识别：

| 扩展名 | 格式 |
| --- | --- |
| `.csv` | `csv` |
| `.json` | `json` |
| `.ulg` | `px4-ulog` |
| `.bin` | `ardupilot-bin` |

所有格式最终都归一化为现有 `FlightLogRecord` 列表，并继续生成 `FlightLogSummary`、`AnomalyEvent`、`evidence_refs` 和 audit JSON。

## 标准字段

每个 parser 必须生成以下 `FlightLogRecord` 字段：

| 标准字段 | 含义 |
| --- | --- |
| `timestamp` | 带时区的样本时间 |
| `flight_mode` | 飞行模式或导航状态 |
| `altitude_m` | 高度或相对高度，单位米 |
| `battery_voltage_v` | 电池电压 |
| `battery_current_a` | 电池电流 |
| `battery_soc_pct` | 电池剩余电量百分比 |
| `gps_satellites` | GPS 卫星数 |
| `gps_hdop` | GPS HDOP 或等价质量指标 |
| `vibration_x` / `vibration_y` / `vibration_z` | 振动指标 |
| `motor_1_output` 到 `motor_4_output` | 归一化电机输出百分比 |
| `link_quality_pct` | 链路质量百分比 |
| `temperature_c` | 温度，单位摄氏度 |

## CSV / JSON 覆盖范围

CSV 和 JSON 是稳定基线。它们必须直接包含全部标准字段。缺少必需字段、数字无效、文件为空，或 JSON 不是记录列表时，都会返回清晰错误。

## PX4 ULog 覆盖范围

PX4 ULog 有两条路径：

- mock fixture：`data/sample_logs/example_px4_mock.ulg`
- 真实/脱敏 ULog：本地 `.ulg` 文件，通过可选依赖 `pyulog` 解析

真实 ULog 解析需要：

```bash
pip install -e .[px4]
```

### PX4 字段映射

| PX4 topic / field | 标准字段 |
| --- | --- |
| `battery_status.voltage_v` 或 `voltage_filtered_v` | `battery_voltage_v` |
| `battery_status.current_a` 或 `current_filtered_a` | `battery_current_a` |
| `battery_status.remaining` 或 mock `battery_soc_pct` | `battery_soc_pct` |
| `vehicle_status.nav_state` 或 `flight_mode` | `flight_mode` |
| `vehicle_local_position.z` 或 `altitude_m` | `altitude_m` |
| `vehicle_gps_position.satellites_used` 或 `gps_satellites` | `gps_satellites` |
| `vehicle_gps_position.hdop` 或 `eph` | `gps_hdop` |
| `vehicle_imu_status.accel_vibration_metric` | `vibration_x` |
| `vehicle_imu_status.gyro_vibration_metric` | `vibration_y` |
| `vehicle_imu_status.delta_angle_coning_metric` | `vibration_z` |
| `actuator_outputs.outputs` 或 `output_0..3` | `motor_1_output` 到 `motor_4_output` |
| `telemetry_status.link_quality_pct` 或 `rssi` | `link_quality_pct` |
| `sensor_combined.temperature_c` 或 `temperature` | `temperature_c` |

### PX4 缺失数据行为

- 缺少 required topic：阻断错误，指出 topic 和文件路径。
- topic 存在但没有可用样本：阻断错误，指出 topic 和文件路径。
- 样本缺少 required field：阻断错误，指出 field、sample index 和文件路径。
- 缺少 `pyulog`：清晰提示 `pip install -e .[px4]`，不显示 traceback。

### PX4 metadata

真实 ULog parser metadata 包含：

- `mock_fixture=false`
- `topics_used`
- `sample_count`
- `safety_boundary=offline-read-only`

mock ULog parser metadata 包含：

- `mock_fixture=true`
- `topics_used`
- `safety_boundary=offline-read-only`

## ArduPilot BIN 覆盖范围

ArduPilot BIN 有两条路径：

- mock fixture：`data/sample_logs/example_ardupilot.bin`
- 真实/脱敏 DataFlash：本地 `.bin` 文件，通过可选依赖 `pymavlink` 解析

真实 BIN 解析需要：

```bash
pip install -e .[ardupilot]
```

### ArduPilot 字段映射

| DataFlash message / field | 标准字段 |
| --- | --- |
| `MODE.Mode` 或 `MODE.ModeNum` | `flight_mode` |
| `GPS.Alt`、`GPS.RelAlt` 或 `GPS.HAGL` | `altitude_m` |
| `GPS.NSats` 或 `GPS.Sats` | `gps_satellites` |
| `GPS.HDop` 或 `GPS.HDOP` | `gps_hdop` |
| `BAT.Volt` 或 `BAT.VoltR` | `battery_voltage_v` |
| `BAT.Curr` 或 `BAT.CurrTot` | `battery_current_a` |
| `BAT.RemPct` 或 `BAT.SoC` | `battery_soc_pct` |
| `BAT.Temp` 或 `BAT.Temp2` | `temperature_c` |
| `VIBE.VibeX` / `VibeY` / `VibeZ` | `vibration_x` / `vibration_y` / `vibration_z` |
| `RCOU.C1..C4` | `motor_1_output` 到 `motor_4_output` |
| 尚未从 DataFlash 稳定映射 | `link_quality_pct` 默认 100，并记录 warning |

### ArduPilot 缺失数据行为

- 空文件：阻断错误。
- mock fixture JSON 无效：阻断错误，指出 fixture。
- mock record 缺少标准字段：阻断错误，指出记录序号和字段。
- 没有可用 DataFlash snapshot：阻断错误，指出文件。
- 缺少 `pymavlink`：清晰提示 `pip install -e .[ardupilot]`，不显示 traceback。
- `link_quality_pct` 真实 DataFlash 映射尚未支持，当前显式记录为默认值。

### ArduPilot metadata

真实 BIN parser metadata 包含：

- `mock_fixture=false`
- `messages_used`
- `messages_consumed`
- `snapshot_count`
- `safety_boundary=offline-read-only`

mock BIN parser metadata 包含：

- `mock_fixture=true`
- `record_count`
- `safety_boundary=offline-read-only`

## Evidence refs 与 audit metadata

`analyze-log` audit JSON 记录：

- requested format
- actual format
- parser name
- parser version
- parser warnings
- source metadata
- parser metadata

`flight_summary.json` 和每条 anomaly 必须保留 `evidence_refs`。证据引用必须能追溯到 source log id、规范化字段、测量值、阈值和 rule id。

## Fixture policy

真实或脱敏日志样例策略见 `data/sample_logs/README.md`。格式专用 placeholder 目录为：

- `data/sample_logs/px4/`
- `data/sample_logs/ardupilot/`

当前测试套件在没有真实 `.ulg` / `.bin` 文件时也必须通过。真实 fixture 不存在时，相关测试会 skip 并指向对应 README。

## 当前限制

- PX4 ULog 映射是最小可用覆盖，不覆盖全部 ULog topic。
- ArduPilot BIN 映射是最小可用覆盖，不覆盖全部 DataFlash message。
- 真实 ArduPilot DataFlash 的 `link_quality_pct` 还没有稳定映射。
- 默认安装和 `.[dev]` 不安装 `pyulog` 或 `pymavlink`。
- 真实/脱敏 fixture 必须先完成来源、授权、体积和隐私检查，才能提交。

# 日志格式与 SITL 集成契约设计

日期：2026-06-25

## 目标

本设计用于协调后续三个并行开发方向：

- PX4 ULog 离线解析支持。
- ArduPilot BIN 离线解析支持。
- SITL 仿真结果导入与验证。

本阶段只定义共享接口、数据流、CLI 命名、依赖边界、错误处理和并行协作规则，不实现具体解析器或仿真验证逻辑。后续三个 agent 必须以本契约为边界独立开发，最终由集成 agent 统一合并。

## 安全边界

项目仍然是离线 advisory-only 无人机运维 Agent。任何新增能力都只能用于日志分析、仿真结果导入、风险评估、报告生成和人工复核辅助。

禁止新增以下能力：

- 连接真实无人机硬件。
- arm/disarm。
- 解锁或启动电机。
- 起飞、降落、返航。
- 航线执行或任务下发。
- 固件上传。
- 飞控参数写入。
- MAVLink command execution。

PX4 ULog、ArduPilot BIN 和 SITL validation 都不能自动批准真实飞行或维护动作。任何飞行安全、维护安全或仿真风险相关输出必须保留 `human_review_required=true`。

## 当前系统约束

现有 `analyze-log` 流程是：

1. `apps/cli/main.py` 读取 `--log` 和 `--asset`。
2. `packages.log_parsers.parse_flight_log` 读取 CSV 或 JSON。
3. 输出 `list[FlightLogRecord]`。
4. `packages.telemetry_rules.summarize_flight` 生成 `FlightLogSummary`。
5. `packages.anomaly_detection.detect_anomalies` 生成 `list[AnomalyEvent]`。
6. CLI 写出 `flight_summary.json`、`anomalies.json` 和 `audit/*.json`。

后续扩展必须保持现有 CSV / JSON 行为兼容，`run-mvp` 默认路径和输出文件名不得变化。

## 统一日志解析器接口

新增共享接口建议放在：

```text
packages/log_parsers/base.py
```

推荐定义：

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from packages.drone_schemas import FlightLogRecord


@dataclass(frozen=True)
class ParsedFlightLog:
    records: list[FlightLogRecord]
    source_log_id: str
    parser_name: str
    parser_version: str
    warnings: list[str]


class FlightLogParser(Protocol):
    name: str
    version: str
    supported_formats: tuple[str, ...]

    def can_parse(self, path: Path, requested_format: str = "auto") -> bool:
        ...

    def parse(self, path: Path) -> ParsedFlightLog:
        ...
```

约定：

- `source_log_id` 默认使用输入文件名，例如 `example_flight.csv`。
- `parser_name` 使用稳定短名，例如 `csv-json-flight-log`、`px4-ulog`、`ardupilot-bin`。
- `parser_version` 独立于 skill version，解析器行为变化时递增。
- `warnings` 用于记录字段缺失但可降级、样例 mock 数据限制、依赖版本提示等非阻断信息。
- `parse` 不写文件，不执行 anomaly rules，不写 audit，只返回规范化记录。

## LogParserAdapter 注册与选择

新增适配器注册建议放在：

```text
packages/log_parsers/registry.py
```

推荐提供：

```python
SUPPORTED_LOG_FORMATS = ("auto", "csv", "json", "px4-ulog", "ardupilot-bin")


def parse_flight_log(path: Path, requested_format: str = "auto") -> ParsedFlightLog:
    ...
```

兼容要求：

- `parse_flight_log(path)` 继续可用。
- 对旧调用方，可额外提供 `parse_flight_log_records(path)` 或保持 `parse_flight_log(path).records` 的迁移层。
- 最终集成时由集成 agent 决定是否一次性迁移现有调用点。

格式选择规则：

- `--format auto` 根据扩展名和解析器 `can_parse` 决定。
- `.csv` -> `csv`
- `.json` -> `json`
- `.ulg` -> `px4-ulog`
- `.bin` -> `ardupilot-bin`
- 格式不匹配时给出清晰错误，例如：`错误: log format px4-ulog cannot parse file: sample.bin`
- 自动识别失败时列出支持格式和文件路径，不显示 traceback。

## CSV / JSON / ULog / BIN 统一输出

所有日志格式必须统一输出现有模型：

- `FlightLogRecord`
- `FlightLogSummary`
- `AnomalyEvent`

解析器只负责把源格式映射为 `FlightLogRecord`。摘要和异常检测继续由现有 `summarize_flight` 与 `detect_anomalies` 负责，避免每种格式重复实现规则逻辑。

字段映射原则：

- 时间戳必须转换为 timezone-aware `datetime`。
- 电池、电流、SOC、GPS、HDOP、振动、电机输出、链路质量和温度必须落到现有字段。
- 源日志缺少字段时，解析器可以使用受控默认值，但必须在 `ParsedFlightLog.warnings` 记录原因。
- 如果缺少生成有效 `FlightLogRecord` 的关键字段，解析器必须失败并给出清晰错误。
- 禁止在解析器中直接生成维护建议或诊断结论。

证据链要求：

- `FlightLogSummary.evidence_refs` 必须能追溯到输入日志路径、字段和 parser。
- `AnomalyEvent.evidence_refs` 继续由 anomaly rules 生成，但 `source_id` 应使用 `ParsedFlightLog.source_log_id`。
- 对 ULog / BIN 的 mock fixture，证据引用也必须指向 fixture 文件和规范化字段，不得只写“mock data”。

## PX4 ULog 适配器契约

Agent A 只负责离线 `.ulg` 解析适配器。

建议新增：

```text
packages/log_parsers/px4_ulog.py
```

契约：

- 只能读取本地 `.ulg` 文件。
- 不连接 PX4、SITL 或真实飞控。
- 不执行 MAVLink command。
- 不写入参数、不上传固件。
- 可使用可选依赖解析真实 ULog；若依赖缺失，CLI 必须提示安装方式或说明当前只支持 mock fixture。
- 小型 fixture 可以是最小 JSON mock 或经过脱敏的小文本 fixture，但不得提交大体积真实日志。
- 解析器输出必须是 `ParsedFlightLog`。

推荐依赖策略：

- 不把 PX4 ULog 解析库放入主依赖，优先放入 optional extra，例如 `px4 = [...]`。
- 没有依赖时抛出项目自定义 `LogParserDependencyError` 或 `ValueError`，由 CLI 转成用户友好错误。

## ArduPilot BIN 适配器契约

Agent B 只负责离线 `.bin` 解析适配器。

建议新增：

```text
packages/log_parsers/ardupilot_bin.py
```

契约：

- 只能读取本地 `.bin` 文件。
- 不连接 ArduPilot、SITL 或真实飞控。
- 不执行 MAVLink command。
- 不写入参数、不上传固件。
- 可使用可选依赖解析真实 BIN；若依赖缺失，CLI 必须提示安装方式或说明当前只支持 mock fixture。
- 小型 fixture 可以是最小 mock 或脱敏样例，不得提交大体积真实日志。
- 解析器输出必须是 `ParsedFlightLog`。

推荐依赖策略：

- 不把 BIN 解析库放入主依赖，优先放入 optional extra，例如 `ardupilot = [...]`。
- 依赖缺失、字段缺失、日志为空时都必须是清晰 CLI 错误。

## SITL 仿真验证契约

Agent C 的 MVP 不直接运行完整 SITL，而是实现“仿真结果导入与验证”。

建议新增：

```text
packages/simulation/result_parser.py
packages/simulation/validation.py
```

输入模型复用：

- `MissionPlan`
- `SimulationScenario`
- `SimulationRun`
- `EvidenceRef`
- `SkillRunAudit`

建议输入文件：

```text
data/sample_simulation/example_simulation_result.json
```

推荐 CLI：

```bash
drone-ops validate-simulation --scenario <path> --result <path> --out <dir>
```

输出：

```text
simulation_run.json
audit/*.json
```

验证逻辑：

- 读取 scenario 和 exported simulation result。
- 验证 mission constraints、失败事件、偏航/高度/航迹偏差、failsafe、超时、能量余量等离线结果字段。
- 输出 `SimulationRun.status`，建议限定为 `PASS`、`FAIL`、`REVIEW_REQUIRED`。
- 任何 `FAIL` 或 `REVIEW_REQUIRED` 必须 `human_review_required=true`。
- `PASS` 也必须说明这是离线仿真结果，不代表真实飞行授权。
- 所有结论必须包含 `evidence_refs`。
- 每次运行必须写 audit JSON。

报告集成：

- 最终集成 agent 负责让 `ops_report.md` 和 PDF 报告可选包含 simulation validation section。
- 如果没有 simulation result，现有报告章节和 run-mvp 不应变化。

## CLI 命名与兼容性

最终推荐 CLI：

```bash
drone-ops analyze-log --log <path> --asset <path> --out <dir> --format auto
drone-ops analyze-log --log <path> --asset <path> --out <dir> --format csv
drone-ops analyze-log --log <path> --asset <path> --out <dir> --format json
drone-ops analyze-log --log <path> --asset <path> --out <dir> --format px4-ulog
drone-ops analyze-log --log <path> --asset <path> --out <dir> --format ardupilot-bin
drone-ops validate-simulation --scenario <path> --result <path> --out <dir>
```

兼容要求：

- `--format` 默认值必须是 `auto`。
- 现有不带 `--format` 的 `analyze-log` 和 `run-mvp` 必须继续可用。
- `run-mvp` 不要求支持 ULog / BIN；它只需继续处理现有 CSV / JSON 样例。
- `python -m apps.cli.main ...` 与 `drone-ops ...` 都必须保持一致。

## 并行 agent 不应同时修改的共享文件

三个并行 agent 应避免同时修改以下文件，除非契约明确分配：

- `apps/cli/main.py`
- `packages/log_parsers/__init__.py`
- `packages/log_parsers/base.py`
- `packages/log_parsers/registry.py`
- `packages/drone_schemas/models.py`
- `packages/report_templates/markdown.py`
- `README.md`
- `docs/data_contracts.md`
- `docs/codex_workflows.md`
- `skills/flight-log-analysis/SKILL.md`
- `skills/simulation-validation/SKILL.md`
- `.github/workflows/ci.yml`

建议分工：

- Agent A 可新增 `packages/log_parsers/px4_ulog.py` 和 PX4 专属测试、fixture、说明草稿。
- Agent B 可新增 `packages/log_parsers/ardupilot_bin.py` 和 BIN 专属测试、fixture、说明草稿。
- Agent C 可新增 `packages/simulation/*`、simulation fixture、simulation tests，并更新 simulation skill 草稿。
- 最终集成 agent 统一修改 CLI、registry、README、CI、报告模板和共享 skill 文档。

## 最终集成 agent 职责

集成分支：

```text
feat/integrate-log-and-sitl-modules
```

集成 agent 负责：

1. 从三个功能分支 cherry-pick 或 merge 已 review 的变更。
2. 解决共享文件冲突。
3. 定稿 `FlightLogParser` / `LogParserAdapter` 接口。
4. 统一 `parse_flight_log` 返回值和旧调用兼容层。
5. 统一 `analyze-log --format` 行为。
6. 统一 `validate-simulation` CLI。
7. 统一错误信息格式。
8. 更新 README、docs、skills。
9. 更新 release notes 草稿，但不创建 tag。
10. 更新 CI smoke test，覆盖 CSV / JSON / ULog mock / BIN mock / simulation mock。
11. 运行完整 `pytest`。
12. 回归 `run-mvp`、`preflight-check`、`monitor-replay`、`export-pdf`。

## 依赖管理

新依赖必须满足：

- 可选、可解释、可测试。
- 不因没有安装 PX4 / ArduPilot 解析库而破坏现有 CSV / JSON / run-mvp。
- 不要求用户安装 GUI、浏览器、真实飞控工具链或 SITL 环境。
- 不把大体积日志样例作为依赖或 fixture。

推荐 extras：

```toml
[project.optional-dependencies]
px4 = ["<ulog-parser-lib>"]
ardupilot = ["<bin-parser-lib>"]
simulation = []
dev = [...]
```

如果解析器依赖缺失，错误信息必须包含：

- 缺失依赖名称。
- 当前命令无法解析的格式。
- 建议安装 extra 的命令，例如 `pip install -e .[px4]`。
- 明确说明系统不会连接真实无人机或执行控制命令。

## 错误处理契约

CLI 必须捕获并转成清晰错误：

- 输入文件不存在。
- 日志为空。
- 格式不支持。
- `--format` 与文件不匹配。
- 必要字段缺失。
- JSON / CSV / mock fixture 格式错误。
- ULog / BIN 可选依赖缺失。
- 仿真 scenario 或 result schema 无效。

错误输出不得包含 Python traceback。测试必须覆盖缺失文件、依赖缺失、空日志和字段缺失。

## 测试契约

每个 agent 至少添加：

- 解析器单元测试。
- CLI 集成测试。
- 错误信息测试。
- evidence_refs 测试。
- 安全边界关键词扫描或契约测试。

最终集成测试必须覆盖：

- CSV `analyze-log --format auto`。
- JSON `analyze-log --format auto`。
- PX4 mock `analyze-log --format px4-ulog`。
- ArduPilot mock `analyze-log --format ardupilot-bin`。
- `validate-simulation` mock/offline flow。
- `run-mvp` 兼容旧用法。
- Markdown / PDF 报告不回归。

## 审计与证据链

新增 skill run 必须写 audit JSON：

- `flight-log-analysis` audit 需要记录 parser name、parser version、requested format、actual format。
- `simulation-validation` audit 需要记录 scenario、result、rules triggered、output refs、human_review_required 和 status。

新增输出必须包含可追溯证据：

- ULog / BIN anomaly evidence 必须指向源日志、字段、测量值、阈值、rule id。
- SimulationRun evidence 必须指向 scenario、result 字段、测量值、阈值或判定规则。

## 验收标准

第一阶段完成标准：

- 本 spec 写入 `docs/superpowers/specs/2026-06-25-log-formats-and-sitl-integration.md`。
- 不实现功能代码。
- 不创建并行 agent 分支。
- 不修改已有 tag 或 release。
- 等待用户确认后，再进入第二阶段。

最终整合完成标准：

- `pytest` 全部通过。
- 原有 v0.4.0 功能不回归。
- CSV / JSON 样例日志仍可完成 `run-mvp`。
- PDF 报告仍可生成。
- ULog / BIN 支持有测试覆盖。
- SITL validation 支持 mock/offline 流程。
- 所有新增输出都有 `evidence_refs`。
- 所有新增 skill run 都写 audit JSON。
- 所有安全相关建议 `human_review_required=true`。
- 没有真实无人机控制代码。
- 没有 MAVLink command execution。
- 没有 arm/disarm/takeoff/land/RTL/mission execution/firmware upload/parameter write 等能力。
- GitHub Actions 通过。


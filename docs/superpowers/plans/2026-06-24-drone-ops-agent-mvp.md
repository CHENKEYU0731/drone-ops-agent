# 无人机运维 Agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个离线可运行、可测试、可审计的无人机运维 Agent CLI MVP。

**Architecture:** 采用 Python 包 + Typer CLI 的离线架构。领域对象集中在 `packages/drone_schemas`，日志解析、异常检测、诊断、维护建议、报告和审计分别由独立包负责，CLI 只做编排和文件读写。

**Tech Stack:** Python 3.11+、Pydantic、Typer、pytest、Markdown。

---

## 文件结构

- 创建 `pyproject.toml`：定义包元数据、依赖、CLI 入口和 pytest 配置。
- 创建 `README.md`：中文说明项目用途、安全边界、安装、运行、测试、skill 扩展和审计日志。
- 创建 `docs/architecture.md`、`docs/safety_policy.md`、`docs/audit_policy.md`、`docs/data_contracts.md`、`docs/codex_workflows.md`、`docs/roadmap.md`：中文项目文档。
- 创建 `apps/cli/main.py` 和 `apps/cli/__init__.py`：Typer 命令和工作流编排。
- 创建 `packages/drone_schemas/models.py`、`packages/drone_schemas/io.py`、`packages/drone_schemas/__init__.py`：Pydantic 模型和 JSON 读写。
- 创建 `packages/log_parsers/parser.py`、`packages/log_parsers/__init__.py`：CSV/JSON 日志解析。
- 创建 `packages/telemetry_rules/summary.py`、`packages/telemetry_rules/__init__.py`：飞行摘要计算。
- 创建 `packages/anomaly_detection/rules.py`、`packages/anomaly_detection/__init__.py`：异常检测规则。
- 创建 `packages/diagnosis_rules/rules.py`、`packages/diagnosis_rules/__init__.py`：故障诊断规则。
- 创建 `packages/maintenance_rules/rules.py`、`packages/maintenance_rules/__init__.py`：维护建议规则。
- 创建 `packages/report_templates/markdown.py`、`packages/report_templates/__init__.py`：Markdown 报告渲染。
- 创建 `packages/audit_logger/logger.py`、`packages/audit_logger/__init__.py`：审计日志创建和写入。
- 创建 `packages/simulation/__init__.py`：仿真扩展占位包。
- 创建 `agents/*/README.md`：中文说明各 agent 职责边界。
- 创建 `skills/*/SKILL.md`、`skills/*/schema.json`、`skills/*/examples/.gitkeep`、`skills/*/tests/.gitkeep`：中文 skill 契约和 schema。
- 创建 `data/sample_assets/uav_001.json`、`data/sample_logs/example_flight.csv`、`data/sample_logs/example_flight.json`、`data/sample_missions/example_mission.json`、`data/sample_reports/.gitkeep`：样例数据。
- 创建 `evals/cases/.gitkeep`、`evals/expected_outputs/.gitkeep`、`evals/scoring/.gitkeep`：评估目录骨架。
- 创建 `tests/unit/*`、`tests/integration/*`、`tests/golden/*`：覆盖 schema、解析、规则、报告、审计和完整 MVP。

## Task 1: 项目骨架和中文文档

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/safety_policy.md`
- Create: `docs/audit_policy.md`
- Create: `docs/data_contracts.md`
- Create: `docs/codex_workflows.md`
- Create: `docs/roadmap.md`
- Create: `agents/*/README.md`
- Create: `evals/*/.gitkeep`

- [ ] **Step 1: 创建项目元数据和依赖**

写入 `pyproject.toml`，声明 `pydantic`、`typer`、`pytest`，并配置 `drone-ops = "apps.cli.main:app"`。

- [ ] **Step 2: 创建中文 README**

写入项目用途、安全边界、安装方式、MVP 命令、测试命令、添加 skill 和查看审计日志的方法。

- [ ] **Step 3: 创建中文 docs**

写入架构、安全、审计、数据契约、Codex 后续任务和路线图文档。

- [ ] **Step 4: 创建 agent 和 evals 目录**

为每个 agent 写中文职责说明；为 evals 三个子目录添加 `.gitkeep`。

- [ ] **Step 5: 验证骨架文件存在**

Run: `Get-ChildItem -Recurse -File | Select-Object FullName`
Expected: 能看到 pyproject、README、docs、agents 和 evals 文件。

## Task 2: Pydantic 领域模型和 JSON 工具

**Files:**
- Create: `packages/drone_schemas/models.py`
- Create: `packages/drone_schemas/io.py`
- Create: `packages/drone_schemas/__init__.py`
- Test: `tests/unit/test_schemas.py`

- [ ] **Step 1: 写 schema 测试**

测试 `DroneAsset`、`FlightLogRecord`、`AnomalyEvent`、`FaultHypothesis`、`MaintenanceRecommendation`、`SkillRunAudit` 的关键字段和验证行为。

- [ ] **Step 2: 实现 Pydantic 模型**

定义 Severity、MaintenancePriority 等枚举，以及需求中的全部领域对象。重要输出对象统一包含 id、timestamp、evidence refs、human_review_required、generated_by_skill、skill_version。

- [ ] **Step 3: 实现 JSON 工具**

提供 `read_json_file(path)`、`write_model(path, model)`、`write_model_list(path, models)` 和 `load_model(path, model_type)`。

- [ ] **Step 4: 运行 schema 测试**

Run: `pytest tests/unit/test_schemas.py -v`
Expected: PASS。

## Task 3: 样例数据、日志解析和摘要

**Files:**
- Create: `data/sample_assets/uav_001.json`
- Create: `data/sample_logs/example_flight.csv`
- Create: `data/sample_logs/example_flight.json`
- Create: `data/sample_missions/example_mission.json`
- Create: `packages/log_parsers/parser.py`
- Create: `packages/log_parsers/__init__.py`
- Create: `packages/telemetry_rules/summary.py`
- Create: `packages/telemetry_rules/__init__.py`
- Test: `tests/unit/test_log_parsing.py`

- [ ] **Step 1: 写解析和摘要测试**

测试 CSV/JSON 都能解析为 `FlightLogRecord`，摘要能计算飞行时长、最低电压、最大电流、最低 SOC、GPS、振动、电机不平衡、链路和模式切换。

- [ ] **Step 2: 创建样例数据**

创建包含正常段和异常段的日志，让规则能触发低 SOC、高电流、GPS 下降、高振动、电机不平衡、链路下降、高温和非预期模式切换。

- [ ] **Step 3: 实现日志解析器**

根据扩展名选择 CSV 或 JSON 解析；字段缺失时抛出包含字段名的 `ValueError`。

- [ ] **Step 4: 实现摘要计算**

根据记录列表生成 `FlightLogSummary`，包括模式切换 timeline 和各类指标摘要。

- [ ] **Step 5: 运行解析测试**

Run: `pytest tests/unit/test_log_parsing.py -v`
Expected: PASS。

## Task 4: 异常检测规则

**Files:**
- Create: `packages/anomaly_detection/rules.py`
- Create: `packages/anomaly_detection/__init__.py`
- Test: `tests/unit/test_anomaly_detection.py`

- [ ] **Step 1: 写异常检测测试**

测试至少触发电压骤降、低 SOC、高电流、GPS 质量下降、HDOP 过高、卫星数过低、高振动、电机不平衡、链路下降、高温和非预期模式切换。

- [ ] **Step 2: 实现规则常量和 evidence 构造**

每条规则固定 rule id、阈值、严重级别和 evidence refs。

- [ ] **Step 3: 实现 `detect_anomalies(records)`**

返回按 timestamp 和 anomaly id 排序的确定性 `AnomalyEvent` 列表。

- [ ] **Step 4: 运行异常测试**

Run: `pytest tests/unit/test_anomaly_detection.py -v`
Expected: PASS。

## Task 5: 诊断规则和维护建议

**Files:**
- Create: `packages/diagnosis_rules/rules.py`
- Create: `packages/diagnosis_rules/__init__.py`
- Create: `packages/maintenance_rules/rules.py`
- Create: `packages/maintenance_rules/__init__.py`
- Test: `tests/unit/test_diagnosis_and_maintenance.py`

- [ ] **Step 1: 写诊断和维护测试**

测试诊断按 confidence 降序输出多个假设，并且维护建议包含证据、优先级、审批要求和人工复核。

- [ ] **Step 2: 实现诊断规则**

将异常类型映射到桨叶/动平衡、电机、电池、GPS、传感器振动、通信链路和热异常假设。

- [ ] **Step 3: 实现维护建议规则**

根据故障假设生成可读动作，优先级覆盖 `IMMEDIATE_GROUNDING`、`BEFORE_NEXT_FLIGHT`、`POST_FLIGHT_INSPECTION`、`SCHEDULED_MAINTENANCE` 和 `MONITOR`。

- [ ] **Step 4: 运行诊断维护测试**

Run: `pytest tests/unit/test_diagnosis_and_maintenance.py -v`
Expected: PASS。

## Task 6: 审计日志和 Markdown 报告

**Files:**
- Create: `packages/audit_logger/logger.py`
- Create: `packages/audit_logger/__init__.py`
- Create: `packages/report_templates/markdown.py`
- Create: `packages/report_templates/__init__.py`
- Test: `tests/unit/test_audit_and_report.py`

- [ ] **Step 1: 写审计和报告测试**

测试审计 JSON 包含 skill name、version、input/output refs、tools called、rules triggered、timestamp、human review 和 status。测试报告包含 11 个指定章节和证据附录。

- [ ] **Step 2: 实现审计写入**

生成 `SkillRunAudit` 并写入 `audit/<skill-name>-<run-id>.json`。

- [ ] **Step 3: 实现 Markdown 报告生成**

渲染执行摘要、飞行概况、资产概况、关键指标、异常时间线、故障假设、维护建议、安全说明、人工复核要求、审计记录和证据引用附录。

- [ ] **Step 4: 运行审计报告测试**

Run: `pytest tests/unit/test_audit_and_report.py -v`
Expected: PASS。

## Task 7: CLI 编排和完整 MVP

**Files:**
- Create: `apps/cli/main.py`
- Create: `apps/cli/__init__.py`
- Test: `tests/integration/test_cli_workflow.py`
- Test: `tests/golden/test_mvp_flow.py`

- [ ] **Step 1: 写 CLI 集成测试**

使用 Typer CliRunner 测试 `analyze-log`、`diagnose`、`generate-report` 和 `run-mvp` 能生成期望文件。

- [ ] **Step 2: 实现 `analyze-log`**

读取日志和资产，生成 summary、anomalies 和 audit。

- [ ] **Step 3: 实现 `diagnose`**

读取 summary、同目录 anomalies 和资产，生成 diagnosis、maintenance 和 audit。

- [ ] **Step 4: 实现 `generate-report`**

读取 summary、diagnosis、maintenance、asset 和 anomalies，生成 Markdown 报告和 audit。

- [ ] **Step 5: 实现 `run-mvp`**

串联完整流程，输出所有要求文件。

- [ ] **Step 6: 运行 CLI 和 golden 测试**

Run: `pytest tests/integration tests/golden -v`
Expected: PASS。

## Task 8: Skill 目录契约和 schema

**Files:**
- Create: `skills/preflight-check/SKILL.md`
- Create: `skills/state-monitoring/SKILL.md`
- Create: `skills/flight-log-analysis/SKILL.md`
- Create: `skills/fault-diagnosis/SKILL.md`
- Create: `skills/maintenance-advisor/SKILL.md`
- Create: `skills/simulation-validation/SKILL.md`
- Create: `skills/ops-report-generation/SKILL.md`
- Create: `skills/*/schema.json`
- Create: `skills/*/examples/.gitkeep`
- Create: `skills/*/tests/.gitkeep`
- Test: `tests/unit/test_skill_contracts.py`

- [ ] **Step 1: 写 skill 合同测试**

测试每个 skill 目录都有 `SKILL.md`、`schema.json`、`examples/` 和 `tests/`，且 `SKILL.md` 包含指定章节。

- [ ] **Step 2: 创建中文 SKILL.md**

为 4 个 MVP skill 写具体可执行流程，为 3 个后续 skill 写结构完整 skeleton。

- [ ] **Step 3: 创建 schema.json**

为每个 skill 写输入输出 schema 概览，引用 Pydantic 模型名和关键字段。

- [ ] **Step 4: 运行 skill 合同测试**

Run: `pytest tests/unit/test_skill_contracts.py -v`
Expected: PASS。

## Task 9: 全量验证和收尾

**Files:**
- Modify: `README.md`
- Modify: `docs/*.md`
- Modify: `docs/superpowers/specs/2026-06-24-drone-ops-agent-design.md`

- [ ] **Step 1: 运行全量测试**

Run: `pytest`
Expected: PASS。

- [ ] **Step 2: 运行 CLI MVP**

Run: `python -m apps.cli.main run-mvp --log data/sample_logs/example_flight.csv --asset data/sample_assets/uav_001.json --out data/sample_reports`
Expected: 生成 summary、anomalies、diagnosis、maintenance、ops_report 和 audit JSON 文件。

- [ ] **Step 3: 检查 Markdown 语言**

Run: `Get-ChildItem -Recurse -Filter *.md | Select-Object FullName`
Expected: 项目 `.md` 文件为中文正文，代码标识符和命令可保留英文。

- [ ] **Step 4: 检查安全边界**

Run: `rg -n "arm|disarm|takeoff|land|rtl|return-to-home|upload firmware|MAV_CMD|motor start|unlock" .`
Expected: 只在安全边界文档中作为禁止项出现，不作为可执行控制逻辑出现。

- [ ] **Step 5: 提交实现**

使用 commit 技能规则提交代码，提交信息建议：

```bash
git add .
git commit -m "feat: Add offline drone ops agent MVP" -m "Build the CLI workflow, schemas, deterministic rules, reports, audit logging, sample data, tests, and Chinese documentation for the drone operations support MVP.

Co-Authored-By: Codex <noreply@openai.com>"
```

## 自检

- Spec 覆盖：计划覆盖项目骨架、中文文档、schema、日志解析、异常检测、诊断、维护建议、报告、审计、CLI、skill 目录、样例数据和测试。
- 占位扫描：计划中没有 TBD/TODO/待补充；所有后续扩展都明确为范围外或 skeleton。
- 类型一致性：计划统一使用 `FlightLogSummary`、`AnomalyEvent`、`FaultHypothesis`、`MaintenanceRecommendation`、`SkillRunAudit` 等模型名。

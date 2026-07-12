# 路线图

项目当前已发布到 `v2.0.0 - Offline Operations Platform Baseline`。

详细规划见：

- `docs/planning/v0.8-to-v2.0-roadmap.md`

## 已完成

- `v0.6.0 - Real Sample Log Validation`
  - 增强日志 parser coverage、sample fixture policy 和真实/脱敏样例边界说明。
  - 不提交未经确认的真实 `.ulg` / `.bin` 二进制样例。
- `v0.7.0 - Quality Gate Baselines`
  - 增强 `validate-report`、`evidence_index.json` 和 `report_validation.json`。
  - 增加 offline/mock simulation scenario matrix。
  - 增加 `validate-simulation` operational rules 和 `rule_results`。
- `v0.8.0 - Report Integration Plus`
  - 将仿真验证、审计摘要、parser metadata 和人工复核清单纳入 Markdown/PDF 报告。
- `v0.9.0 - Work Order Drafts`
  - 增加工单草稿生成、工单草稿验证和报告中的工单章节。
- `v1.0.0 - Stable Offline Ops Agent`
  - 冻结核心 CLI、schema、audit、证据链和安全边界。
- `v1.1.0` 至 `v1.4.0`
  - 完成机队健康分析、本地只读 Dashboard、规则包版本管理和诊断/报告评测。
- `v1.5.0` 至 `v1.9.0`
  - 完成平台 readiness、dataset registry、offline adapter/approval、organization handoff 和 readiness index。
- `v2.0.0 - Offline Operations Platform Baseline`
  - 将已完成能力收成可验证的组织级离线运维决策平台基线。

## 当前里程碑

### v2.0.0：Offline Operations Platform Baseline

目标已经完成：项目具备 CLI、本地只读 Web Dashboard、多资产分析、报告和工单闭环、规则与评测、审计、审批、交接及平台质量门禁，同时继续保持 offline-only、advisory-only 和 human-review-required。

## 已完成版本演进

- `v0.9.0`：工单草稿闭环。
- `v1.0.0`：稳定离线运维 Agent 主版本。
- `v1.1.0`：机队健康趋势分析。
- `v1.2.0`：本地 Web Dashboard MVP。
- `v1.3.0`：规则包和 skill 版本管理。
- `v1.4.0`：诊断与报告评测。
- `v1.5.x`：平台化准备。
- `v2.0.0`：组织级离线运维平台基线。

## 安全边界

所有阶段默认保持：

- offline-first。
- advisory-only。
- human review required。
- 不连接真实无人机。
- 不执行 MAVLink command。
- 不执行 arm/disarm、takeoff、landing、RTL、mission execution、motor start、firmware upload 或 flight-controller parameter writing。
- 不启动或连接真实 PX4、ArduPilot、Gazebo、SITL 或外部仿真器。

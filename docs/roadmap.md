# 路线图

项目当前已发布到 `v0.9.0 - Work Order Drafts`。

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

## 下一阶段

### v1.0.0：Stable Offline Ops Agent

目标：冻结并稳定从 `v0.1.0` 到 `v0.9.0` 的完整离线能力，形成第一个可靠主版本。

建议拆成小 PR：

1. 稳定合同盘点：CLI、JSON 输出、schema、audit 和安全边界。
2. 安全边界回归测试：集中验证没有真实飞控、仿真器或维修系统接入。
3. v1.0.0 release readiness：完整 CLI / 报告 / 验证 / GitHub Actions 收口。

## 长期方向

- `v0.9.0`：工单草稿闭环。
- `v1.0.0`：稳定离线运维 Agent 主版本。
- `v1.1.0`：机队健康趋势分析。
- `v1.2.0`：本地 Web Dashboard MVP。
- `v1.3.0`：规则包和 skill 版本管理。
- `v1.4.0`：诊断与报告评测。
- `v1.5.x`：平台化准备。
- `v2.0.0`：组织级运维平台基线。

## 安全边界

所有阶段默认保持：

- offline-first。
- advisory-only。
- human review required。
- 不连接真实无人机。
- 不执行 MAVLink command。
- 不执行 arm/disarm、takeoff、landing、RTL、mission execution、motor start、firmware upload 或 flight-controller parameter writing。
- 不启动或连接真实 PX4、ArduPilot、Gazebo、SITL 或外部仿真器。

# 路线图

项目当前已发布到 `v0.7.0 - Quality Gate Baselines`。

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

## 下一阶段

### v0.8.0：Report Integration Plus

目标：让报告成为单次运维复盘材料，逐步纳入仿真结果、审计摘要、parser metadata、人工复核清单和 PDF 验证。

建议拆成小 PR：

1. `generate-report --simulation <simulation_run.json>`，Markdown 报告增加仿真验证章节。
2. 报告增加 audit summary、parser metadata 和 human review checklist。
3. PDF 输出同步验证新增章节。

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

# 路线图

项目当前版本为 `v2.4.0 - Reproducible Distribution`。

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
- `v2.1.0 - Demo and Portfolio Readiness`
  - 增加可重复生成的本地演示成果包、中文演示指南和更严格的平台验证门禁。
- `v2.2.0 - Evaluation and Case Study Baseline`
  - 用 14 个仿真场景和诊断/报告 golden case 量化预期状态准确率、证据覆盖率、误报与漏检。
- `v2.3.0 - Open-Source Upstream Log Compatibility`
  - 增加固定来源和校验和的公开上游 ULog 注册表、显式下载与离线 parser 兼容性案例研究。
- `v2.4.0 - Reproducible Distribution`
  - 增加环境诊断、直接依赖约束、Windows 临时环境验收、wheel/sdist smoke test 和确定性发布 ZIP。

## 当前里程碑

### v2.4.0：Reproducible Distribution

目标已经完成：项目可以在干净的 Windows 临时虚拟环境中按固定直接依赖安装、运行全量测试、生成演示成果、构建 wheel/sdist，并生成内容、顺序、时间戳和权限均稳定的发布 ZIP 与校验和。构建过程可能显式访问 Python 包索引，安装完成后的项目运行继续保持 offline-only、advisory-only 和 human-review-required。

## 已完成版本演进

- `v0.9.0`：工单草稿闭环。
- `v1.0.0`：稳定离线运维 Agent 主版本。
- `v1.1.0`：机队健康趋势分析。
- `v1.2.0`：本地 Web Dashboard MVP。
- `v1.3.0`：规则包和 skill 版本管理。
- `v1.4.0`：诊断与报告评测。
- `v1.5.x`：平台化准备。
- `v2.0.0`：组织级离线运维平台基线。
- `v2.1.0`：本地演示与作品展示就绪。
- `v2.2.0`：离线评测与案例研究基线。
- `v2.3.0`：公开上游日志兼容性案例研究。
- `v2.4.0`：可复现安装、构建与发布包基线。

## 安全边界

所有阶段默认保持：

- offline-first。
- advisory-only。
- human review required。
- 不连接真实无人机。
- 不执行 MAVLink command。
- 不执行 arm/disarm、takeoff、landing、RTL、mission execution、motor start、firmware upload 或 flight-controller parameter writing。
- 不启动或连接真实 PX4、ArduPilot、Gazebo、SITL 或外部仿真器。

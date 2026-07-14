# 简历与面试说明

## 中文简历描述

**drone-ops-agent｜离线无人机运维决策支持平台｜Python / Pydantic / Typer / ReportLab / Pytest**

- 设计并实现从本地飞行日志解析、异常检测、故障诊断、维护建议到 Markdown/PDF 报告和 DRAFT 工单的可追溯工作流，关键输出带 `evidence_refs`、audit 和人工复核标记。
- 建立报告、仿真、工单、数据集、适配器和平台 readiness 质量门禁；用 14 个 mock 仿真场景和 1 个诊断/报告 golden case 固化回归基线。
- 完成 PX4 ULog / ArduPilot BIN 离线适配、3 个固定来源上游 ULog 兼容性案例、机队健康汇总和本地只读 Dashboard，同时严格隔离真实控制与外部系统写操作。
- 建立 Windows clean-venv 验收、Python 3.11/3.12 CI、wheel/sdist smoke test、确定性源码 ZIP 与 SHA-256 发布链路。

## English Resume Version

**drone-ops-agent | Offline UAV Operations and Maintenance Decision-Support Platform | Python, Pydantic, Typer, ReportLab, Pytest**

- Built an evidence-linked workflow from offline log parsing and anomaly detection to diagnostic hypotheses, maintenance recommendations, PDF reports, audit records, and human-reviewed draft work orders.
- Implemented deterministic quality gates for reports, simulations, work orders, datasets, adapters, and platform readiness, backed by 14 mock simulation scenarios and one diagnosis/report golden case.
- Added offline PX4 ULog and ArduPilot BIN adapters, pinned upstream ULog compatibility cases, fleet health aggregation, and a local read-only dashboard while excluding real control and external write paths.
- Established clean-environment validation, Python 3.11/3.12 CI, wheel/sdist smoke tests, deterministic source bundles, and SHA-256 release verification.

## 60 秒项目介绍

“我做的是一个离线无人机运维决策支持平台。输入是本地 sample、mock、sanitized 或登记过来源的日志，输出包括异常、诊断、维护建议、PDF 报告、证据索引、审计和工单草稿。项目重点不是调用大模型生成一段文字，而是让每个结论都能回溯到结构化证据，并用质量门禁检查断裂引用、缺失章节和审核边界。我还为仿真规则、报告和平台能力建立了回归案例，并完成 clean venv、CI、wheel/sdist 和带校验和的发布流程。系统严格不连接真实无人机，也不执行任何 MAVLink 或维修系统写操作。”

## 常见追问

### 为什么坚持 offline-only？

当前没有经过授权和脱敏的真实业务数据，也没有真实飞控执行授权。离线边界可以让规则、schema、证据链和工程交付先被可靠验证，同时避免把作品演示误变成安全关键控制系统。

### 项目里的 Agent 体现在哪里？

Agent 体现在按职责拆分的日志分析、诊断、维护、报告、仿真和编排角色，以及它们之间的结构化输入输出契约。实现层使用确定性规则和 CLI 编排，避免在没有评测数据时把外部模型调用包装成不可验证的智能。

### 1.0 的案例指标意味着什么？

它只表示固定 golden/mock 案例的预期状态和证据覆盖全部匹配，用于防止规则回归。它不等于真实飞行故障检测准确率，也不能证明统计泛化。

### 最困难的工程问题是什么？

一是保持异常、诊断、建议、报告和 audit 的引用链完整；二是保证输出顺序和结构适合回归测试；三是在扩展 ULog、Dashboard、工单和平台能力时始终不越过真实控制和外部写操作边界。

### 下一步如何进入真实应用？

必须先获得授权并脱敏的真实日志，建立数据协议、标注方法、隐私审查和真实基准；随后只能先增加 read-only import 和 shadow evaluation。任何飞控命令或维修系统写操作都需要独立威胁建模、权限、审批、回滚和安全认证，不属于当前项目范围。

当前作品始终保持 offline-only、advisory-only，不连接真实无人机，不执行 MAVLink command，所有关键结论均需人工复核。

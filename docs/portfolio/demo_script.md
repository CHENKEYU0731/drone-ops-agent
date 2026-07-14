# 3–5 分钟项目演示脚本

## 演示前准备

```bash
python scripts/build_portfolio_showcase.py --out portfolio_showcase
```

准备打开：项目 README、`guides/项目总览.md`、`demo_outputs/reports/ops_report.pdf`、`demo_outputs/reports/evidence_index.json`、`demo_outputs/reports/simulation_run.json`、`demo_outputs/case_studies/case_study_report.md` 和 `demo_outputs/fleet/fleet_health_report.md`。

## 第 0–1 分钟：问题与定位

讲述：无人机运维输出常分散在日志、规则、报告和人工经验中。本项目把本地数据转换为可追溯的异常、诊断、维护建议、报告和审计材料。它是离线决策支持平台，不控制无人机，所有关键结论都需要人工复核。

展示：README 架构图和安全边界。

## 第 1–2 分钟：单次运维链路

展示：`ops_report.pdf` 的执行摘要、异常、诊断、维护建议、仿真验证和人工复核清单。

讲述：报告不是孤立文本；每个结论由结构化 JSON、证据引用和 audit 支撑。

## 第 2–3 分钟：证据链与质量门禁

展示：`evidence_index.json` 和 `report_validation.json`。

讲述：系统检查缺失引用、断裂引用、报告章节和 audit 覆盖。维护建议还可以生成 `DRAFT` 工单，但不会自动派单。

## 第 3–4 分钟：仿真、评测和上游日志

展示：`simulation_run.json`、`case_study_report.md`、`open_source_logs/registry_validation.json`。

讲述：14 个 mock 仿真场景覆盖四类状态，15 个固定案例用于回归评测。三个上游 ULog 只证明 parser 兼容，不能解释成真实飞行准确率。

## 第 4–5 分钟：机队与工程交付

展示：`fleet_health_report.md`、Dashboard 截图、`portfolio_manifest.json`。

讲述：项目从单次飞行扩展到多资产汇总、只读 Dashboard 和平台质量门禁；同时提供 clean venv、Python 3.11/3.12 CI、wheel/sdist、源码 ZIP 和 SHA-256，保证别人能够复现和检查。

## 收尾一句话

“这个项目的核心价值不是替人做飞行或维修决策，而是把离线运维分析变成有证据、有审计、有质量门禁、可人工复核的工程流程。”

演示全程保持 offline-only、advisory-only，不连接真实无人机，也不执行 MAVLink command。

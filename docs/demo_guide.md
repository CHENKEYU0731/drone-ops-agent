# 项目演示与示例成果包说明

这份文档用于帮助你和导师快速查看 `drone-ops-agent` 当前已经实现的能力。它面向作品展示和项目理解，不是答辩 PPT，也不是生产部署说明。

## 一键生成示例成果包

在项目根目录运行：

```bash
python scripts/generate_demo_outputs.py --out demo_outputs
```

该命令会重新生成 `demo_outputs/` 目录。它只读取仓库内的 sample / mock / sanitized fixture，并调用现有离线 CLI 流程，不连接真实无人机、真实仿真器、真实维修系统或真实 fleet platform。

## 推荐查看顺序

生成完成后，建议按下面顺序查看：

1. `demo_outputs/README.md`

   示例成果包自己的索引文件，概括了每类输出的用途。

2. `demo_outputs/reports/ops_report.md`

   单次运维任务的 Markdown 报告，包含飞行摘要、异常、诊断、维护建议、仿真验证、工单草稿和人工复核清单。

3. `demo_outputs/reports/ops_report.pdf`

   与 Markdown 报告对应的本地 PDF，适合直接发给导师快速查看效果。

4. `demo_outputs/reports/evidence_index.json`

   报告证据索引，用来说明异常、诊断、维护建议、audit 和报告文本之间如何互相追溯。

5. `demo_outputs/reports/report_validation.json`

   报告质量门禁结果，用来确认报告证据链、章节、audit 覆盖和引用关系是否完整。

6. `demo_outputs/reports/simulation_run.json`

   离线/mock 仿真验证结果，包含规则命中详情、风险结论、`evidence_refs` 和 `human_review_required=true`。

7. `demo_outputs/reports/work_order_drafts.md`

   从维护建议生成的本地工单草稿，便于展示“建议 -> 工单草稿 -> 人工复核”的闭环。

8. `demo_outputs/reports/work_order_validation.json`

   工单草稿质量门禁结果，用来确认工单草稿是否保留证据、来源建议、人工审批和 `DRAFT` 状态。

9. `demo_outputs/fleet/fleet_health_report.md`

   机队健康分析摘要，用来展示项目已经从单次飞行扩展到多资产、多任务趋势分析。

10. `demo_outputs/dashboard/dashboard_bundle.json`

    本地只读 dashboard 数据包，用来说明后续 Web 展示可以直接读取哪些结构化数据。

11. `demo_outputs/platform/platform_index_validation.json`

    v1.9.0 platform readiness index 验证结果，用来展示当前项目已完成能力的索引和质量门禁。

12. `demo_outputs/platform/operations_platform_validation.json`

    v2.0.0 operations platform baseline 验证结果，用来展示项目已经收成组织级离线运维平台基线。

## 这个成果包能展示什么

- 从飞行日志到异常、诊断、维护建议和报告的离线运维链路。
- 报告证据链和 audit 质量门禁。
- 离线/mock 仿真验证结果如何进入报告。
- 维护建议如何转成工单草稿，并通过工单质量门禁。
- 多资产机队健康趋势分析。
- 本地 dashboard 数据包和平台 readiness / operations platform baseline。
- 每个关键输出都保持 `human_review_required=true`。

## 安全边界

演示流程保持 offline-only、advisory-only、human-review-required。

它不连接真实无人机，不执行 MAVLink command，不执行 arm/disarm、takeoff、landing、RTL、mission execution、motor start、firmware upload 或 flight-controller parameter writing。

它不启动或连接 PX4、ArduPilot、Gazebo、SITL 或外部仿真器，不接入真实维修系统，不调用真实 fleet platform / CMMS / Jira / 飞书 / 企业微信 API，不自动派单，不上传文件，也不提交真实、敏感或未经批准的二进制飞行日志。

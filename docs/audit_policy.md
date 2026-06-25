# 审计策略

## 记录内容

每次 skill 执行记录：

- skill name
- skill version
- input file paths
- output file paths
- tools/functions called
- rules triggered
- timestamp
- human review required
- status

## 为什么需要审计

无人机运维建议会影响飞行安全和维护安全。审计记录让工程师能够追溯每个结论的输入、规则和输出，便于复核、复盘和持续改进。

## 从维护建议追溯到证据

维护建议包含 `evidence_refs`。每个证据引用记录 source type、source id、timestamp、field、measured value、threshold、rule id 和 description。报告的证据附录会汇总这些引用，帮助工程师从建议回到原始日志字段。

## 报告验证与证据索引

`drone-ops validate-report` 会对 `run-mvp` 输出做离线一致性检查。它优先校验结构化 JSON，而不是脆弱匹配 Markdown 全文。

验证范围包括：

- `anomalies.json` 中每个 anomaly 的 `evidence_refs`、`rule_id`、`measured_value`、`threshold` 和 `human_review_required`
- `diagnosis.json` 中每个 fault hypothesis 的证据、confidence、severity、recommended next steps 和人工复核要求
- `maintenance_recommendations.json` 中每条建议的证据、component、action、priority、reason、required approval 和人工复核要求
- `audit/*.json` 中关键 skill run 的输入、输出、工具、规则、时间戳、状态和人工复核标记
- `ops_report.md` 是否存在、是否包含主要章节和证据线索

使用 `--write-index` 时，命令会写出：

- `evidence_index.json`
- `report_validation.json`

`evidence_index.json` 使用稳定 key 汇总证据引用，并记录每条 evidence 被 anomaly、fault hypothesis 或 maintenance recommendation 引用的位置。该索引用于审计、回归测试和人工复核辅助，不代表真实飞行安全许可。

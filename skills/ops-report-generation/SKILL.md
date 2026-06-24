# Skill: ops-report-generation

## Purpose

生成 PDF-ready Markdown 运维报告。该 skill 对应 CLI 命令 `drone-ops generate-report`，核心函数是 `render_ops_report`。

## Inputs

- `flight_summary.json`
- `anomalies.json`
- `diagnosis.json`
- `maintenance_recommendations.json`
- `DroneAsset` JSON
- 可选 audit records

## Outputs

- `ops_report.md`
- `audit/ops-report-generation-<run_id>.json`

## Hard Rules

- 报告必须说明系统只提供运维支持和决策辅助。
- 报告不得包含真实飞控命令或执行步骤。
- 异常、故障假设和维护建议必须显示证据引用。
- 报告必须包含人工复核要求。

## Procedure

1. 加载摘要、异常、诊断、维护建议和资产。
2. 调用 `render_ops_report` 渲染 11 个固定章节。
3. 在异常、故障假设、维护建议和证据附录中展示 rule id 和 source id。
4. 写出 `ops_report.md`。
5. 写出审计记录。

## Evidence Requirements

- 报告的证据附录必须汇总 anomaly、diagnosis 和 maintenance 的 EvidenceRef。
- 正文条目必须提供简短证据引用，便于快速追溯。

## Audit Requirements

- 审计记录必须包含报告输入文件和输出路径。

## Test Cases

- 报告包含 11 个指定章节。
- 报告正文包含“证据：”和 rule id。
- 报告包含安全说明和人工复核要求。

## Known Limitations

- MVP 只生成 Markdown，不直接生成 PDF。

## Future Extensions

- 增加 PDF 导出。
- 增加报告模板版本管理。

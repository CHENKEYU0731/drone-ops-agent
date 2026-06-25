# Skill: ops-report-generation

## Purpose

生成 Markdown 运维报告，并支持将本地 Markdown 报告导出为 PDF。该 skill 对应 CLI 命令 `drone-ops generate-report`、`drone-ops export-pdf` 和 `drone-ops validate-report`，核心函数是 `render_ops_report`、`export_markdown_to_pdf` 和 `validate_report_outputs`。

## Inputs

- `flight_summary.json`
- `anomalies.json`
- `diagnosis.json`
- `maintenance_recommendations.json`
- `DroneAsset` JSON
- 可选 audit records
- 可选 Markdown 报告文件，用于 PDF 导出
- 可选 report output directory，用于 report validation
- 可选环境变量 `DRONE_OPS_PDF_FONT_PATH`，用于指定可嵌入 CJK TrueType/OpenType 字体

## Outputs

- `ops_report.md`
- `ops_report.pdf`，仅在运行 `export-pdf` 或 `generate-report --pdf` 时生成
- `audit/ops-report-generation-<run_id>.json`
- `evidence_index.json`，仅在运行 `validate-report --write-index` 时生成
- `report_validation.json`，仅在运行 `validate-report --write-index` 时生成

## Hard Rules

- 报告必须说明系统只提供运维支持和决策辅助。
- 报告不得包含真实飞控命令或执行步骤。
- 异常、故障假设和维护建议必须显示证据引用。
- 报告必须包含人工复核要求。
- PDF 导出只转换本地 Markdown 文件，不连接真实无人机，不执行任何真实动作。
- PDF 导出必须使用可嵌入 CJK TrueType/OpenType 字体；找不到字体时必须给出清晰错误，不得静默退化为可能导致中文不可见的 CID 字体。
- Report validation 只做离线可信度检查，不代表真实飞行安全许可。
- Report validation 不得放宽 `human_review_required=true` 要求；对高风险诊断或维护建议只能更严格。

## Procedure

1. 加载摘要、异常、诊断、维护建议和资产。
2. 调用 `render_ops_report` 渲染 11 个固定章节。
3. 在异常、故障假设、维护建议和证据附录中展示 rule id 和 source id。
4. 写出 `ops_report.md`。
5. 写出审计记录。
6. 如提供 `--pdf`，调用 `export_markdown_to_pdf` 将 Markdown 报告导出为 PDF。
7. 如使用 `export-pdf`，读取已有 Markdown 报告并写出 PDF。
8. 如使用 `validate-report`，读取 `flight_summary.json`、`anomalies.json`、`diagnosis.json`、`maintenance_recommendations.json`、`ops_report.md` 和 `audit/*.json`。
9. 校验证据链、关键 audit 记录、人工复核标记和轻量 Markdown 章节线索。
10. 如提供 `--write-index`，写出 `evidence_index.json` 和 `report_validation.json`。

## Evidence Requirements

- 报告的证据附录必须汇总 anomaly、diagnosis 和 maintenance 的 EvidenceRef。
- 正文条目必须提供简短证据引用，便于快速追溯。
- Report validation 必须确认 anomaly、fault hypothesis 和 maintenance recommendation 的 evidence refs 非空，并能构建稳定 evidence index key。

## Audit Requirements

- 审计记录必须包含报告输入文件和输出路径。
- PDF 导出当前不新增审计记录；生成报告阶段的审计仍记录 Markdown 报告生成输入和输出。
- Report validation 必须确认 flight-log-analysis、fault-diagnosis、maintenance-advisor 和 ops-report-generation 的 audit JSON 存在并包含输入、输出、工具、规则、时间戳、状态和人工复核标记。

## Test Cases

- 报告包含 11 个指定章节。
- 报告正文包含“证据：”和 rule id。
- 报告包含安全说明和人工复核要求。
- Markdown 可以导出为以 `%PDF` 开头的非空 PDF 文件。
- 缺失或空 Markdown 输入必须返回清晰错误。
- `export-pdf` CLI 可用。
- `generate-report --pdf` 可同步写出 Markdown 和 PDF。
- `validate-report --report-dir <dir>` 可以验证 `run-mvp` 输出。
- `validate-report --write-index` 可以写出 `evidence_index.json` 和 `report_validation.json`。
- 缺失 evidence refs、关键 audit 文件或 `ops_report.md` 时必须返回清晰错误且不显示 traceback。
- 如本机存在 Poppler，渲染第一页不得出现 `Missing language pack` 或 `Unknown font tag`。

## Known Limitations

- PDF 当前为基础可读排版，支持标题、段落、列表和代码块的基础渲染。
- 复杂 Markdown 表格和精细版式尚未实现。

## Future Extensions

- 增加 PDF 高级排版、表格渲染和模板版本管理。
- 增加报告模板版本管理。

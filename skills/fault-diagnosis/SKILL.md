# Skill: fault-diagnosis

## Purpose

根据 `FlightLogSummary`、`AnomalyEvent` 列表和 `DroneAsset` 生成按置信度排序的 `FaultHypothesis`。该 skill 由 CLI 命令 `drone-ops diagnose` 触发，核心函数是 `generate_fault_hypotheses`。

## Inputs

- `flight_summary.json`
- `anomalies.json`
- `DroneAsset` JSON

## Outputs

- `diagnosis.json`
- `audit/fault-diagnosis-<run_id>.json`

## Hard Rules

- 不输出唯一确定根因，除非证据非常充分。
- 每个故障假设必须包含 `supporting_evidence` 和 `evidence_refs`。
- `counter_evidence` 字段必须存在，即使当前为空。
- 所有诊断输出必须 `human_review_required=true`。

## Procedure

1. 加载摘要、异常和资产。
2. 将异常 rule id 映射到候选故障假设。
3. 合并同类假设的证据和下一步建议。
4. 按 confidence 降序排序。
5. 写出 `diagnosis.json`。
6. 写出审计记录。

## Evidence Requirements

- supporting evidence 必须来自异常事件的 EvidenceRef。
- evidence refs 必须能追溯到原始日志字段和规则阈值。

## Audit Requirements

- rules triggered 记录生成的故障假设名称。
- input refs 必须包含 summary、anomalies 和 asset。

## Test Cases

- 多个故障假设按 confidence 排序。
- 每个故障假设包含 supporting evidence、evidence refs 和 human review 标记。

## Known Limitations

- 当前是规则型诊断，不做概率图模型或机器学习。
- counter evidence 当前保留结构，后续可增加反证规则。

## Future Extensions

- 引入资产维护历史权重。
- 增加反证规则和置信度校准。

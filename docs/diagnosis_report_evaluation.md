# 诊断与报告评估

`run-evals` 是 v1.4.0 新增的本地离线质量门禁，用于评估诊断、维修建议和运维报告输出是否满足固定 golden case 的预期。

它只读取本地 JSON / Markdown 文件，不调用外部模型，不连接真实无人机、飞控、MAVLink endpoint、PX4、ArduPilot、Gazebo 或 SITL。所有结论都是 advisory-only，并且默认 `human_review_required=true`。

## 评估输入

样例用例位于：

- `data/sample_evals/diagnosis_report_eval_case.json`

该用例引用一组 deterministic sample outputs：

- `data/sample_evals/diagnosis_report_outputs/diagnosis.json`
- `data/sample_evals/diagnosis_report_outputs/maintenance_recommendations.json`
- `data/sample_evals/diagnosis_report_outputs/ops_report.md`

## 评估维度

v1.4.0 的 baseline 评估维度包括：

- `diagnosis_hypothesis_quality`：诊断假设是否覆盖预期 fault id。
- `maintenance_recommendation_coverage`：维修建议是否覆盖预期 recommendation id。
- `evidence_completeness`：诊断、维修建议和报告是否保留预期 evidence refs。
- `report_section_completeness`：报告是否包含诊断、维修建议、证据和安全边界章节。
- `safety_boundary_correctness`：报告是否声明 offline-only / advisory-only / 人工复核边界。

## CLI

```bash
python -m apps.cli.main run-evals \
  --case data/sample_evals/diagnosis_report_eval_case.json \
  --out <tmp-eval-dir>
```

输出：

- `<tmp-eval-dir>/eval_results.json`
- `<tmp-eval-dir>/eval_report.md`
- `<tmp-eval-dir>/audit/diagnosis-report-evaluation-*.json`

`eval_results.json` 使用固定 `created_at=1970-01-01T00:00:00Z`，结果顺序稳定，适合 golden / snapshot 风格测试。

## 安全边界

本评估能力不包含：

- 真实无人机连接
- MAVLink command execution
- arm/disarm、takeoff、landing、RTL、mission execution、motor start
- firmware upload
- flight-controller parameter writing
- PX4 / ArduPilot / Gazebo / SITL 启动或连接
- 外部模型调用
- 真实维修系统或真实工单系统接入
- 真实、敏感或未批准的二进制飞行日志

它只用于离线质量评估，不代表真实飞行授权或真实维修授权。

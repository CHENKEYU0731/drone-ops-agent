# 离线评测与案例研究

`run-case-studies` 是 v2.2.0 的本地案例研究入口。它复用已有 simulation scenario matrix 和 diagnosis/report eval，不复制业务规则，也不调用外部模型。

## 案例范围

默认样例组合包含 15 个案例：

- 14 个 offline/mock simulation matrix 场景。
- 1 个 diagnosis/report golden eval case。

仿真场景覆盖：

- nominal flight
- battery sag / low reserve
- GPS degradation
- motor vibration anomaly
- severe temperature issue
- return-home altitude breach
- low-battery return not triggered
- communication link loss
- geofence margin risk
- wind disturbance and mission completion
- payload/endurance margin
- missing validation constraint
- missing telemetry fields
- inconsistent simulation metadata

场景预期结果覆盖 `PASS`、`REVIEW_REQUIRED`、`FAIL` 和 `INVALID_INPUT`。

## 运行命令

```bash
python -m apps.cli.main run-case-studies \
  --simulation-matrix data/sample_simulation/scenario_matrix.json \
  --eval-case data/sample_evals/diagnosis_report_eval_case.json \
  --out <tmp-case-study-dir>
```

输出：

- `case_study_results.json`
- `case_study_report.md`
- `audit/evaluation-case-study-*.json`

## 指标定义

- `expected_status_accuracy`：实际状态与 case 中声明的预期状态一致的比例。
- `evidence_coverage_rate`：可执行规则和诊断/报告指标中包含证据引用的比例。
- `false_alarm_count`：预期 `PASS` 但实际不是 `PASS` 的仿真案例数。
- `missed_risk_count`：预期 `FAIL` 但实际没有得到 `FAIL` 的仿真案例数。
- `diagnosis_report_average_score`：诊断/报告 eval case 的平均确定性分数。

输出使用固定 `created_at=1970-01-01T00:00:00Z`、稳定 case 排序和 canonical SHA-256 `result_digest`，适合 golden / snapshot 和重复性检查。

## 结果解释

默认样例的目标是：

- 15 个案例全部匹配预期。
- `expected_status_accuracy=1.0`。
- `evidence_coverage_rate=1.0`。
- `false_alarm_count=0`。
- `missed_risk_count=0`。

这些数字只证明当前仓库内 sample / mock / sanitized case 与确定性规则一致，不代表真实飞行环境中的统计性能，也不能替代真实数据验证、专业维护判断或飞行授权。

## 安全边界

该流程保持 offline-only、advisory-only 和 `human_review_required=true`。它不连接真实无人机、飞控、PX4、ArduPilot、Gazebo、SITL、维修系统或 fleet platform，不执行 MAVLink command，不自动派单，不上传固件或写入飞控参数。

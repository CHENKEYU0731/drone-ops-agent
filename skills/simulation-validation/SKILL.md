# Skill: simulation-validation

## Purpose

导入 mock/offline simulation result JSON，并对结果字段执行离线验证。

MVP 不运行 PX4、ArduPilot、Gazebo 或任何真实 SITL，不连接真实无人机硬件，不执行 MAVLink command，不修改飞控参数，不上传固件。

## Inputs

- `SimulationScenario`
- exported offline simulation result JSON

## Outputs

- `SimulationRun`
- `simulation_run.json`
- audit JSON

## Hard Rules

- 仿真必须与真实硬件隔离。
- 不向真实飞控发送命令。
- 仿真结论不能自动批准维护或飞行操作。
- 不做 arm/disarm/takeoff/land/RTL/mission execution/firmware upload/parameter write。
- 所有 simulation validation 输出必须 `human_review_required=true`。
- 所有结论必须包含 `evidence_refs`。

## Procedure

1. 使用 `validate-simulation` 读取 `SimulationScenario` JSON。
2. 使用 `parse_simulation_result` 读取 mock/offline simulation result JSON。
3. 使用 `validate_simulation_result` 检查完成状态、failure events、failsafe events、timeout、持续时间、高度、航迹偏差、高度偏差和能量余量。
4. 写出 `simulation_run.json`。
5. 写出 `audit/simulation-validation-*.json`。

CLI:

```bash
drone-ops validate-simulation --scenario <path> --result <path> --out <dir>
python -m apps.cli.main validate-simulation --scenario <path> --result <path> --out <dir>
```

## Evidence Requirements

- `SimulationRun.evidence_refs` 必须引用 scenario 和 result source。
- 每条 result evidence 必须包含 source field、measured value、threshold 和 rule id。
- 不允许只写 "mock data" 作为证据。

## Audit Requirements

- 每次 skill run 必须写 audit JSON。
- audit 必须记录 scenario、result、rules triggered、output refs、status 和 `human_review_required=true`。

## Test Cases

- 无效场景会失败并给出清晰错误，不显示 Python traceback。
- 仿真结果包含 evidence refs。
- `PASS`、`FAIL` 和 `REVIEW_REQUIRED` 都需要人工复核。
- CLI 会写 `simulation_run.json` 和 audit JSON。

## Known Limitations

- MVP 不包含 SITL 执行器。
- MVP 不接入 ops report renderer。最终集成点是 `packages.report_templates.markdown.render_ops_report` 和 PDF exporter：当集成分支传入 `simulation_run.json` 时，`ops_report.md` 和 PDF 后续应增加 simulation validation section；没有 simulation result 时现有 run-mvp 报告章节不应变化。

## Future Extensions

- 增加 PX4/ArduPilot SITL。
- 增加仿真结果对比报告。

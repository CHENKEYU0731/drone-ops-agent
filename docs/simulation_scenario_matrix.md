# Simulation Scenario Matrix

This matrix is a deterministic offline/mock validation baseline for
`validate-simulation`. It documents expected outcomes for representative
simulation result imports without starting or connecting PX4, ArduPilot,
Gazebo, SITL, an external simulator, or real drone hardware.

The machine-readable fixture is:

- `data/sample_simulation/scenario_matrix.json`

## Safety Boundary

- Offline/mock import only.
- Advisory output only.
- No MAVLink command execution.
- No arm/disarm, takeoff, landing, RTL, mission execution, motor start,
  firmware upload, or flight-controller parameter writing.
- No real or sensitive binary flight logs are included.

## Expected Results

The matrix reuses existing `validate-simulation` statuses where possible:

- `PASS`: imported result satisfies all declared validation constraints.
- `REVIEW_REQUIRED`: imported result is parseable, but validation confidence is
  incomplete because required validation constraints are missing.
- `FAIL`: imported result contains failures, failsafe/timeout conditions, or
  threshold violations.
- `INVALID_INPUT`: fixture payload is intentionally invalid, so validation must
  fail before producing `SimulationRun`.

`INVALID_INPUT` is a matrix expectation, not a new `SimulationRun.status`.

The degraded `FAIL` cases are intentionally severe mock scenarios. Battery sag
and GPS degradation cross configured fail thresholds, while motor vibration and
temperature cases import explicit failure events. Lighter degradation without a
threshold violation should be modeled as `REVIEW_REQUIRED` only when the result
is parseable but validation confidence is incomplete.

The three incomplete-input cases are distinct:

- `missing-constraint-review`: the result payload is readable, but a validation
  constraint is absent, so the run is produced as `REVIEW_REQUIRED`.
- `missing-telemetry-fields`: required result telemetry is absent, so the matrix
  expects `INVALID_INPUT` before a `SimulationRun` is produced.
- `inconsistent-simulation-metadata`: scenario/result metadata is contradictory,
  so the matrix expects `INVALID_INPUT` before a `SimulationRun` is produced.

## Scenario Coverage

| Case ID | Scenario | Expected result | Validation intent |
| --- | --- | --- | --- |
| `nominal-flight` | nominal flight | `PASS` | All imported metrics remain within constraints. |
| `battery-sag-low-reserve` | battery sag / low battery degradation | `FAIL` | Energy reserve falls below `min_energy_remaining_pct`. |
| `gps-degradation` | GPS degradation | `FAIL` | Cross-track error exceeds `max_cross_track_error_m`. |
| `motor-vibration-anomaly` | motor vibration anomaly | `FAIL` | Offline result imports `motor_vibration_anomaly` as a failure event. |
| `severe-temperature-issue` | severe temperature issue | `FAIL` | Offline result imports `severe_temperature_issue` as a failure event. |
| `missing-constraint-review` | missing validation constraint | `REVIEW_REQUIRED` | Parseable result omits a validation threshold. |
| `missing-telemetry-fields` | missing telemetry fields | `INVALID_INPUT` | Required result field is absent. |
| `inconsistent-simulation-metadata` | inconsistent simulation metadata | `INVALID_INPUT` | Scenario and result `scenario_id` values do not match. |

## Determinism Rules

- Matrix cases are sorted and addressed by stable `case_id`.
- `simulation_run.json` uses deterministic `id`, timestamp, and evidence ref
  ordering for a given scenario/result pair.
- Validation audit `rules_triggered` remains sorted. Audit run ids and creation
  timestamps may still reflect the local skill run event.

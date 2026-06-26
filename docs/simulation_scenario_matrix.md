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

Operational rule expansion cases are also intentionally severe. Return-home
altitude, low-battery return strategy, link loss, geofence margin, wind
disturbance, and payload/endurance cases cross their declared offline thresholds
so the expected result is `FAIL`. These checks validate imported mock result
fields only; they do not start a simulator and do not execute flight-control
commands.

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
| `return-home-altitude-breach` | return-home altitude validation | `FAIL` | Return-home altitude falls below `min_return_home_altitude_m`. |
| `low-battery-return-not-triggered` | low-battery return strategy | `FAIL` | Battery reserve is below `low_battery_return_trigger_pct` and return was not triggered. |
| `communication-link-loss` | communication link interruption | `FAIL` | Link loss duration exceeds `max_link_loss_duration_s`. |
| `geofence-margin-risk` | geofence margin risk | `FAIL` | Geofence margin falls below `min_geofence_margin_m`. |
| `wind-disturbance-low-completion` | wind disturbance mission completion | `FAIL` | Wind threshold and minimum mission completion constraints are breached. |
| `payload-endurance-margin` | payload/endurance impact | `FAIL` | Endurance margin falls below `min_endurance_margin_pct`. |
| `missing-constraint-review` | missing validation constraint | `REVIEW_REQUIRED` | Parseable result omits a validation threshold. |
| `missing-telemetry-fields` | missing telemetry fields | `INVALID_INPUT` | Required result field is absent. |
| `inconsistent-simulation-metadata` | inconsistent simulation metadata | `INVALID_INPUT` | Scenario and result `scenario_id` values do not match. |

## Rule Results

`simulation_run.json` includes a deterministic `rule_results` list. Each item
contains:

- `rule_id`
- `status`
- `field`
- `measured_value`
- `threshold`
- `message`
- `evidence_refs`
- `human_review_required=true`

The top-level simulation status is derived from these rule results and legacy
failure/failsafe/timeout checks. Every rule result keeps evidence references so
reviewers can trace a conclusion back to the imported offline result field and
declared threshold.

## Determinism Rules

- Matrix cases are sorted and addressed by stable `case_id`.
- `simulation_run.json` uses deterministic `id`, timestamp, and evidence ref
  ordering for a given scenario/result pair.
- `rule_results` are sorted by rule id and field.
- Validation audit `rules_triggered` remains sorted. Audit run ids and creation
  timestamps may still reflect the local skill run event.

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from packages.drone_schemas import EvidenceRef, SimulationRuleResult, SimulationRun, SimulationScenario
from packages.simulation.result_parser import SimulationResult


SKILL_NAME = "simulation-validation"
SKILL_VERSION = "1.0.0"

PASS = "PASS"
FAIL = "FAIL"
REVIEW_REQUIRED = "REVIEW_REQUIRED"


def validate_simulation_result(
    scenario: SimulationScenario,
    result: SimulationResult,
    *,
    scenario_path: Path,
    result_path: Path,
) -> SimulationRun:
    if scenario.scenario_id != result.scenario_id:
        raise ValueError(
            f"仿真场景与结果不匹配: scenario_id={scenario.scenario_id}, result.scenario_id={result.scenario_id}"
        )

    rule_results: list[SimulationRuleResult] = []
    refs: list[EvidenceRef] = []

    completed_ref = _ref(
        result_path,
        "completed",
        str(result.completed).lower(),
        "true",
        "SIM_RESULT_COMPLETED",
        "Offline simulation result must report mission completion.",
    )
    refs.append(completed_ref)
    rule_results.append(
        _rule_result(
            rule_id="SIM_RESULT_COMPLETED",
            status=PASS if result.completed else FAIL,
            field="completed",
            measured_value=str(result.completed).lower(),
            threshold="true",
            message="Offline simulation result reports whether the mock mission completed.",
            evidence_ref=completed_ref,
        )
    )
    failed = not result.completed
    review = False

    if result.failure_events:
        failed = True
        failure_ref = _ref(
            result_path,
            "failure_events",
            ",".join(result.failure_events),
            "none",
            "SIM_RESULT_FAILURE_EVENT",
            "Offline simulation result reported failure events.",
        )
        refs.append(failure_ref)
        rule_results.append(
            _rule_result(
                rule_id="SIM_RESULT_FAILURE_EVENT",
                status=FAIL,
                field="failure_events",
                measured_value=",".join(result.failure_events),
                threshold="none",
                message="Offline simulation result reported failure events.",
                evidence_ref=failure_ref,
            )
        )

    if result.failsafe_events:
        failed = True
        failsafe_ref = _ref(
            result_path,
            "failsafe_events",
            ",".join(result.failsafe_events),
            "none",
            "SIM_RESULT_FAILSAFE_EVENT",
            "Offline simulation result reported failsafe events.",
        )
        refs.append(failsafe_ref)
        rule_results.append(
            _rule_result(
                rule_id="SIM_RESULT_FAILSAFE_EVENT",
                status=FAIL,
                field="failsafe_events",
                measured_value=",".join(result.failsafe_events),
                threshold="none",
                message="Offline simulation result reported failsafe events.",
                evidence_ref=failsafe_ref,
            )
        )

    if result.timeout:
        failed = True
        timeout_ref = _ref(
            result_path,
            "timeout",
            "true",
            "false",
            "SIM_RESULT_TIMEOUT",
            "Offline simulation result exceeded its configured runtime.",
        )
        refs.append(timeout_ref)
        rule_results.append(
            _rule_result(
                rule_id="SIM_RESULT_TIMEOUT",
                status=FAIL,
                field="timeout",
                measured_value="true",
                threshold="false",
                message="Offline simulation result exceeded its configured runtime.",
                evidence_ref=timeout_ref,
            )
        )

    checks = [
        ("duration_s", result.duration_s, "max_duration_s", lambda value, threshold: value <= threshold, "SIM_RESULT_DURATION"),
        ("max_altitude_m", result.max_altitude_m, "max_altitude_m", lambda value, threshold: value <= threshold, "SIM_RESULT_ALTITUDE"),
        (
            "max_cross_track_error_m",
            result.max_cross_track_error_m,
            "max_cross_track_error_m",
            lambda value, threshold: value <= threshold,
            "SIM_RESULT_CROSS_TRACK_ERROR",
        ),
        (
            "max_altitude_error_m",
            result.max_altitude_error_m,
            "max_altitude_error_m",
            lambda value, threshold: value <= threshold,
            "SIM_RESULT_ALTITUDE_ERROR",
        ),
        (
            "energy_remaining_pct",
            result.energy_remaining_pct,
            "min_energy_remaining_pct",
            lambda value, threshold: value >= threshold,
            "SIM_RESULT_ENERGY_RESERVE",
        ),
    ]

    for field, measured, threshold_field, predicate, rule_id in checks:
        rule_result = _evaluate_threshold_rule(
            result=result,
            result_path=result_path,
            field=field,
            measured=measured,
            threshold_field=threshold_field,
            predicate=predicate,
            rule_id=rule_id,
            description="Offline simulation metric was checked against the exported constraint.",
        )
        rule_results.append(rule_result)
        refs.extend(rule_result.evidence_refs)
        if rule_result.status == FAIL:
            failed = True
        elif rule_result.status == REVIEW_REQUIRED:
            review = True

    operational_checks = [
        (
            "return_home_altitude_m",
            result.return_home_altitude_m,
            "min_return_home_altitude_m",
            lambda value, threshold: value >= threshold,
            "SIM_RTH_ALTITUDE",
            "Return-home altitude from the offline result was checked against the minimum safe mock threshold.",
        ),
        (
            "low_battery_return_triggered",
            result.low_battery_return_triggered,
            "low_battery_return_trigger_pct",
            lambda value, threshold: bool(value) if result.energy_remaining_pct <= threshold else True,
            "SIM_LOW_BATTERY_RTH",
            "Low-battery return strategy was checked when the mock result fell below the trigger threshold.",
        ),
        (
            "max_link_loss_duration_s",
            result.max_link_loss_duration_s,
            "max_link_loss_duration_s",
            lambda value, threshold: value <= threshold,
            "SIM_LINK_LOSS_DURATION",
            "Communication link loss duration was checked against the offline validation threshold.",
        ),
        (
            "geofence_margin_m",
            result.geofence_margin_m,
            "min_geofence_margin_m",
            lambda value, threshold: value >= threshold,
            "SIM_GEOFENCE_MARGIN",
            "Geofence margin was checked against the minimum offline safety margin.",
        ),
        (
            "wind_speed_mps",
            result.wind_speed_mps,
            "max_wind_speed_mps",
            lambda value, threshold: value <= threshold,
            "SIM_WIND_SPEED",
            "Wind disturbance was checked against the maximum offline wind threshold.",
        ),
        (
            "mission_completion_pct",
            result.mission_completion_pct,
            "min_wind_mission_completion_pct",
            lambda value, threshold: value >= threshold,
            "SIM_WIND_MISSION_COMPLETION",
            "Mission completion under wind disturbance was checked against the offline threshold.",
        ),
        (
            "endurance_margin_pct",
            result.endurance_margin_pct,
            "min_endurance_margin_pct",
            lambda value, threshold: value >= threshold,
            "SIM_PAYLOAD_ENDURANCE_MARGIN",
            "Payload/endurance margin was checked against the minimum offline reserve threshold.",
        ),
    ]

    for field, measured, threshold_field, predicate, rule_id, description in operational_checks:
        if measured is None and threshold_field not in result.constraints:
            continue
        rule_result = _evaluate_threshold_rule(
            result=result,
            result_path=result_path,
            field=field,
            measured=measured,
            threshold_field=threshold_field,
            predicate=predicate,
            rule_id=rule_id,
            description=description,
        )
        rule_results.append(rule_result)
        refs.extend(rule_result.evidence_refs)
        if rule_result.status == FAIL:
            failed = True
        elif rule_result.status == REVIEW_REQUIRED:
            review = True

    refs.append(
        EvidenceRef(
            source_type="simulation_scenario",
            source_id=f"{_path_ref(scenario_path)}:scenario_id",
            field="scenario_id",
            measured_value=scenario.scenario_id,
            threshold=result.scenario_id,
            rule_id="SIM_SCENARIO_MATCH",
            description="Simulation scenario id matches the imported offline result.",
        )
    )

    status = FAIL if failed else REVIEW_REQUIRED if review else PASS
    result_summary = (
        f"Validated offline simulation result {result.result_id} for scenario {scenario.scenario_id}: "
        f"status={status}. This offline simulation result does not authorize real flight, maintenance, "
        "arm/disarm, takeoff, landing, RTL, mission execution, firmware upload, or parameter changes."
    )

    refs = sorted(refs, key=lambda ref: (ref.rule_id, ref.field, ref.source_id))
    rule_results = sorted(rule_results, key=lambda item: (item.rule_id, item.field))

    return SimulationRun(
        id=f"SIM-{scenario.scenario_id}-{result.result_id}",
        timestamp=datetime(1970, 1, 1, tzinfo=UTC),
        scenario_id=scenario.scenario_id,
        status=status,
        evidence_refs=refs,
        rule_results=rule_results,
        result_summary=result_summary,
        human_review_required=True,
        drone_id=scenario.drone_id,
        generated_by_skill=SKILL_NAME,
        skill_version=SKILL_VERSION,
    )


def _evaluate_threshold_rule(
    *,
    result: SimulationResult,
    result_path: Path,
    field: str,
    measured: float | int | str | bool | None,
    threshold_field: str,
    predicate,
    rule_id: str,
    description: str,
) -> SimulationRuleResult:
    threshold = result.constraints.get(threshold_field)
    if measured is None:
        ref = _ref(
            result_path,
            field,
            "missing",
            f"required:{field}",
            f"{rule_id}_REVIEW",
            "Offline simulation result omitted a validation metric.",
        )
        return _rule_result(
            rule_id=rule_id,
            status=REVIEW_REQUIRED,
            field=field,
            measured_value="missing",
            threshold=f"required:{field}",
            message="Offline simulation result omitted a validation metric.",
            evidence_ref=ref,
        )
    if threshold is None:
        ref = _ref(
            result_path,
            field,
            _serializable_value(measured),
            f"missing:{threshold_field}",
            f"{rule_id}_REVIEW",
            "Offline simulation result omitted a validation constraint.",
        )
        return _rule_result(
            rule_id=rule_id,
            status=REVIEW_REQUIRED,
            field=field,
            measured_value=_serializable_value(measured),
            threshold=f"missing:{threshold_field}",
            message="Offline simulation result omitted a validation constraint.",
            evidence_ref=ref,
        )

    passed = predicate(measured, threshold)
    ref = _ref(
        result_path,
        field,
        _serializable_value(measured),
        threshold,
        rule_id,
        description,
    )
    return _rule_result(
        rule_id=rule_id,
        status=PASS if passed else FAIL,
        field=field,
        measured_value=_serializable_value(measured),
        threshold=threshold,
        message=description,
        evidence_ref=ref,
    )


def _rule_result(
    *,
    rule_id: str,
    status: str,
    field: str,
    measured_value: float | int | str,
    threshold: float | int | str,
    message: str,
    evidence_ref: EvidenceRef,
) -> SimulationRuleResult:
    return SimulationRuleResult(
        rule_id=rule_id,
        status=status,
        field=field,
        measured_value=measured_value,
        threshold=threshold,
        message=message,
        evidence_refs=[evidence_ref],
        human_review_required=True,
    )


def _ref(
    result_path: Path,
    field: str,
    measured_value: float | int | str,
    threshold: float | int | str,
    rule_id: str,
    description: str,
) -> EvidenceRef:
    return EvidenceRef(
        source_type="simulation_result",
        source_id=f"{_path_ref(result_path)}:{field}",
        field=field,
        measured_value=measured_value,
        threshold=threshold,
        rule_id=rule_id,
        description=description,
    )


def _path_ref(path: Path) -> str:
    return path.as_posix()


def _serializable_value(value: float | int | str | bool) -> float | int | str:
    if isinstance(value, bool):
        return str(value).lower()
    return value

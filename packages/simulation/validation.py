from __future__ import annotations

from pathlib import Path

from packages.drone_schemas import EvidenceRef, SimulationRun, SimulationScenario
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

    refs: list[EvidenceRef] = [
        _ref(
            result_path,
            "completed",
            str(result.completed).lower(),
            "true",
            "SIM_RESULT_COMPLETED",
            "Offline simulation result must report mission completion.",
        )
    ]
    failed = not result.completed
    review = False

    if result.failure_events:
        failed = True
        refs.append(
            _ref(
                result_path,
                "failure_events",
                ",".join(result.failure_events),
                "none",
                "SIM_RESULT_FAILURE_EVENT",
                "Offline simulation result reported failure events.",
            )
        )

    if result.failsafe_events:
        failed = True
        refs.append(
            _ref(
                result_path,
                "failsafe_events",
                ",".join(result.failsafe_events),
                "none",
                "SIM_RESULT_FAILSAFE_EVENT",
                "Offline simulation result reported failsafe events.",
            )
        )

    if result.timeout:
        failed = True
        refs.append(
            _ref(
                result_path,
                "timeout",
                "true",
                "false",
                "SIM_RESULT_TIMEOUT",
                "Offline simulation result exceeded its configured runtime.",
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
        threshold = result.constraints.get(threshold_field)
        if threshold is None:
            review = True
            refs.append(
                _ref(
                    result_path,
                    field,
                    measured,
                    f"missing:{threshold_field}",
                    f"{rule_id}_REVIEW",
                    "Offline simulation result omitted a validation constraint.",
                )
            )
            continue
        refs.append(
            _ref(
                result_path,
                field,
                measured,
                threshold,
                rule_id,
                "Offline simulation metric was checked against the exported constraint.",
            )
        )
        if not predicate(float(measured), float(threshold)):
            failed = True

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

    return SimulationRun(
        scenario_id=scenario.scenario_id,
        status=status,
        evidence_refs=refs,
        result_summary=result_summary,
        human_review_required=True,
        drone_id=scenario.drone_id,
        generated_by_skill=SKILL_NAME,
        skill_version=SKILL_VERSION,
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

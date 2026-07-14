from pathlib import Path

import pytest

from packages.simulation import FAIL, PASS, REVIEW_REQUIRED, validate_simulation_result
from packages.simulation.scenario_matrix import INVALID_INPUT, load_simulation_scenario_matrix


MATRIX_PATH = Path("data/sample_simulation/scenario_matrix.json")


EXPECTED_RESULTS = {
    "nominal-flight": PASS,
    "battery-sag-low-reserve": FAIL,
    "gps-degradation": FAIL,
    "motor-vibration-anomaly": FAIL,
    "severe-temperature-issue": FAIL,
    "return-home-altitude-breach": FAIL,
    "low-battery-return-not-triggered": FAIL,
    "communication-link-loss": FAIL,
    "geofence-margin-risk": FAIL,
    "wind-disturbance-low-completion": FAIL,
    "payload-endurance-margin": FAIL,
    "missing-constraint-review": REVIEW_REQUIRED,
    "missing-telemetry-fields": INVALID_INPUT,
    "inconsistent-simulation-metadata": INVALID_INPUT,
}


def test_simulation_scenario_matrix_declares_expected_results() -> None:
    cases = load_simulation_scenario_matrix(MATRIX_PATH)

    assert {case.case_id: case.expected_result for case in cases} == EXPECTED_RESULTS
    assert all(case.mode == "offline_mock_import" for case in cases)
    assert all(case.safety_boundary == "advisory_only" for case in cases)


@pytest.mark.parametrize("case_id,expected_result", EXPECTED_RESULTS.items())
def test_simulation_scenario_matrix_cases_are_deterministic(case_id: str, expected_result: str) -> None:
    case = load_simulation_scenario_matrix(MATRIX_PATH).by_id(case_id)

    if expected_result == INVALID_INPUT:
        with pytest.raises(ValueError, match=case.expected_error_contains):
            case.validate_payloads()
        return

    scenario, result = case.validate_payloads()
    run = validate_simulation_result(
        scenario,
        result,
        scenario_path=MATRIX_PATH,
        result_path=MATRIX_PATH,
    )

    assert run.status == expected_result
    assert run.human_review_required is True
    assert run.evidence_refs
    assert run.rule_results
    assert run.id == f"SIM-{scenario.scenario_id}-{result.result_id}"
    assert run.timestamp.isoformat() == "1970-01-01T00:00:00+00:00"
    assert [ref.rule_id for ref in run.evidence_refs] == sorted(ref.rule_id for ref in run.evidence_refs)
    assert [item.rule_id for item in run.rule_results] == sorted(item.rule_id for item in run.rule_results)


def test_simulation_scenario_matrix_rejects_unknown_case_id() -> None:
    cases = load_simulation_scenario_matrix(MATRIX_PATH)

    with pytest.raises(KeyError, match="unknown-case"):
        cases.by_id("unknown-case")

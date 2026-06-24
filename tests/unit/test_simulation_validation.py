from pathlib import Path

from packages.drone_schemas import SimulationScenario, load_model
from packages.simulation import parse_simulation_result, validate_simulation_result


SCENARIO_PATH = Path("data/sample_simulation/example_scenario.json")
RESULT_PATH = Path("data/sample_simulation/example_simulation_result.json")


def test_parse_simulation_result_reads_mock_export() -> None:
    result = parse_simulation_result(RESULT_PATH)

    assert result.result_id == "SIM-RESULT-001"
    assert result.scenario_id == "SIM-SCENARIO-001"
    assert result.completed is True
    assert result.constraints["max_cross_track_error_m"] == 5


def test_validate_simulation_result_returns_pass_with_evidence_refs() -> None:
    scenario = load_model(SCENARIO_PATH, SimulationScenario)
    result = parse_simulation_result(RESULT_PATH)

    run = validate_simulation_result(scenario, result, scenario_path=SCENARIO_PATH, result_path=RESULT_PATH)

    assert run.status == "PASS"
    assert run.human_review_required is True
    assert run.generated_by_skill == "simulation-validation"
    assert run.evidence_refs
    assert {ref.field for ref in run.evidence_refs} >= {
        "completed",
        "max_altitude_m",
        "max_cross_track_error_m",
        "max_altitude_error_m",
        "energy_remaining_pct",
    }
    assert all(ref.source_id.startswith("data/sample_simulation/") for ref in run.evidence_refs)
    assert "offline simulation result" in run.result_summary
    assert "does not authorize real flight" in run.result_summary


def test_validate_simulation_result_marks_failures_for_review() -> None:
    scenario = load_model(SCENARIO_PATH, SimulationScenario)
    result = parse_simulation_result(RESULT_PATH).model_copy(
        update={
            "completed": False,
            "max_cross_track_error_m": 9.5,
            "failure_events": ["mission_timeout"],
        }
    )

    run = validate_simulation_result(scenario, result, scenario_path=SCENARIO_PATH, result_path=RESULT_PATH)

    assert run.status == "FAIL"
    assert run.human_review_required is True
    assert "SIM_RESULT_FAILURE_EVENT" in {ref.rule_id for ref in run.evidence_refs}


def test_simulation_validation_production_code_has_no_control_stack_imports() -> None:
    forbidden_terms = [
        "pymavlink",
        "mavutil",
        "mavsdk",
        "dronekit",
        "set_parameter",
        "param_set",
        "command_long",
    ]

    for path in Path("packages/simulation").glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            assert term not in text, f"{path} must not include control stack term {term}"

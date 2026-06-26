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


def test_validate_simulation_result_outputs_structured_operational_rule_results() -> None:
    scenario = load_model(SCENARIO_PATH, SimulationScenario)
    result = parse_simulation_result(RESULT_PATH).model_copy(
        update={
            "return_home_altitude_m": 55,
            "low_battery_return_triggered": True,
            "max_link_loss_duration_s": 2,
            "geofence_margin_m": 18,
            "wind_speed_mps": 7,
            "mission_completion_pct": 98,
            "payload_mass_kg": 1.2,
            "endurance_margin_pct": 24,
            "constraints": {
                "max_duration_s": 600,
                "max_altitude_m": 60,
                "max_cross_track_error_m": 5,
                "max_altitude_error_m": 4,
                "min_energy_remaining_pct": 30,
                "min_return_home_altitude_m": 45,
                "low_battery_return_trigger_pct": 25,
                "max_link_loss_duration_s": 5,
                "min_geofence_margin_m": 10,
                "max_wind_speed_mps": 10,
                "min_wind_mission_completion_pct": 90,
                "min_endurance_margin_pct": 15,
            },
        }
    )

    run = validate_simulation_result(scenario, result, scenario_path=SCENARIO_PATH, result_path=RESULT_PATH)

    assert run.status == "PASS"
    rule_results = {item.rule_id: item for item in run.rule_results}
    assert rule_results["SIM_RTH_ALTITUDE"].status == "PASS"
    assert rule_results["SIM_LOW_BATTERY_RTH"].status == "PASS"
    assert rule_results["SIM_LINK_LOSS_DURATION"].status == "PASS"
    assert rule_results["SIM_GEOFENCE_MARGIN"].status == "PASS"
    assert rule_results["SIM_WIND_MISSION_COMPLETION"].status == "PASS"
    assert rule_results["SIM_PAYLOAD_ENDURANCE_MARGIN"].status == "PASS"
    assert all(item.evidence_refs for item in run.rule_results)
    assert [item.rule_id for item in run.rule_results] == sorted(item.rule_id for item in run.rule_results)


def test_validate_simulation_result_fails_severe_operational_rule_breaches() -> None:
    scenario = load_model(SCENARIO_PATH, SimulationScenario)
    result = parse_simulation_result(RESULT_PATH).model_copy(
        update={
            "return_home_altitude_m": 32,
            "low_battery_return_triggered": False,
            "max_link_loss_duration_s": 14,
            "geofence_margin_m": -2,
            "wind_speed_mps": 14,
            "mission_completion_pct": 76,
            "payload_mass_kg": 2.6,
            "endurance_margin_pct": 8,
            "energy_remaining_pct": 18,
            "constraints": {
                "max_duration_s": 600,
                "max_altitude_m": 60,
                "max_cross_track_error_m": 5,
                "max_altitude_error_m": 4,
                "min_energy_remaining_pct": 30,
                "min_return_home_altitude_m": 45,
                "low_battery_return_trigger_pct": 25,
                "max_link_loss_duration_s": 5,
                "min_geofence_margin_m": 10,
                "max_wind_speed_mps": 10,
                "min_wind_mission_completion_pct": 90,
                "min_endurance_margin_pct": 15,
            },
        }
    )

    run = validate_simulation_result(scenario, result, scenario_path=SCENARIO_PATH, result_path=RESULT_PATH)

    assert run.status == "FAIL"
    failed_rules = {item.rule_id for item in run.rule_results if item.status == "FAIL"}
    assert failed_rules >= {
        "SIM_RTH_ALTITUDE",
        "SIM_LOW_BATTERY_RTH",
        "SIM_LINK_LOSS_DURATION",
        "SIM_GEOFENCE_MARGIN",
        "SIM_WIND_MISSION_COMPLETION",
        "SIM_PAYLOAD_ENDURANCE_MARGIN",
    }
    assert failed_rules <= {ref.rule_id for ref in run.evidence_refs}


def test_validate_simulation_result_requires_review_for_missing_operational_metric() -> None:
    scenario = load_model(SCENARIO_PATH, SimulationScenario)
    result = parse_simulation_result(RESULT_PATH).model_copy(
        update={
            "constraints": {
                "max_duration_s": 600,
                "max_altitude_m": 60,
                "max_cross_track_error_m": 5,
                "max_altitude_error_m": 4,
                "min_energy_remaining_pct": 30,
                "min_return_home_altitude_m": 45,
            },
        }
    )

    run = validate_simulation_result(scenario, result, scenario_path=SCENARIO_PATH, result_path=RESULT_PATH)

    assert run.status == "REVIEW_REQUIRED"
    rule_results = {item.rule_id: item for item in run.rule_results}
    assert rule_results["SIM_RTH_ALTITUDE"].status == "REVIEW_REQUIRED"
    assert rule_results["SIM_RTH_ALTITUDE"].field == "return_home_altitude_m"


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

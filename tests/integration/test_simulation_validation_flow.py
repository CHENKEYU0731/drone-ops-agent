import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import write_json
from packages.simulation import load_simulation_scenario_matrix


runner = CliRunner()
MATRIX_PATH = Path("data/sample_simulation/scenario_matrix.json")


def test_validate_simulation_cli_writes_run_and_audit(tmp_path: Path) -> None:
    out_dir = tmp_path / "simulation"
    result = runner.invoke(
        app,
        [
            "validate-simulation",
            "--scenario",
            "data/sample_simulation/example_scenario.json",
            "--result",
            "data/sample_simulation/example_simulation_result.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    output = out_dir / "simulation_run.json"
    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    assert payload["human_review_required"] is True
    assert payload["evidence_refs"]

    audit_files = list((out_dir / "audit").glob("simulation-validation-*.json"))
    assert audit_files
    audit = json.loads(audit_files[0].read_text(encoding="utf-8"))
    assert audit["skill_name"] == "simulation-validation"
    assert audit["output_refs"] == [str(output)]
    assert audit["rules_triggered"]
    assert audit["human_review_required"] is True
    assert audit["status"] == "success"


def test_validate_simulation_cli_missing_file_error_is_clear(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "validate-simulation",
            "--scenario",
            "missing_scenario.json",
            "--result",
            "data/sample_simulation/example_simulation_result.json",
            "--out",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "missing_scenario.json" in result.output
    assert "Traceback" not in result.output


def test_validate_simulation_cli_accepts_matrix_nominal_fixture(tmp_path: Path) -> None:
    case = load_simulation_scenario_matrix(MATRIX_PATH).by_id("nominal-flight")
    scenario_path = tmp_path / "scenario.json"
    result_path = tmp_path / "result.json"
    out_dir = tmp_path / "simulation"
    write_json(scenario_path, case.scenario)
    write_json(result_path, case.result)

    result = runner.invoke(
        app,
        [
            "validate-simulation",
            "--scenario",
            str(scenario_path),
            "--result",
            str(result_path),
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads((out_dir / "simulation_run.json").read_text(encoding="utf-8"))
    assert payload["id"] == "SIM-SIM-MATRIX-NOMINAL-SIM-MATRIX-RESULT-NOMINAL"
    assert payload["timestamp"] == "1970-01-01T00:00:00Z"
    assert payload["status"] == "PASS"
    assert [ref["rule_id"] for ref in payload["evidence_refs"]] == sorted(
        ref["rule_id"] for ref in payload["evidence_refs"]
    )

    audit_files = list((out_dir / "audit").glob("simulation-validation-*.json"))
    assert audit_files
    audit = json.loads(audit_files[0].read_text(encoding="utf-8"))
    assert audit["metadata"]["simulation_status"] == "PASS"
    assert audit["metadata"]["safety_boundary"] == "offline-import-only"


def test_validate_simulation_cli_writes_rule_results_and_audit_rules(tmp_path: Path) -> None:
    scenario_path = tmp_path / "scenario.json"
    result_path = tmp_path / "result.json"
    out_dir = tmp_path / "simulation"
    write_json(
        scenario_path,
        {
            "scenario_id": "SIM-OPS-RULES",
            "drone_id": "UAV-001",
            "description": "Offline operational rule validation fixture.",
            "input_refs": ["mock://simulation/operational-rules"],
        },
    )
    write_json(
        result_path,
        {
            "result_id": "SIM-OPS-RULES-RESULT",
            "scenario_id": "SIM-OPS-RULES",
            "mission_id": "MISSION-OPS-RULES",
            "source": "offline_mock_export",
            "duration_s": 520,
            "completed": True,
            "max_altitude_m": 57,
            "max_cross_track_error_m": 4,
            "max_altitude_error_m": 2,
            "failsafe_events": [],
            "failure_events": [],
            "energy_remaining_pct": 19,
            "return_home_altitude_m": 35,
            "low_battery_return_triggered": False,
            "max_link_loss_duration_s": 12,
            "geofence_margin_m": -1,
            "wind_speed_mps": 14,
            "mission_completion_pct": 82,
            "payload_mass_kg": 2.4,
            "endurance_margin_pct": 7,
            "timeout": False,
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
        },
    )

    result = runner.invoke(
        app,
        [
            "validate-simulation",
            "--scenario",
            str(scenario_path),
            "--result",
            str(result_path),
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads((out_dir / "simulation_run.json").read_text(encoding="utf-8"))
    assert payload["status"] == "FAIL"
    assert payload["human_review_required"] is True
    rule_ids = [item["rule_id"] for item in payload["rule_results"]]
    assert rule_ids == sorted(rule_ids)
    assert {
        "SIM_RTH_ALTITUDE",
        "SIM_LOW_BATTERY_RTH",
        "SIM_LINK_LOSS_DURATION",
        "SIM_GEOFENCE_MARGIN",
        "SIM_WIND_MISSION_COMPLETION",
        "SIM_PAYLOAD_ENDURANCE_MARGIN",
    } <= set(rule_ids)
    assert all(item["human_review_required"] is True for item in payload["rule_results"])
    assert all(item["evidence_refs"] for item in payload["rule_results"])

    audit_files = list((out_dir / "audit").glob("simulation-validation-*.json"))
    assert audit_files
    audit = json.loads(audit_files[0].read_text(encoding="utf-8"))
    assert {
        "SIM_RTH_ALTITUDE",
        "SIM_LOW_BATTERY_RTH",
        "SIM_LINK_LOSS_DURATION",
        "SIM_GEOFENCE_MARGIN",
        "SIM_WIND_MISSION_COMPLETION",
        "SIM_PAYLOAD_ENDURANCE_MARGIN",
    } <= set(audit["rules_triggered"])

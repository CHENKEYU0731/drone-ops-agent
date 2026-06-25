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

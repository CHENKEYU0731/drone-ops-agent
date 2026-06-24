import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


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

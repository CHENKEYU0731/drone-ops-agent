from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_run_evals_cli_writes_eval_results_and_audit(tmp_path: Path) -> None:
    out_dir = tmp_path / "evals"

    result = runner.invoke(
        app,
        [
            "run-evals",
            "--case",
            "data/sample_evals/diagnosis_report_eval_case.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Eval suite status: PASS" in result.output
    payload = read_json_file(out_dir / "eval_results.json")
    assert isinstance(payload, dict)
    assert payload["status"] == "PASS"
    assert payload["human_review_required"] is True
    assert payload["safety_boundary"]["offline_only"] is True
    audit_files = sorted((out_dir / "audit").glob("diagnosis-report-evaluation-*.json"))
    assert audit_files
    audit = read_json_file(audit_files[0])
    assert isinstance(audit, dict)
    assert audit["skill_name"] == "diagnosis-report-evaluation"
    assert audit["rules_triggered"] == [
        "diagnosis_hypothesis_quality",
        "evidence_completeness",
        "maintenance_recommendation_coverage",
        "report_section_completeness",
        "safety_boundary_correctness",
    ]

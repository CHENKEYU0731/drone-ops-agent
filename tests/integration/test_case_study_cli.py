import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_case_study_cli_writes_results_report_and_audit(tmp_path: Path) -> None:
    out_dir = tmp_path / "case-study"

    result = runner.invoke(
        app,
        [
            "run-case-studies",
            "--simulation-matrix",
            "data/sample_simulation/scenario_matrix.json",
            "--eval-case",
            "data/sample_evals/diagnosis_report_eval_case.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case study status: PASS" in result.output
    payload = read_json_file(out_dir / "case_study_results.json")
    assert isinstance(payload, dict)
    assert payload["case_count"] == 15
    assert payload["metrics"]["expected_status_accuracy"] == 1.0
    report = (out_dir / "case_study_report.md").read_text(encoding="utf-8")
    assert "v2.2.0 离线评测与案例研究" in report
    assert "误报数" in report
    assert "漏检数" in report
    assert "证据覆盖率" in report

    audit_files = sorted((out_dir / "audit").glob("evaluation-case-study-*.json"))
    assert audit_files
    audit = read_json_file(audit_files[0])
    assert isinstance(audit, dict)
    assert audit["skill_name"] == "evaluation-case-study"
    assert audit["human_review_required"] is True
    assert set(audit["rules_triggered"]) >= {
        "CASE_EVIDENCE_COVERAGE",
        "CASE_EXPECTED_STATUS_MATCH",
        "CASE_FALSE_ALARM_COUNT",
        "CASE_MISSED_RISK_COUNT",
    }


def test_case_study_cli_returns_nonzero_for_status_mismatch(tmp_path: Path) -> None:
    source = Path("data/sample_simulation/scenario_matrix.json")
    matrix = json.loads(source.read_text(encoding="utf-8"))
    nominal = next(case for case in matrix["cases"] if case["case_id"] == "nominal-flight")
    nominal["expected_result"] = "FAIL"
    matrix_path = tmp_path / "scenario_matrix.json"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_dir = tmp_path / "failed-case-study"

    result = runner.invoke(
        app,
        [
            "run-case-studies",
            "--simulation-matrix",
            str(matrix_path),
            "--eval-case",
            "data/sample_evals/diagnosis_report_eval_case.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 1
    payload = read_json_file(out_dir / "case_study_results.json")
    assert isinstance(payload, dict)
    assert payload["status"] == "FAIL"
    audit_path = next((out_dir / "audit").glob("evaluation-case-study-*.json"))
    audit = read_json_file(audit_path)
    assert isinstance(audit, dict)
    assert audit["status"] == "failed"

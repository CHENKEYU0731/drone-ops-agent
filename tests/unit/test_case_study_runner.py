import json
from pathlib import Path

from packages.evals.case_study import run_case_study


MATRIX_PATH = Path("data/sample_simulation/scenario_matrix.json")
EVAL_CASE_PATH = Path("data/sample_evals/diagnosis_report_eval_case.json")


def test_case_study_combines_simulation_and_diagnosis_report_evidence() -> None:
    payload = run_case_study(MATRIX_PATH, [EVAL_CASE_PATH])

    assert payload["schema_version"] == 1
    assert payload["created_at"] == "1970-01-01T00:00:00Z"
    assert payload["status"] == "PASS"
    assert payload["case_count"] == 15
    assert payload["simulation"]["case_count"] == 14
    assert payload["simulation"]["status_counts"] == {
        "FAIL": 10,
        "INVALID_INPUT": 2,
        "PASS": 1,
        "REVIEW_REQUIRED": 1,
    }
    assert payload["diagnosis_report"]["case_count"] == 1
    assert payload["metrics"] == {
        "diagnosis_report_average_score": 1.0,
        "evidence_coverage_rate": 1.0,
        "expected_status_accuracy": 1.0,
        "false_alarm_count": 0,
        "missed_risk_count": 0,
    }
    assert all(case["matched_expected"] for case in payload["simulation"]["cases"])
    assert all(case["expected_error_matched"] for case in payload["simulation"]["cases"])
    assert all(case["human_review_required"] for case in payload["simulation"]["cases"])
    assert payload["human_review_required"] is True


def test_case_study_output_is_deterministic() -> None:
    first = run_case_study(MATRIX_PATH, [EVAL_CASE_PATH])
    second = run_case_study(MATRIX_PATH, [EVAL_CASE_PATH])

    assert first == second
    assert len(first["result_digest"]) == 64


def test_case_study_fails_when_observed_status_misses_expected_risk(tmp_path: Path) -> None:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    nominal = next(case for case in matrix["cases"] if case["case_id"] == "nominal-flight")
    nominal["expected_result"] = "FAIL"
    matrix_path = tmp_path / "scenario_matrix.json"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload = run_case_study(matrix_path, [EVAL_CASE_PATH])

    assert payload["status"] == "FAIL"
    assert payload["metrics"]["expected_status_accuracy"] < 1.0
    assert payload["metrics"]["missed_risk_count"] == 1

from pathlib import Path

from packages.drone_schemas import read_json_file
from packages.evals import run_eval_case, run_eval_suite


CASE_PATH = Path("data/sample_evals/diagnosis_report_eval_case.json")


def test_run_eval_case_passes_golden_diagnosis_report_case() -> None:
    result = run_eval_case(CASE_PATH)

    assert result.case_id == "diagnosis-report-golden"
    assert result.status.value == "PASS"
    assert result.score == 1.0
    assert result.human_review_required is True
    assert [item["metric_id"] for item in result.metric_results] == sorted(
        item["metric_id"] for item in result.metric_results
    )
    assert not result.findings


def test_run_eval_case_fails_when_required_report_section_is_missing(tmp_path: Path) -> None:
    case_payload = read_json_file(CASE_PATH)
    assert isinstance(case_payload, dict)
    report_path = tmp_path / "ops_report.md"
    report_path.write_text("# Report\n\n## Diagnosis\n\n## Evidence\n", encoding="utf-8")
    case_payload["input_refs"]["report"] = str(report_path)
    case_path = tmp_path / "case.json"
    case_path.write_text(__import__("json").dumps(case_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = run_eval_case(case_path)

    assert result.status.value == "FAIL"
    assert any(finding["code"] == "MISSING_REPORT_SECTION" for finding in result.findings)


def test_run_eval_suite_writes_deterministic_eval_results(tmp_path: Path) -> None:
    output_path = tmp_path / "eval_results.json"

    payload = run_eval_suite([CASE_PATH], output_path=output_path)

    assert payload["schema_version"] == 1
    assert payload["created_at"] == "1970-01-01T00:00:00Z"
    assert payload["status"] == "PASS"
    assert payload["score"] == 1.0
    assert output_path.exists()
    written = read_json_file(output_path)
    assert written == payload

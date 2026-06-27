from pathlib import Path


def test_v1_4_release_readiness_doc_covers_diagnosis_report_eval_gate() -> None:
    text = Path("docs/v1.4.0_release_readiness.md").read_text(encoding="utf-8")

    assert "run-evals" in text
    assert "diagnosis_report_eval_case.json" in text
    assert "eval_results.json" in text
    assert "eval_report.md" in text
    assert "diagnosis_hypothesis_quality" in text
    assert "maintenance_recommendation_coverage" in text
    assert "evidence_completeness" in text
    assert "report_section_completeness" in text
    assert "safety_boundary_correctness" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
    assert "MAVLink command execution" in text
    assert "GitHub Actions" in text

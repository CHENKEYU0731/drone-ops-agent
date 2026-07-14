from pathlib import Path


def test_v2_2_release_readiness_documents_case_study_gate() -> None:
    text = Path("docs/v2.2.0_release_readiness.md").read_text(encoding="utf-8")

    assert "Evaluation and Case Study Baseline" in text
    assert "run-case-studies" in text
    assert "case_study_results.json" in text
    assert "case_study_report.md" in text
    assert "expected_status_accuracy=1.0" in text
    assert "evidence_coverage_rate=1.0" in text
    assert "false_alarm_count=0" in text
    assert "missed_risk_count=0" in text
    assert "result_digest" in text
    assert "Python 3.11" in text
    assert "Python 3.12" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text

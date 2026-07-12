from pathlib import Path


def test_v2_1_release_readiness_covers_demo_and_hardening_scope() -> None:
    text = Path("docs/v2.1.0_release_readiness.md").read_text(encoding="utf-8")

    assert "Demo and Portfolio Readiness" in text
    assert "python scripts/generate_demo_outputs.py --out demo_outputs" in text
    assert ".drone-ops-demo-output" in text
    assert "ops_report.pdf" in text
    assert "validate-platform-index" in text
    assert "validate-operations-platform" in text
    assert "REVIEW_REQUIRED" in text
    assert "human_review_required=true" in text
    assert "Python 3.11" in text
    assert "Python 3.12" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text

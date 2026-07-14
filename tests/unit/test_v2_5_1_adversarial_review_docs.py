from pathlib import Path


def test_v2_5_1_adversarial_review_records_fixes_and_residual_risk() -> None:
    review = Path("docs/v2.5.1_adversarial_review.md").read_text(encoding="utf-8")
    readiness = Path("docs/v2.5.1_release_readiness.md").read_text(encoding="utf-8")
    release = Path("docs/releases/v2.5.1-draft.md").read_text(encoding="utf-8")

    for text in (review, readiness, release):
        assert "offline-only" in text
        assert "advisory-only" in text
        assert "human-review-required" in text
        assert "MAVLink command" in text

    assert "managed 输出目录标记可伪造" in review
    assert "Dashboard DOM 注入" in review
    assert "质量门禁退出码不一致" in review
    assert "残余风险" in review
    assert "2.5.1" in release

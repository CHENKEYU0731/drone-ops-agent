from pathlib import Path


def test_v2_5_release_readiness_documents_portfolio_boundary() -> None:
    readiness = Path("docs/v2.5.0_release_readiness.md").read_text(encoding="utf-8")
    release = Path("docs/releases/v2.5.0-draft.md").read_text(encoding="utf-8")

    for text in (readiness, release):
        assert "offline-only" in text
        assert "advisory-only" in text
        assert "human-review-required" in text
        assert "MAVLink command" in text

    assert "sample_mock_sanitized_only=true" in readiness
    assert "real_world_accuracy_claimed=false" in readiness
    assert "scripts/verify_release.ps1" in readiness
    assert "2.5.0" in release

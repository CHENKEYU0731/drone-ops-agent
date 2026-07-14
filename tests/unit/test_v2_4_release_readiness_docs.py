from pathlib import Path


def test_v2_4_release_readiness_documents_reproducible_distribution() -> None:
    readiness = Path("docs/v2.4.0_release_readiness.md").read_text(encoding="utf-8")
    guide = Path("docs/reproducible_distribution.md").read_text(encoding="utf-8")
    release = Path("docs/releases/v2.4.0-draft.md").read_text(encoding="utf-8")

    for text in (readiness, guide, release):
        assert "offline-only" in text
        assert "advisory-only" in text
        assert "MAVLink command" in text

    assert "verify_release.ps1" in readiness
    assert "distribution_manifest.json" in readiness
    assert "SHA-256" in readiness
    assert "符号链接" in guide
    assert "2.4.0" in release

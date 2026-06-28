from pathlib import Path


def test_v1_9_release_readiness_doc_covers_platform_index_gate() -> None:
    text = Path("docs/v1.9.0_release_readiness.md").read_text(encoding="utf-8")

    assert "validate-platform-index" in text
    assert "platform_readiness_index.json" in text
    assert "platform_index_validation.json" in text
    assert "PlatformReadinessIndex" in text
    assert "PlatformReadinessCapability" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
    assert "真实维修系统" in text
    assert "GitHub Actions" in text

from pathlib import Path


def test_v2_0_release_readiness_doc_covers_operations_platform_gate() -> None:
    text = Path("docs/v2.0.0_release_readiness.md").read_text(encoding="utf-8")

    assert "validate-operations-platform" in text
    assert "operations_platform_baseline.json" in text
    assert "operations_platform_validation.json" in text
    assert "OperationsPlatformBaseline" in text
    assert "OperationsPlatformModule" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
    assert "真实维修系统" in text
    assert "GitHub Actions" in text

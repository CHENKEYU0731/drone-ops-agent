from pathlib import Path


def test_v1_6_release_readiness_doc_covers_dataset_registry_gate() -> None:
    text = Path("docs/v1.6.0_release_readiness.md").read_text(encoding="utf-8")

    assert "validate-datasets" in text
    assert "data/sample_datasets/registry.json" in text
    assert "dataset_validation.json" in text
    assert "DatasetCase" in text
    assert "DatasetRegistry" in text
    assert "sanitized" in text
    assert "mock_sample" in text
    assert "recommended_commands" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
    assert "MAVLink command execution" in text
    assert "GitHub Actions" in text

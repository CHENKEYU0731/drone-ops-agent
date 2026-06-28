from pathlib import Path


def test_v1_8_release_readiness_doc_covers_handoff_gate() -> None:
    text = Path("docs/v1.8.0_release_readiness.md").read_text(encoding="utf-8")

    assert "validate-handoff-package" in text
    assert "organization_handoff_package.json" in text
    assert "handoff_validation.json" in text
    assert "OrganizationHandoffPackage" in text
    assert "OrganizationHandoffArtifact" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
    assert "真实维修系统" in text
    assert "GitHub Actions" in text

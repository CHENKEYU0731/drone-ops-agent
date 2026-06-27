from pathlib import Path


def test_v1_5_release_readiness_doc_covers_platform_readiness_gate() -> None:
    text = Path("docs/v1.5.0_release_readiness.md").read_text(encoding="utf-8")

    assert "build-report-bundle" in text
    assert "validate-platform-readiness" in text
    assert "workspace_project.json" in text
    assert "report_bundle_manifest.json" in text
    assert "platform_readiness_checklist.json" in text
    assert "platform_readiness_validation.json" in text
    assert "offline adapter contract" in text
    assert "reviewer / approval model" in text
    assert "数据保留" in text
    assert "脱敏" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
    assert "MAVLink command execution" in text
    assert "GitHub Actions" in text

from pathlib import Path


def test_v1_7_release_readiness_doc_covers_adapter_approval_gate() -> None:
    text = Path("docs/v1.7.0_release_readiness.md").read_text(encoding="utf-8")

    assert "validate-adapters" in text
    assert "validate-approvals" in text
    assert "offline_adapter_registry.json" in text
    assert "approval_packet.json" in text
    assert "adapter_validation.json" in text
    assert "approval_validation.json" in text
    assert "OfflineAdapterRegistry" in text
    assert "ApprovalPacket" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
    assert "MAVLink command execution" in text
    assert "真实维修系统" in text
    assert "GitHub Actions" in text

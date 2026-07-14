from pathlib import Path


def test_v2_3_docs_preserve_provenance_and_safety_boundary() -> None:
    text = Path("docs/v2.3.0_release_readiness.md").read_text(encoding="utf-8")

    assert "Open-Source Upstream Log Compatibility" in text
    assert "BSD-3-Clause" in text
    assert "SHA-256" in text
    assert "all_real_world_flight_verified=false" in text
    assert "21、52、157" in text
    assert "Python 3.11" in text and "Python 3.12" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
    assert "不能称为“真实飞行日志准确率验证”" in text

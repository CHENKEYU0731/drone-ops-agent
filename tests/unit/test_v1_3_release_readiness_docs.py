from pathlib import Path


def test_v1_3_release_readiness_doc_covers_rule_governance_gate() -> None:
    text = Path("docs/v1.3.0_release_readiness.md").read_text(encoding="utf-8")

    assert "validate-rule-pack" in text
    assert "rule_pack_validation.json" in text
    assert "list-skills" in text
    assert "skill_registry.json" in text
    assert "list-rule-packs" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
    assert "MAVLink command execution" in text
    assert "GitHub Actions" in text

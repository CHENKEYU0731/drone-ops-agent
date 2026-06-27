from pathlib import Path

from packages.rule_packs import build_skill_registry


def test_build_skill_registry_returns_stable_offline_entries() -> None:
    registry = build_skill_registry(
        rule_pack_paths=[Path("data/sample_rule_packs/offline_default_rules.json")]
    )

    assert registry["schema_version"] == 1
    assert registry["registry_id"] == "SKILL-REGISTRY-OFFLINE"
    assert registry["generated_at"] == "1970-01-01T00:00:00Z"
    assert registry["human_review_required"] is True
    assert registry["safety_boundary"]["offline_only"] is True
    assert [item["skill_name"] for item in registry["skills"]] == sorted(
        item["skill_name"] for item in registry["skills"]
    )
    assert {
        "rule_pack_id": "offline-default-rules",
        "version": "1.3.0",
        "path": "data/sample_rule_packs/offline_default_rules.json",
    } in registry["rule_packs"]


def test_skill_registry_contains_core_cli_skills() -> None:
    registry = build_skill_registry(rule_pack_paths=[])
    names = {item["skill_name"] for item in registry["skills"]}

    assert {"validate-report", "validate-simulation", "generate-work-orders", "fleet-summary"} <= names

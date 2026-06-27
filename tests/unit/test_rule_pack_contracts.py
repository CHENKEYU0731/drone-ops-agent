from pathlib import Path

import pytest

from packages.drone_schemas import RulePack, RulePackRule, RulePackScope, load_model


def test_rule_pack_contract_supports_versioned_rules() -> None:
    rule = RulePackRule(
        rule_id="PREFLIGHT_BATTERY_MIN_SOC",
        version="1.0.0",
        scope=RulePackScope.PREFLIGHT,
        description="Battery SOC must stay above the offline preflight threshold.",
        severity="HIGH",
        inputs=["battery.soc_pct"],
        thresholds={"min_soc_pct": 25},
        evidence_fields=["battery.soc_pct"],
        human_review_required=True,
    )
    pack = RulePack(
        pack_id="offline-default-rules",
        name="Offline Default Rules",
        version="1.3.0",
        scope=RulePackScope.MIXED,
        rules=[rule],
        source_refs=["data/sample_rule_packs/offline_default_rules.json"],
        safety_boundary={
            "offline_only": True,
            "advisory_only": True,
            "no_real_drone_connection": True,
        },
    )

    assert pack.rule_count == 1
    assert pack.rules[0].rule_id == "PREFLIGHT_BATTERY_MIN_SOC"
    assert pack.human_review_required is True
    assert pack.generated_by_skill == "rule-pack-management"


def test_rule_pack_rejects_duplicate_rule_ids() -> None:
    rule = {
        "rule_id": "DUPLICATE_RULE",
        "version": "1.0.0",
        "scope": "PREFLIGHT",
        "description": "Duplicate rule id example.",
        "severity": "LOW",
        "inputs": ["asset.operational_status"],
        "thresholds": {},
        "evidence_fields": ["asset.operational_status"],
    }

    with pytest.raises(ValueError, match="duplicate rule_id"):
        RulePack(
            pack_id="duplicate-pack",
            name="Duplicate Pack",
            version="1.3.0",
            scope=RulePackScope.PREFLIGHT,
            rules=[RulePackRule(**rule), RulePackRule(**rule)],
            safety_boundary={"offline_only": True},
        )


def test_sample_rule_pack_fixture_loads() -> None:
    pack = load_model(Path("data/sample_rule_packs/offline_default_rules.json"), RulePack)

    assert pack.pack_id == "offline-default-rules"
    assert pack.version == "1.3.0"
    assert pack.rule_count >= 3
    assert [rule.rule_id for rule in pack.rules] == sorted(rule.rule_id for rule in pack.rules)
    assert pack.safety_boundary["offline_only"] is True

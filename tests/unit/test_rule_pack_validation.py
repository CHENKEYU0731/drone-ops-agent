from pathlib import Path

from packages.rule_packs import validate_rule_pack


def test_validate_rule_pack_accepts_sample_fixture() -> None:
    result = validate_rule_pack(Path("data/sample_rule_packs/offline_default_rules.json"))

    assert result["status"] == "PASS"
    assert result["counts"] == {
        "rules": 4,
        "findings": 0,
        "scopes": 4,
    }
    assert result["rule_pack"]["pack_id"] == "offline-default-rules"
    assert result["rule_pack"]["version"] == "1.3.0"
    assert result["safety_boundary"]["offline_only"] is True
    assert result["human_review_required"] is True


def test_validate_rule_pack_exposes_missing_evidence_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad_rule_pack.json"
    path.write_text(
        """
{
  "pack_id": "bad-pack",
  "name": "Bad Pack",
  "version": "1.3.0",
  "scope": "PREFLIGHT",
  "generated_by_skill": "rule-pack-management",
  "skill_version": "1.3.0",
  "rules": [
    {
      "rule_id": "BAD_RULE",
      "version": "1.0.0",
      "scope": "PREFLIGHT",
      "description": "Missing evidence field.",
      "severity": "LOW",
      "inputs": ["asset.operational_status"],
      "thresholds": {},
      "evidence_fields": []
    }
  ],
  "safety_boundary": {"offline_only": true}
}
""".strip(),
        encoding="utf-8",
    )

    result = validate_rule_pack(path)

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["findings"] == [
        {
            "code": "RULE_MISSING_EVIDENCE_FIELDS",
            "severity": "MEDIUM",
            "rule_id": "BAD_RULE",
            "message": "Rule BAD_RULE should declare at least one evidence field.",
        }
    ]

from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import RulePack, load_model


REGISTRY_GENERATED_AT = "1970-01-01T00:00:00Z"


CORE_SKILLS = [
    {"skill_name": "analyze-log", "skill_version": "1.0.0", "category": "analysis"},
    {"skill_name": "dashboard-bundle", "skill_version": "1.2.0", "category": "dashboard"},
    {"skill_name": "fleet-summary", "skill_version": "1.1.0", "category": "fleet-health"},
    {"skill_name": "generate-report", "skill_version": "1.0.0", "category": "reporting"},
    {"skill_name": "generate-work-orders", "skill_version": "1.0.0", "category": "work-orders"},
    {"skill_name": "preflight-check", "skill_version": "1.0.0", "category": "preflight"},
    {"skill_name": "validate-report", "skill_version": "1.0.0", "category": "validation"},
    {"skill_name": "validate-rule-pack", "skill_version": "1.3.0", "category": "rule-governance"},
    {"skill_name": "validate-simulation", "skill_version": "1.0.0", "category": "simulation"},
]


def build_skill_registry(*, rule_pack_paths: list[Path]) -> dict[str, Any]:
    rule_packs = list_rule_pack_refs(rule_pack_paths)
    return {
        "schema_version": 1,
        "registry_id": "SKILL-REGISTRY-OFFLINE",
        "generated_at": REGISTRY_GENERATED_AT,
        "skills": sorted(CORE_SKILLS, key=lambda item: item["skill_name"]),
        "rule_packs": rule_packs,
        "safety_boundary": {
            "offline_only": True,
            "advisory_only": True,
            "read_only": True,
            "no_real_drone_connection": True,
            "no_external_platform_connection": True,
        },
        "human_review_required": True,
    }


def list_rule_pack_refs(rule_pack_paths: list[Path]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for path in rule_pack_paths:
        pack = load_model(path, RulePack)
        refs.append(
            {
                "rule_pack_id": pack.pack_id,
                "version": pack.version,
                "path": path.as_posix(),
            }
        )
    return sorted(refs, key=lambda item: (item["rule_pack_id"], item["version"], item["path"]))

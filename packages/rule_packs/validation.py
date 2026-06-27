from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import RulePack, load_model


VALIDATION_CREATED_AT = "1970-01-01T00:00:00Z"


def validate_rule_pack(path: Path) -> dict[str, Any]:
    pack = load_model(path, RulePack)
    findings = _collect_findings(pack)
    scopes = sorted({rule.scope.value for rule in pack.rules})
    return {
        "schema_version": 1,
        "validation_id": f"RULEPACK-VALIDATION-{pack.pack_id}",
        "created_at": VALIDATION_CREATED_AT,
        "status": "PASS" if not findings else "REVIEW_REQUIRED",
        "rule_pack": {
            "pack_id": pack.pack_id,
            "name": pack.name,
            "version": pack.version,
            "scope": pack.scope.value,
        },
        "counts": {
            "rules": pack.rule_count,
            "findings": len(findings),
            "scopes": len(scopes),
        },
        "scopes": scopes,
        "findings": findings,
        "safety_boundary": {
            "offline_only": bool(pack.safety_boundary.get("offline_only")),
            "advisory_only": bool(pack.safety_boundary.get("advisory_only")),
            "no_real_drone_connection": bool(pack.safety_boundary.get("no_real_drone_connection")),
            "no_mavlink_command_execution": bool(pack.safety_boundary.get("no_mavlink_command_execution")),
            "no_external_platform_connection": bool(pack.safety_boundary.get("no_external_platform_connection")),
        },
        "human_review_required": True,
        "source_refs": [str(path), *pack.source_refs],
    }


def _collect_findings(pack: RulePack) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for rule in pack.rules:
        if not rule.evidence_fields:
            findings.append(
                {
                    "code": "RULE_MISSING_EVIDENCE_FIELDS",
                    "severity": "MEDIUM",
                    "rule_id": rule.rule_id,
                    "message": f"Rule {rule.rule_id} should declare at least one evidence field.",
                }
            )
        if not rule.inputs:
            findings.append(
                {
                    "code": "RULE_MISSING_INPUTS",
                    "severity": "MEDIUM",
                    "rule_id": rule.rule_id,
                    "message": f"Rule {rule.rule_id} should declare at least one input.",
                }
            )
    return sorted(findings, key=lambda item: (item["rule_id"], item["code"]))

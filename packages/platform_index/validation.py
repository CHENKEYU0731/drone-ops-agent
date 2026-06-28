from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import PlatformReadinessIndex, load_model


CREATED_AT = "1970-01-01T00:00:00Z"


def validate_platform_index(path: Path) -> dict[str, Any]:
    index = load_model(path, PlatformReadinessIndex)
    findings = _collect_findings(index)
    versions = sorted({capability.version for capability in index.capabilities})
    return {
        "schema_version": 1,
        "validation_id": f"PLATFORM-INDEX-VALIDATION-{index.index_id}",
        "created_at": CREATED_AT,
        "status": "PASS" if not findings else "REVIEW_REQUIRED",
        "platform_index": {
            "index_id": index.index_id,
            "version": index.version,
        },
        "counts": {
            "capabilities": index.capability_count,
            "versions": len(versions),
            "required_release_checks": len(index.required_release_checks),
            "findings": len(findings),
        },
        "versions": versions,
        "required_release_checks": index.required_release_checks,
        "findings": findings,
        "safety_boundary": {
            "offline_only": bool(index.safety_boundary.get("offline_only")),
            "advisory_only": bool(index.safety_boundary.get("advisory_only")),
            "human_review_required": bool(index.safety_boundary.get("human_review_required")),
            "no_real_drone_connection": bool(index.safety_boundary.get("no_real_drone_connection")),
            "no_mavlink_command_execution": bool(index.safety_boundary.get("no_mavlink_command_execution")),
            "no_external_platform_connection": bool(index.safety_boundary.get("no_external_platform_connection")),
            "no_auto_dispatch": bool(index.safety_boundary.get("no_auto_dispatch")),
        },
        "human_review_required": True,
        "source_refs": [str(path), *[ref for capability in index.capabilities for ref in capability.output_refs]],
    }


def _collect_findings(index: PlatformReadinessIndex) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if index.safety_boundary.get("offline_only") is not True:
        findings.append(_finding("PLATFORM_INDEX_OFFLINE_BOUNDARY_MISSING", index.index_id, "Index missing offline_only=true."))
    if index.safety_boundary.get("advisory_only") is not True:
        findings.append(_finding("PLATFORM_INDEX_ADVISORY_BOUNDARY_MISSING", index.index_id, "Index missing advisory_only=true."))
    if index.safety_boundary.get("no_external_platform_connection") is not True:
        findings.append(
            _finding(
                "PLATFORM_INDEX_PLATFORM_BOUNDARY_MISSING",
                index.index_id,
                "Index must declare no_external_platform_connection=true.",
            )
        )
    if index.safety_boundary.get("no_auto_dispatch") is not True:
        findings.append(_finding("PLATFORM_INDEX_AUTO_DISPATCH_BOUNDARY_MISSING", index.index_id, "Index must prohibit auto dispatch."))
    if "pytest" not in index.required_release_checks:
        findings.append(_finding("PLATFORM_INDEX_PYTEST_CHECK_MISSING", index.index_id, "Index should require pytest."))

    for capability in index.capabilities:
        if not capability.commands:
            findings.append(
                _finding(
                    "PLATFORM_CAPABILITY_COMMANDS_MISSING",
                    capability.capability_id,
                    f"Capability {capability.capability_id} must include at least one command.",
                )
            )
        if not capability.output_refs:
            findings.append(
                _finding(
                    "PLATFORM_CAPABILITY_OUTPUT_REFS_MISSING",
                    capability.capability_id,
                    f"Capability {capability.capability_id} must include output refs.",
                )
            )
        if capability.human_review_required is not True:
            findings.append(
                _finding(
                    "PLATFORM_CAPABILITY_REVIEW_MISSING",
                    capability.capability_id,
                    f"Capability {capability.capability_id} must require human review.",
                )
            )
        if "offline-only" not in capability.safety_notes or "advisory-only" not in capability.safety_notes:
            findings.append(
                _finding(
                    "PLATFORM_CAPABILITY_SAFETY_NOTES_INCOMPLETE",
                    capability.capability_id,
                    f"Capability {capability.capability_id} should declare offline-only and advisory-only.",
                )
            )

    return sorted(findings, key=lambda item: (item["subject_id"], item["code"], item["message"]))


def _finding(code: str, subject_id: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "HIGH" if "MISSING" in code else "MEDIUM",
        "subject_id": subject_id,
        "message": message,
    }

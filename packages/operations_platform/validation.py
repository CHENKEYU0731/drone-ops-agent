from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import OperationsPlatformBaseline, load_model


CREATED_AT = "1970-01-01T00:00:00Z"


def validate_operations_platform(path: Path) -> dict[str, Any]:
    baseline = load_model(path, OperationsPlatformBaseline)
    findings = _collect_findings(baseline)
    source_versions = sorted({module.source_version for module in baseline.modules})
    reviewer_roles = sorted({role for module in baseline.modules for role in module.reviewer_roles})
    return {
        "schema_version": 1,
        "validation_id": f"OPS-PLATFORM-VALIDATION-{baseline.baseline_id}",
        "created_at": CREATED_AT,
        "status": "PASS" if not findings else "REVIEW_REQUIRED",
        "operations_platform": {
            "baseline_id": baseline.baseline_id,
            "version": baseline.version,
            "title": baseline.title,
        },
        "counts": {
            "modules": baseline.module_count,
            "source_versions": len(source_versions),
            "reviewer_roles": len(reviewer_roles),
            "release_checks": len(baseline.release_checks),
            "findings": len(findings),
        },
        "module_ids": [module.module_id for module in baseline.modules],
        "source_versions": source_versions,
        "reviewer_roles": reviewer_roles,
        "release_checks": baseline.release_checks,
        "findings": findings,
        "safety_boundary": {
            "offline_only": bool(baseline.safety_boundary.get("offline_only")),
            "advisory_only": bool(baseline.safety_boundary.get("advisory_only")),
            "human_review_required": bool(baseline.safety_boundary.get("human_review_required")),
            "no_real_drone_connection": bool(baseline.safety_boundary.get("no_real_drone_connection")),
            "no_mavlink_command_execution": bool(baseline.safety_boundary.get("no_mavlink_command_execution")),
            "no_external_platform_connection": bool(baseline.safety_boundary.get("no_external_platform_connection")),
            "no_real_maintenance_system": bool(baseline.safety_boundary.get("no_real_maintenance_system")),
            "no_auto_dispatch": bool(baseline.safety_boundary.get("no_auto_dispatch")),
            "no_simulator_launch": bool(baseline.safety_boundary.get("no_simulator_launch")),
        },
        "human_review_required": True,
        "source_refs": [str(path), *[ref for module in baseline.modules for ref in module.artifact_refs]],
    }


def _collect_findings(baseline: OperationsPlatformBaseline) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required_boundaries = {
        "offline_only": "OPS_PLATFORM_OFFLINE_BOUNDARY_MISSING",
        "advisory_only": "OPS_PLATFORM_ADVISORY_BOUNDARY_MISSING",
        "human_review_required": "OPS_PLATFORM_REVIEW_BOUNDARY_MISSING",
        "no_real_drone_connection": "OPS_PLATFORM_DRONE_BOUNDARY_MISSING",
        "no_mavlink_command_execution": "OPS_PLATFORM_MAVLINK_BOUNDARY_MISSING",
        "no_external_platform_connection": "OPS_PLATFORM_EXTERNAL_PLATFORM_BOUNDARY_MISSING",
        "no_real_maintenance_system": "OPS_PLATFORM_MAINTENANCE_BOUNDARY_MISSING",
        "no_auto_dispatch": "OPS_PLATFORM_AUTO_DISPATCH_BOUNDARY_MISSING",
        "no_simulator_launch": "OPS_PLATFORM_SIMULATOR_BOUNDARY_MISSING",
    }
    for flag, code in required_boundaries.items():
        if baseline.safety_boundary.get(flag) is not True:
            findings.append(_finding(code, baseline.baseline_id, f"Baseline must declare {flag}=true."))

    for release_check in ("pytest", "validate-operations-platform"):
        if release_check not in baseline.release_checks:
            findings.append(
                _finding(
                    "OPS_PLATFORM_RELEASE_CHECK_MISSING",
                    baseline.baseline_id,
                    f"Baseline should require {release_check}.",
                )
            )

    for module in baseline.modules:
        if not module.artifact_refs:
            findings.append(
                _finding(
                    "OPS_PLATFORM_MODULE_ARTIFACT_REFS_MISSING",
                    module.module_id,
                    f"Module {module.module_id} must include artifact refs.",
                )
            )
        if not module.validation_commands:
            findings.append(
                _finding(
                    "OPS_PLATFORM_MODULE_VALIDATION_COMMANDS_MISSING",
                    module.module_id,
                    f"Module {module.module_id} must include validation commands.",
                )
            )
        if not module.expected_outputs:
            findings.append(
                _finding(
                    "OPS_PLATFORM_MODULE_EXPECTED_OUTPUTS_MISSING",
                    module.module_id,
                    f"Module {module.module_id} must include expected outputs.",
                )
            )
        if not module.reviewer_roles:
            findings.append(
                _finding(
                    "OPS_PLATFORM_MODULE_REVIEWER_ROLES_MISSING",
                    module.module_id,
                    f"Module {module.module_id} must include reviewer roles.",
                )
            )
        if module.human_review_required is not True:
            findings.append(
                _finding(
                    "OPS_PLATFORM_MODULE_REVIEW_MISSING",
                    module.module_id,
                    f"Module {module.module_id} must require human review.",
                )
            )
        for required_note in ("offline-only", "advisory-only", "human-review-required"):
            if required_note not in module.safety_notes:
                findings.append(
                    _finding(
                        "OPS_PLATFORM_MODULE_SAFETY_NOTES_INCOMPLETE",
                        module.module_id,
                        f"Module {module.module_id} should declare {required_note}.",
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

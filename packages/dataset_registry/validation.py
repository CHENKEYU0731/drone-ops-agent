from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import DatasetRegistry, load_model


CREATED_AT = "1970-01-01T00:00:00Z"
ALLOWED_SANITIZED_STATUS = {"sanitized_sample", "mock_sample", "placeholder", "synthetic_sample"}


def validate_dataset_registry(path: Path) -> dict[str, Any]:
    registry = load_model(path, DatasetRegistry)
    findings = _collect_findings(registry, path.parent)
    case_types = sorted({case.case_type for case in registry.cases})
    capabilities = sorted({capability for case in registry.cases for capability in case.capabilities})
    return {
        "schema_version": 1,
        "validation_id": f"DATASET-VALIDATION-{registry.registry_id}",
        "created_at": CREATED_AT,
        "status": "PASS" if not findings else "REVIEW_REQUIRED",
        "registry": {
            "registry_id": registry.registry_id,
            "version": registry.version,
        },
        "counts": {
            "cases": registry.case_count,
            "case_types": len(case_types),
            "capabilities": len(capabilities),
            "findings": len(findings),
        },
        "case_types": case_types,
        "capabilities": capabilities,
        "findings": findings,
        "safety_boundary": {
            "offline_only": bool(registry.safety_boundary.get("offline_only")),
            "advisory_only": bool(registry.safety_boundary.get("advisory_only")),
            "human_review_required": bool(registry.safety_boundary.get("human_review_required")),
            "no_real_drone_connection": bool(registry.safety_boundary.get("no_real_drone_connection")),
            "no_mavlink_command_execution": bool(registry.safety_boundary.get("no_mavlink_command_execution")),
            "no_external_platform_connection": bool(registry.safety_boundary.get("no_external_platform_connection")),
        },
        "human_review_required": True,
        "source_refs": [str(path), *registry.source_refs],
    }


def _collect_findings(registry: DatasetRegistry, base_dir: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if registry.safety_boundary.get("offline_only") is not True:
        findings.append(_finding("REGISTRY_OFFLINE_BOUNDARY_MISSING", registry.registry_id, "Registry missing offline_only=true."))
    if registry.safety_boundary.get("advisory_only") is not True:
        findings.append(_finding("REGISTRY_ADVISORY_BOUNDARY_MISSING", registry.registry_id, "Registry missing advisory_only=true."))
    for case in registry.cases:
        if case.sanitized_status not in ALLOWED_SANITIZED_STATUS:
            findings.append(
                _finding(
                    "SANITIZED_STATUS_UNAPPROVED",
                    case.case_id,
                    f"Case {case.case_id} has unapproved sanitized_status={case.sanitized_status}.",
                )
            )
        if not case.source_refs:
            findings.append(_finding("SOURCE_REFS_EMPTY", case.case_id, f"Case {case.case_id} has no source refs."))
        for source_ref in case.source_refs:
            if not _resolve_ref(source_ref, base_dir).exists():
                findings.append(_finding("SOURCE_REF_MISSING", case.case_id, f"Case {case.case_id} source ref missing: {source_ref}."))
        if not case.recommended_commands:
            findings.append(_finding("RECOMMENDED_COMMANDS_EMPTY", case.case_id, f"Case {case.case_id} has no recommended commands."))
        if not case.expected_outputs:
            findings.append(_finding("EXPECTED_OUTPUTS_EMPTY", case.case_id, f"Case {case.case_id} has no expected outputs."))
        if case.safety_boundary.get("offline_only") is not True:
            findings.append(_finding("CASE_OFFLINE_BOUNDARY_MISSING", case.case_id, f"Case {case.case_id} missing offline_only=true."))
        if case.safety_boundary.get("advisory_only") is not True:
            findings.append(_finding("CASE_ADVISORY_BOUNDARY_MISSING", case.case_id, f"Case {case.case_id} missing advisory_only=true."))
        if case.human_review_required is not True:
            findings.append(_finding("HUMAN_REVIEW_REQUIRED_MISSING", case.case_id, f"Case {case.case_id} must require human review."))
    return sorted(findings, key=lambda item: (item["case_id"], item["code"], item["message"]))


def _resolve_ref(source_ref: str, base_dir: Path) -> Path:
    path = Path(source_ref)
    if path.is_absolute() or path.exists():
        return path
    return base_dir / path


def _finding(code: str, case_id: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "HIGH" if "MISSING" in code else "MEDIUM",
        "case_id": case_id,
        "message": message,
    }

from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import OrganizationHandoffPackage, load_model


CREATED_AT = "1970-01-01T00:00:00Z"


def validate_handoff_package(path: Path) -> dict[str, Any]:
    package = load_model(path, OrganizationHandoffPackage)
    findings = _collect_findings(package, path.parent)
    artifact_types = sorted({artifact.artifact_type for artifact in package.artifact_refs})
    return {
        "schema_version": 1,
        "validation_id": f"HANDOFF-VALIDATION-{package.package_id}",
        "created_at": CREATED_AT,
        "status": "PASS" if not findings else "REVIEW_REQUIRED",
        "handoff_package": {
            "package_id": package.package_id,
            "version": package.version,
            "workspace_project_id": package.workspace_project_id,
        },
        "counts": {
            "artifacts": package.artifact_count,
            "artifact_types": len(artifact_types),
            "reviewer_roles": len(package.reviewer_roles),
            "findings": len(findings),
        },
        "artifact_types": artifact_types,
        "reviewer_roles": package.reviewer_roles,
        "findings": findings,
        "safety_boundary": {
            "offline_only": bool(package.safety_boundary.get("offline_only")),
            "advisory_only": bool(package.safety_boundary.get("advisory_only")),
            "human_review_required": bool(package.safety_boundary.get("human_review_required")),
            "no_real_drone_connection": bool(package.safety_boundary.get("no_real_drone_connection")),
            "no_external_platform_connection": bool(package.safety_boundary.get("no_external_platform_connection")),
            "no_auto_dispatch": bool(package.safety_boundary.get("no_auto_dispatch")),
        },
        "human_review_required": True,
        "source_refs": [str(path), *[artifact.path for artifact in package.artifact_refs]],
    }


def _collect_findings(package: OrganizationHandoffPackage, base_dir: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if package.safety_boundary.get("offline_only") is not True:
        findings.append(_finding("HANDOFF_OFFLINE_BOUNDARY_MISSING", package.package_id, "Package missing offline_only=true."))
    if package.safety_boundary.get("advisory_only") is not True:
        findings.append(_finding("HANDOFF_ADVISORY_BOUNDARY_MISSING", package.package_id, "Package missing advisory_only=true."))
    if package.safety_boundary.get("no_external_platform_connection") is not True:
        findings.append(
            _finding(
                "HANDOFF_PLATFORM_BOUNDARY_MISSING",
                package.package_id,
                "Package must declare no_external_platform_connection=true.",
            )
        )
    if package.safety_boundary.get("no_auto_dispatch") is not True:
        findings.append(_finding("HANDOFF_AUTO_DISPATCH_BOUNDARY_MISSING", package.package_id, "Package must prohibit auto dispatch."))
    if not package.reviewer_roles:
        findings.append(_finding("HANDOFF_REVIEWER_ROLES_MISSING", package.package_id, "Package should declare reviewer roles."))

    for artifact in package.artifact_refs:
        if artifact.required and not _resolve_ref(artifact.path, base_dir).exists():
            findings.append(_finding("HANDOFF_ARTIFACT_MISSING", artifact.artifact_id, f"Required artifact missing: {artifact.path}."))
        if artifact.human_review_required is not True:
            findings.append(_finding("HANDOFF_ARTIFACT_REVIEW_MISSING", artifact.artifact_id, f"Artifact {artifact.artifact_id} must require human review."))
        if not artifact.description.strip():
            findings.append(_finding("HANDOFF_ARTIFACT_DESCRIPTION_MISSING", artifact.artifact_id, f"Artifact {artifact.artifact_id} missing description."))

    return sorted(findings, key=lambda item: (item["subject_id"], item["code"], item["message"]))


def _resolve_ref(source_ref: str, base_dir: Path) -> Path:
    path = Path(source_ref)
    if path.is_absolute() or path.exists():
        return path
    return base_dir / path


def _finding(code: str, subject_id: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "HIGH" if "MISSING" in code else "MEDIUM",
        "subject_id": subject_id,
        "message": message,
    }

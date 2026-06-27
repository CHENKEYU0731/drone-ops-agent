from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import (
    OfflineAdapterContract,
    PlatformReadinessChecklist,
    ReportBundleManifest,
    WorkspaceProject,
    load_model,
)


CREATED_AT = "1970-01-01T00:00:00Z"


def validate_platform_readiness(
    *,
    workspace_path: Path,
    bundle_path: Path,
    checklist_path: Path,
    adapter_paths: list[Path] | None = None,
) -> dict[str, Any]:
    adapters = adapter_paths or []
    workspace = load_model(workspace_path, WorkspaceProject)
    bundle = load_model(bundle_path, ReportBundleManifest)
    checklist = load_model(checklist_path, PlatformReadinessChecklist)
    adapter_contracts = [load_model(path, OfflineAdapterContract) for path in adapters]
    findings = _collect_findings(workspace, bundle, checklist, adapter_contracts)
    return {
        "schema_version": 1,
        "validation_id": f"PLATFORM-READINESS-{workspace.project_id}",
        "created_at": CREATED_AT,
        "status": "PASS" if not findings else "REVIEW_REQUIRED",
        "workspace_project_id": workspace.project_id,
        "bundle_id": bundle.bundle_id,
        "checklist_id": checklist.checklist_id,
        "counts": {
            "bundled_files": bundle.file_count,
            "checks": len(checklist.checks),
            "adapter_contracts": len(adapter_contracts),
            "findings": len(findings),
        },
        "findings": findings,
        "safety_boundary": {
            "offline_only": bool(
                workspace.safety_boundary.get("offline_only")
                and bundle.safety_boundary.get("offline_only")
                and checklist.safety_boundary.get("offline_only")
            ),
            "advisory_only": bool(
                workspace.safety_boundary.get("advisory_only")
                and bundle.safety_boundary.get("advisory_only")
                and checklist.safety_boundary.get("advisory_only")
            ),
            "no_real_drone_connection": bool(checklist.safety_boundary.get("no_real_drone_connection")),
            "no_mavlink_command_execution": bool(checklist.safety_boundary.get("no_mavlink_command_execution")),
            "no_external_platform_connection": bool(checklist.safety_boundary.get("no_external_platform_connection")),
            "no_auto_dispatch": bool(checklist.safety_boundary.get("no_auto_dispatch")),
        },
        "human_review_required": True,
        "checked_files": {
            "workspace": str(workspace_path),
            "bundle": str(bundle_path),
            "checklist": str(checklist_path),
            "adapters": [str(path) for path in adapters],
        },
    }


def _collect_findings(
    workspace: WorkspaceProject,
    bundle: ReportBundleManifest,
    checklist: PlatformReadinessChecklist,
    adapters: list[OfflineAdapterContract],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if bundle.workspace_project_id != workspace.project_id:
        findings.append(
            {
                "code": "BUNDLE_WORKSPACE_MISMATCH",
                "severity": "HIGH",
                "message": f"Bundle {bundle.bundle_id} references {bundle.workspace_project_id}, expected {workspace.project_id}.",
            }
        )
    for label, boundary in [
        ("workspace", workspace.safety_boundary),
        ("bundle", bundle.safety_boundary),
        ("checklist", checklist.safety_boundary),
    ]:
        if boundary.get("offline_only") is not True:
            findings.append({"code": "OFFLINE_BOUNDARY_MISSING", "severity": "HIGH", "message": f"{label} missing offline_only=true."})
        if boundary.get("advisory_only") is not True:
            findings.append({"code": "ADVISORY_BOUNDARY_MISSING", "severity": "HIGH", "message": f"{label} missing advisory_only=true."})
    if not workspace.reviewer_roles:
        findings.append({"code": "REVIEWER_ROLES_MISSING", "severity": "MEDIUM", "message": "Workspace should declare reviewer roles."})
    if not bundle.file_refs:
        findings.append({"code": "BUNDLE_FILES_MISSING", "severity": "HIGH", "message": "Report bundle manifest has no file refs."})
    if not checklist.checks:
        findings.append({"code": "CHECKLIST_EMPTY", "severity": "HIGH", "message": "Platform readiness checklist has no checks."})
    for adapter in adapters:
        prohibited = set(adapter.prohibited_operations)
        required = {"api_call", "auto_dispatch", "mavlink_command"}
        missing = sorted(required - prohibited)
        if missing:
            findings.append(
                {
                    "code": "ADAPTER_PROHIBITIONS_INCOMPLETE",
                    "severity": "HIGH",
                    "message": f"Adapter {adapter.adapter_id} missing prohibited operations: {', '.join(missing)}.",
                }
            )
    return sorted(findings, key=lambda item: (item["code"], item["message"]))

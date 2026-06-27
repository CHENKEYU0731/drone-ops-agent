from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import ApprovalPacket, OfflineAdapterRegistry, load_model


CREATED_AT = "1970-01-01T00:00:00Z"
REQUIRED_PROHIBITED_OPERATIONS = {"api_call", "auto_dispatch", "mavlink_command"}


def validate_adapter_registry(path: Path) -> dict[str, Any]:
    registry = load_model(path, OfflineAdapterRegistry)
    findings = _collect_registry_findings(registry)
    adapter_types = sorted({adapter.adapter_type for adapter in registry.adapters})
    return {
        "schema_version": 1,
        "validation_id": f"ADAPTER-VALIDATION-{registry.registry_id}",
        "created_at": CREATED_AT,
        "status": "PASS" if not findings else "REVIEW_REQUIRED",
        "registry": {
            "registry_id": registry.registry_id,
            "version": registry.version,
        },
        "counts": {
            "adapters": registry.adapter_count,
            "adapter_types": len(adapter_types),
            "findings": len(findings),
        },
        "adapter_types": adapter_types,
        "findings": findings,
        "safety_boundary": {
            "offline_only": bool(registry.safety_boundary.get("offline_only")),
            "advisory_only": bool(registry.safety_boundary.get("advisory_only")),
            "human_review_required": bool(registry.safety_boundary.get("human_review_required")),
            "no_real_drone_connection": bool(registry.safety_boundary.get("no_real_drone_connection")),
            "no_mavlink_command_execution": bool(registry.safety_boundary.get("no_mavlink_command_execution")),
            "no_external_platform_connection": bool(registry.safety_boundary.get("no_external_platform_connection")),
            "no_auto_dispatch": bool(registry.safety_boundary.get("no_auto_dispatch")),
        },
        "human_review_required": True,
        "source_refs": [str(path), *registry.source_refs],
    }


def validate_approval_packet(path: Path) -> dict[str, Any]:
    packet = load_model(path, ApprovalPacket)
    findings = _collect_approval_findings(packet)
    reviewer_roles = sorted({approval.reviewer_role for approval in packet.approvals})
    return {
        "schema_version": 1,
        "validation_id": f"APPROVAL-VALIDATION-{packet.packet_id}",
        "created_at": CREATED_AT,
        "status": "PASS" if not findings else "REVIEW_REQUIRED",
        "approval_packet": {
            "packet_id": packet.packet_id,
            "subject_ref": packet.subject_ref,
        },
        "counts": {
            "approvals": packet.approval_count,
            "required_roles": len(packet.required_roles),
            "findings": len(findings),
        },
        "required_roles": packet.required_roles,
        "reviewer_roles": reviewer_roles,
        "findings": findings,
        "safety_boundary": {
            "offline_only": bool(packet.safety_boundary.get("offline_only")),
            "advisory_only": bool(packet.safety_boundary.get("advisory_only")),
            "human_review_required": bool(packet.safety_boundary.get("human_review_required", True)),
        },
        "human_review_required": True,
        "source_refs": [str(path)],
    }


def _collect_registry_findings(registry: OfflineAdapterRegistry) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if registry.safety_boundary.get("offline_only") is not True:
        findings.append(_finding("REGISTRY_OFFLINE_BOUNDARY_MISSING", registry.registry_id, "Registry missing offline_only=true."))
    if registry.safety_boundary.get("advisory_only") is not True:
        findings.append(_finding("REGISTRY_ADVISORY_BOUNDARY_MISSING", registry.registry_id, "Registry missing advisory_only=true."))
    if registry.safety_boundary.get("no_auto_dispatch") is not True:
        findings.append(_finding("REGISTRY_AUTO_DISPATCH_BOUNDARY_MISSING", registry.registry_id, "Registry must prohibit auto dispatch."))

    for adapter in registry.adapters:
        missing = sorted(REQUIRED_PROHIBITED_OPERATIONS - set(adapter.prohibited_operations))
        if missing:
            findings.append(
                _finding(
                    "ADAPTER_PROHIBITED_OPERATIONS_INCOMPLETE",
                    adapter.adapter_id,
                    f"Adapter {adapter.adapter_id} missing prohibited operations: {', '.join(missing)}.",
                )
            )
        if adapter.safety_boundary.get("offline_only") is not True:
            findings.append(_finding("ADAPTER_OFFLINE_BOUNDARY_MISSING", adapter.adapter_id, f"Adapter {adapter.adapter_id} missing offline_only=true."))
        if adapter.safety_boundary.get("advisory_only") is not True:
            findings.append(_finding("ADAPTER_ADVISORY_BOUNDARY_MISSING", adapter.adapter_id, f"Adapter {adapter.adapter_id} missing advisory_only=true."))
        if adapter.safety_boundary.get("no_real_platform_connection") is not True:
            findings.append(
                _finding(
                    "ADAPTER_REAL_PLATFORM_BOUNDARY_MISSING",
                    adapter.adapter_id,
                    f"Adapter {adapter.adapter_id} must declare no_real_platform_connection=true.",
                )
            )
        if adapter.human_review_required is not True:
            findings.append(_finding("ADAPTER_HUMAN_REVIEW_MISSING", adapter.adapter_id, f"Adapter {adapter.adapter_id} must require human review."))

    return sorted(findings, key=lambda item: (item["subject_id"], item["code"], item["message"]))


def _collect_approval_findings(packet: ApprovalPacket) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not packet.subject_ref.strip():
        findings.append(_finding("APPROVAL_SUBJECT_REF_MISSING", packet.packet_id, "Approval packet must include subject_ref."))
    if packet.safety_boundary.get("offline_only") is not True:
        findings.append(_finding("APPROVAL_OFFLINE_BOUNDARY_MISSING", packet.packet_id, "Approval packet missing offline_only=true."))
    if packet.safety_boundary.get("advisory_only") is not True:
        findings.append(_finding("APPROVAL_ADVISORY_BOUNDARY_MISSING", packet.packet_id, "Approval packet missing advisory_only=true."))

    approved_roles = {approval.reviewer_role for approval in packet.approvals if approval.reviewer_role}
    for role in packet.required_roles:
        if role not in approved_roles:
            findings.append(_finding("APPROVAL_REQUIRED_ROLE_MISSING", role, f"Required reviewer role missing: {role}."))

    for approval in packet.approvals:
        if approval.subject_ref != packet.subject_ref:
            findings.append(
                _finding(
                    "APPROVAL_SUBJECT_MISMATCH",
                    approval.approval_id,
                    f"Approval {approval.approval_id} references {approval.subject_ref}, expected {packet.subject_ref}.",
                )
            )
        if not approval.reviewer_id.strip():
            findings.append(_finding("APPROVAL_REVIEWER_MISSING", approval.approval_id, f"Approval {approval.approval_id} missing reviewer_id."))
        if not approval.reviewer_role.strip():
            findings.append(_finding("APPROVAL_ROLE_MISSING", approval.approval_id, f"Approval {approval.approval_id} missing reviewer_role."))
        if not approval.decision.strip():
            findings.append(_finding("APPROVAL_DECISION_MISSING", approval.approval_id, f"Approval {approval.approval_id} missing decision."))
        if not approval.rationale.strip():
            findings.append(_finding("APPROVAL_RATIONALE_MISSING", approval.approval_id, f"Approval {approval.approval_id} missing rationale."))
        if approval.human_review_required is not True:
            findings.append(_finding("APPROVAL_HUMAN_REVIEW_MISSING", approval.approval_id, f"Approval {approval.approval_id} must require human review."))

    return sorted(findings, key=lambda item: (item["subject_id"], item["code"], item["message"]))


def _finding(code: str, subject_id: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "HIGH" if "MISSING" in code or "INCOMPLETE" in code else "MEDIUM",
        "subject_id": subject_id,
        "message": message,
    }

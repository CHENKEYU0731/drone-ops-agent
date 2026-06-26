from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


DETERMINISTIC_VALIDATION_CREATED_AT = datetime(1970, 1, 1, tzinfo=UTC)
REQUIRED_DRAFT_FIELDS = [
    "work_order_id",
    "asset_id",
    "component",
    "priority",
    "action",
    "reason",
    "evidence_refs",
    "required_approval",
    "estimated_effort",
    "status",
    "source_recommendation_id",
    "human_review_required",
]


class WorkOrderValidationCounts(BaseModel):
    validated_drafts: int = 0
    evidence_refs: int = 0


class WorkOrderValidationResult(BaseModel):
    status: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    counts: WorkOrderValidationCounts = Field(default_factory=WorkOrderValidationCounts)
    checked_files: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = DETERMINISTIC_VALIDATION_CREATED_AT

    def serializable_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class WorkOrderValidationError(ValueError):
    def __init__(self, errors: list[str], result: WorkOrderValidationResult):
        super().__init__("\n".join(errors))
        self.errors = errors
        self.result = result


def validate_work_order_drafts(
    drafts: list[dict[str, Any]],
    checked_files: dict[str, str] | None = None,
) -> WorkOrderValidationResult:
    errors: list[str] = []
    evidence_ref_count = 0

    for index, draft in enumerate(drafts):
        prefix = f"work_order_drafts[{index}]"
        _require_fields(draft, REQUIRED_DRAFT_FIELDS, prefix, errors)
        if draft.get("status") != "DRAFT":
            errors.append(f"{prefix} status must be DRAFT")
        if draft.get("human_review_required") is not True:
            errors.append(f"{prefix} requires human_review_required=true")

        evidence_refs = draft.get("evidence_refs")
        if not evidence_refs:
            errors.append(f"{prefix} missing evidence_refs")
        elif not isinstance(evidence_refs, list):
            errors.append(f"{prefix} evidence_refs must be a list")
        else:
            evidence_ref_count += len(evidence_refs)

    result = WorkOrderValidationResult(
        status="failed" if errors else "passed",
        errors=errors,
        counts=WorkOrderValidationCounts(
            validated_drafts=len(drafts),
            evidence_refs=evidence_ref_count,
        ),
        checked_files=checked_files or {},
    )
    if errors:
        raise WorkOrderValidationError(errors, result)
    return result


def _require_fields(payload: dict[str, Any], fields: list[str], prefix: str, errors: list[str]) -> None:
    for field in fields:
        if field not in payload or payload[field] in (None, "", []):
            errors.append(f"{prefix} missing {field}")

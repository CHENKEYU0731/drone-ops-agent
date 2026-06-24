from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import SkillRunAudit, write_model


def write_audit_record(
    out_dir: Path,
    skill_name: str,
    skill_version: str,
    input_refs: list[str],
    output_refs: list[str],
    tools_called: list[str],
    rules_triggered: list[str],
    human_review_required: bool,
    status: str,
    reviewer: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> SkillRunAudit:
    audit = SkillRunAudit(
        skill_name=skill_name,
        skill_version=skill_version,
        input_refs=input_refs,
        tools_called=tools_called,
        rules_triggered=rules_triggered,
        output_refs=output_refs,
        human_review_required=human_review_required,
        reviewer=reviewer,
        status=status,
        metadata=metadata or {},
    )
    audit_dir = out_dir / "audit"
    write_model(audit_dir / f"{skill_name}-{audit.run_id}.json", audit)
    return audit

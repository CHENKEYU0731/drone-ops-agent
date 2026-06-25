from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packages.drone_schemas import write_json
from packages.report_validation.models import (
    EvidenceIndex,
    EvidenceIndexEntry,
    ReportValidationCounts,
    ReportValidationPaths,
    ReportValidationResult,
)


REQUIRED_EVIDENCE_FIELDS = ["source_type", "source_id", "field", "rule_id", "description"]
HIGH_SEVERITIES = {"HIGH", "CRITICAL"}
GROUNDING_PRIORITIES = {"IMMEDIATE_GROUNDING", "BEFORE_NEXT_FLIGHT"}
REQUIRED_AUDIT_SKILLS = {
    "flight-log-analysis": {"flight-log-analysis", "analyze-log"},
    "fault-diagnosis": {"fault-diagnosis", "diagnose"},
    "maintenance-advisor": {"maintenance-advisor"},
    "ops-report-generation": {"ops-report-generation", "generate-report"},
}
REQUIRED_AUDIT_FIELDS = [
    "skill_name",
    "skill_version",
    "input_refs",
    "output_refs",
    "tools_called",
    "rules_triggered",
    "human_review_required",
    "status",
]
NON_EMPTY_AUDIT_FIELDS = [
    "skill_name",
    "skill_version",
    "input_refs",
    "output_refs",
    "tools_called",
    "human_review_required",
    "status",
]


class ReportValidationError(ValueError):
    def __init__(self, errors: list[str], result: ReportValidationResult):
        super().__init__("\n".join(errors))
        self.errors = errors
        self.result = result


def validate_report_outputs(paths: ReportValidationPaths, write_index: bool = False) -> ReportValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    index_entries: dict[str, EvidenceIndexEntry] = {}

    summary = _read_json(paths.summary, "flight_summary.json", errors)
    anomalies = _read_json_list(paths.anomalies, "anomalies.json", errors)
    diagnosis = _read_json_list(paths.diagnosis, "diagnosis.json", errors)
    maintenance = _read_json_list(paths.maintenance, "maintenance_recommendations.json", errors)
    _validate_report_markdown(paths.report, errors, warnings)
    audit_count = _validate_audits(paths.audit_dir, errors)

    if isinstance(summary, dict):
        _collect_evidence_refs(index_entries, summary.get("evidence_refs", []), f"summary:{summary.get('id', 'unknown')}", errors)

    _validate_anomalies(anomalies, errors, index_entries)
    _validate_diagnosis(diagnosis, errors, index_entries)
    _validate_maintenance(maintenance, errors, index_entries)

    result = ReportValidationResult(
        status="failed" if errors else "passed",
        errors=errors,
        warnings=warnings,
        counts=ReportValidationCounts(
            evidence_refs=len(index_entries),
            validated_anomalies=len(anomalies),
            validated_hypotheses=len(diagnosis),
            validated_recommendations=len(maintenance),
            validated_audit_files=audit_count,
        ),
        checked_files=paths.checked_files(),
        evidence_index=EvidenceIndex(entries=sorted(index_entries.values(), key=lambda item: item.key)),
    )

    if write_index:
        _write_validation_outputs(paths, result)
    if errors:
        raise ReportValidationError(errors, result)
    return result


def _read_json(path: Path, label: str, errors: list[str]) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{label} missing: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"{label} invalid JSON: {exc}")
    return None


def _read_json_list(path: Path, label: str, errors: list[str]) -> list[dict[str, Any]]:
    payload = _read_json(path, label, errors)
    if payload is None:
        return []
    if not isinstance(payload, list):
        errors.append(f"{label} must be a JSON list")
        return []
    items: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if isinstance(item, dict):
            items.append(item)
        else:
            errors.append(f"{label}[{index}] must be an object")
    return items


def _validate_anomalies(
    anomalies: list[dict[str, Any]],
    errors: list[str],
    index_entries: dict[str, EvidenceIndexEntry],
) -> None:
    for index, anomaly in enumerate(anomalies):
        prefix = f"anomalies[{index}]"
        _require_fields(anomaly, ["rule_id", "measured_value", "threshold", "human_review_required"], prefix, errors)
        if anomaly.get("human_review_required") is not True:
            errors.append(f"{prefix} requires human_review_required=true")
        evidence_refs = anomaly.get("evidence_refs")
        if not evidence_refs:
            errors.append(f"{prefix} missing evidence_refs")
            continue
        _collect_evidence_refs(index_entries, evidence_refs, f"anomaly:{anomaly.get('anomaly_id', anomaly.get('id', index))}", errors, prefix)


def _validate_diagnosis(
    hypotheses: list[dict[str, Any]],
    errors: list[str],
    index_entries: dict[str, EvidenceIndexEntry],
) -> None:
    for index, hypothesis in enumerate(hypotheses):
        prefix = f"diagnosis[{index}]"
        _require_fields(hypothesis, ["confidence", "severity", "recommended_next_steps", "human_review_required"], prefix, errors)
        evidence_refs = hypothesis.get("evidence_refs") or hypothesis.get("supporting_evidence")
        if not evidence_refs:
            errors.append(f"{prefix} missing evidence_refs")
        else:
            _collect_evidence_refs(
                index_entries,
                evidence_refs,
                f"fault_hypothesis:{hypothesis.get('fault_id', hypothesis.get('id', index))}",
                errors,
                prefix,
            )
        if str(hypothesis.get("severity", "")).upper() in HIGH_SEVERITIES and hypothesis.get("human_review_required") is not True:
            errors.append(f"{prefix} severity={hypothesis.get('severity')} requires human_review_required=true")


def _validate_maintenance(
    recommendations: list[dict[str, Any]],
    errors: list[str],
    index_entries: dict[str, EvidenceIndexEntry],
) -> None:
    required = ["component", "action", "priority", "reason", "required_approval", "human_review_required"]
    for index, recommendation in enumerate(recommendations):
        prefix = f"maintenance_recommendations[{index}]"
        _require_fields(recommendation, required, prefix, errors)
        evidence_refs = recommendation.get("evidence_refs")
        if not evidence_refs:
            errors.append(f"{prefix} missing evidence_refs")
        else:
            _collect_evidence_refs(
                index_entries,
                evidence_refs,
                f"maintenance_recommendation:{recommendation.get('recommendation_id', recommendation.get('id', index))}",
                errors,
                prefix,
            )
        priority = str(recommendation.get("priority", "")).upper()
        if priority in GROUNDING_PRIORITIES and recommendation.get("human_review_required") is not True:
            errors.append(f"{prefix} priority={priority} requires human_review_required=true")


def _collect_evidence_refs(
    index_entries: dict[str, EvidenceIndexEntry],
    evidence_refs: object,
    referenced_by: str,
    errors: list[str],
    owner_prefix: str = "evidence_refs",
) -> None:
    if not isinstance(evidence_refs, list):
        errors.append(f"{owner_prefix} evidence_refs must be a list")
        return
    for ref_index, ref in enumerate(evidence_refs):
        prefix = f"{owner_prefix}.evidence_refs[{ref_index}]"
        if not isinstance(ref, dict):
            errors.append(f"{prefix} must be an object")
            continue
        _require_fields(ref, REQUIRED_EVIDENCE_FIELDS, prefix, errors)
        if not all(ref.get(field) not in (None, "") for field in REQUIRED_EVIDENCE_FIELDS):
            continue
        key = _evidence_key(ref)
        if key not in index_entries:
            index_entries[key] = EvidenceIndexEntry(
                key=key,
                source_type=str(ref["source_type"]),
                source_id=str(ref["source_id"]),
                timestamp=str(ref["timestamp"]) if ref.get("timestamp") is not None else None,
                field=str(ref["field"]),
                measured_value=ref.get("measured_value", ""),
                threshold=ref.get("threshold", ""),
                rule_id=str(ref["rule_id"]),
                description=str(ref["description"]),
                referenced_by=[],
            )
        if referenced_by not in index_entries[key].referenced_by:
            index_entries[key].referenced_by.append(referenced_by)


def _evidence_key(ref: dict[str, Any]) -> str:
    return ":".join(
        [
            str(ref.get("source_type", "")),
            str(ref.get("source_id", "")),
            str(ref.get("timestamp", "")),
            str(ref.get("field", "")),
            str(ref.get("rule_id", "")),
        ]
    )


def _require_fields(payload: dict[str, Any], fields: list[str], prefix: str, errors: list[str]) -> None:
    for field in fields:
        if field not in payload or payload[field] in (None, "", []):
            errors.append(f"{prefix} missing {field}")


def _require_present_fields(payload: dict[str, Any], fields: list[str], prefix: str, errors: list[str]) -> None:
    for field in fields:
        if field not in payload:
            errors.append(f"{prefix} missing {field}")


def _validate_audits(audit_dir: Path, errors: list[str]) -> int:
    if not audit_dir.exists():
        errors.append(f"audit directory missing: {audit_dir}")
        return 0
    if not audit_dir.is_dir():
        errors.append(f"audit path is not a directory: {audit_dir}")
        return 0

    audit_payloads: list[dict[str, Any]] = []
    for audit_file in sorted(audit_dir.glob("*.json")):
        payload = _read_json(audit_file, audit_file.name, errors)
        if isinstance(payload, dict):
            audit_payloads.append(payload)
            _require_present_fields(payload, REQUIRED_AUDIT_FIELDS, audit_file.name, errors)
            _require_fields(payload, NON_EMPTY_AUDIT_FIELDS, audit_file.name, errors)
            if "created_at" not in payload and "timestamp" not in payload:
                errors.append(f"{audit_file.name} missing timestamp")

    skill_names = {str(payload.get("skill_name", "")) for payload in audit_payloads}
    for canonical_name, aliases in REQUIRED_AUDIT_SKILLS.items():
        if skill_names.isdisjoint(aliases):
            errors.append(f"audit missing required skill {canonical_name}")
    return len(audit_payloads)


def _validate_report_markdown(report_path: Path, errors: list[str], warnings: list[str]) -> None:
    try:
        report = report_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"ops_report.md missing: {report_path}")
        return

    for marker in ["## 1.", "## 5.", "## 6.", "## 7.", "## 10.", "## 11."]:
        if marker not in report:
            errors.append(f"ops_report.md missing section marker {marker}")
    if not any(token in report for token in ["evidence", "Evidence", "rule", "source", "证据", "规则", "来源"]):
        warnings.append("ops_report.md has no obvious evidence/rule/source reference tokens")


def _write_validation_outputs(paths: ReportValidationPaths, result: ReportValidationResult) -> None:
    output_dir = paths.output_dir()
    write_json(output_dir / "evidence_index.json", result.evidence_index.model_dump(mode="json"))
    write_json(output_dir / "report_validation.json", result.serializable_payload())

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class EvidenceIndexEntry(BaseModel):
    key: str
    source_type: str
    source_id: str
    timestamp: str | None = None
    field: str
    measured_value: float | int | str
    threshold: float | int | str
    rule_id: str
    description: str
    referenced_by: list[str] = Field(default_factory=list)


class EvidenceIndex(BaseModel):
    entries: list[EvidenceIndexEntry] = Field(default_factory=list)


class ReportValidationCounts(BaseModel):
    evidence_refs: int = 0
    validated_anomalies: int = 0
    validated_hypotheses: int = 0
    validated_recommendations: int = 0
    validated_audit_files: int = 0


class ReportValidationIssue(BaseModel):
    message: str
    severity: str = "error"


class ReportValidationPaths(BaseModel):
    summary: Path
    anomalies: Path
    diagnosis: Path
    maintenance: Path
    report: Path
    audit_dir: Path
    report_dir: Path | None = None

    @classmethod
    def from_report_dir(cls, report_dir: Path) -> "ReportValidationPaths":
        return cls(
            report_dir=report_dir,
            summary=report_dir / "flight_summary.json",
            anomalies=report_dir / "anomalies.json",
            diagnosis=report_dir / "diagnosis.json",
            maintenance=report_dir / "maintenance_recommendations.json",
            report=report_dir / "ops_report.md",
            audit_dir=report_dir / "audit",
        )

    def output_dir(self) -> Path:
        return self.report_dir or self.report.parent

    def checked_files(self) -> dict[str, str]:
        return {
            "summary": str(self.summary),
            "anomalies": str(self.anomalies),
            "diagnosis": str(self.diagnosis),
            "maintenance": str(self.maintenance),
            "report": str(self.report),
            "audit_dir": str(self.audit_dir),
        }


class ReportValidationResult(BaseModel):
    status: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    counts: ReportValidationCounts = Field(default_factory=ReportValidationCounts)
    checked_files: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evidence_index: EvidenceIndex = Field(default_factory=EvidenceIndex)

    def serializable_payload(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        payload.pop("evidence_index", None)
        return payload

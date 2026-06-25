from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.cli.main import _run_analyze_log, _run_diagnose, _run_generate_report
from packages.report_validation import (
    ReportValidationError,
    ReportValidationPaths,
    validate_report_outputs,
)


def _build_report_outputs(out_dir: Path) -> None:
    asset = Path("data/sample_assets/uav_001.json")
    _run_analyze_log(Path("data/sample_logs/example_flight.csv"), asset, out_dir)
    _run_diagnose(out_dir / "flight_summary.json", asset, out_dir)
    _run_generate_report(
        out_dir / "flight_summary.json",
        out_dir / "diagnosis.json",
        out_dir / "maintenance_recommendations.json",
        out_dir / "ops_report.md",
        asset,
        None,
    )


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_validate_report_outputs_passes_after_run_mvp_and_writes_index(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    _build_report_outputs(out_dir)

    result = validate_report_outputs(ReportValidationPaths.from_report_dir(out_dir), write_index=True)

    assert result.status == "passed"
    assert result.counts.evidence_refs > 0
    assert result.counts.validated_anomalies > 0
    assert result.counts.validated_hypotheses > 0
    assert result.counts.validated_recommendations > 0
    assert result.counts.validated_audit_files == 4
    assert (out_dir / "evidence_index.json").exists()
    assert (out_dir / "report_validation.json").exists()


def test_validate_report_outputs_fails_when_anomaly_lacks_evidence_refs(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    _build_report_outputs(out_dir)
    anomalies = _load_json(out_dir / "anomalies.json")
    assert isinstance(anomalies, list)
    anomalies[0]["evidence_refs"] = []
    _write_json(out_dir / "anomalies.json", anomalies)

    with pytest.raises(ReportValidationError) as exc_info:
        validate_report_outputs(ReportValidationPaths.from_report_dir(out_dir))

    assert "anomalies[0] missing evidence_refs" in str(exc_info.value)


def test_validate_report_outputs_fails_when_maintenance_lacks_evidence(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    _build_report_outputs(out_dir)
    maintenance = _load_json(out_dir / "maintenance_recommendations.json")
    assert isinstance(maintenance, list)
    maintenance[0]["evidence_refs"] = []
    _write_json(out_dir / "maintenance_recommendations.json", maintenance)

    with pytest.raises(ReportValidationError) as exc_info:
        validate_report_outputs(ReportValidationPaths.from_report_dir(out_dir))

    assert "maintenance_recommendations[0] missing evidence_refs" in str(exc_info.value)


def test_validate_report_outputs_fails_when_safety_review_is_relaxed(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    _build_report_outputs(out_dir)
    maintenance = _load_json(out_dir / "maintenance_recommendations.json")
    assert isinstance(maintenance, list)
    maintenance[0]["priority"] = "BEFORE_NEXT_FLIGHT"
    maintenance[0]["human_review_required"] = False
    _write_json(out_dir / "maintenance_recommendations.json", maintenance)

    with pytest.raises(ReportValidationError) as exc_info:
        validate_report_outputs(ReportValidationPaths.from_report_dir(out_dir))

    assert "maintenance_recommendations[0] priority=BEFORE_NEXT_FLIGHT requires human_review_required=true" in str(
        exc_info.value
    )


def test_validate_report_outputs_fails_when_high_diagnosis_review_is_relaxed(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    _build_report_outputs(out_dir)
    diagnosis = _load_json(out_dir / "diagnosis.json")
    assert isinstance(diagnosis, list)
    diagnosis[0]["severity"] = "HIGH"
    diagnosis[0]["human_review_required"] = False
    _write_json(out_dir / "diagnosis.json", diagnosis)

    with pytest.raises(ReportValidationError) as exc_info:
        validate_report_outputs(ReportValidationPaths.from_report_dir(out_dir))

    assert "diagnosis[0] severity=HIGH requires human_review_required=true" in str(exc_info.value)


def test_validate_report_outputs_fails_when_required_audit_is_missing(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    _build_report_outputs(out_dir)
    for audit_file in (out_dir / "audit").glob("ops-report-generation-*.json"):
        audit_file.unlink()

    with pytest.raises(ReportValidationError) as exc_info:
        validate_report_outputs(ReportValidationPaths.from_report_dir(out_dir))

    assert "audit missing required skill ops-report-generation" in str(exc_info.value)


def test_validate_report_outputs_fails_when_markdown_report_is_missing(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    _build_report_outputs(out_dir)
    (out_dir / "ops_report.md").unlink()

    with pytest.raises(ReportValidationError) as exc_info:
        validate_report_outputs(ReportValidationPaths.from_report_dir(out_dir))

    assert "ops_report.md missing" in str(exc_info.value)

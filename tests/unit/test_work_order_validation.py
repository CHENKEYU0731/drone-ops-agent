from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.cli.main import _run_analyze_log, _run_diagnose, _run_generate_work_orders
from packages.work_orders import WorkOrderValidationError, validate_work_order_drafts


def _build_work_order_drafts(out_dir: Path) -> list[dict[str, object]]:
    asset = Path("data/sample_assets/uav_001.json")
    _run_analyze_log(Path("data/sample_logs/example_flight.csv"), asset, out_dir)
    _run_diagnose(out_dir / "flight_summary.json", asset, out_dir)
    _run_generate_work_orders(out_dir / "maintenance_recommendations.json", asset, out_dir)
    payload = json.loads((out_dir / "work_order_drafts.json").read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    return payload


def test_validate_work_order_drafts_passes_for_generated_drafts(tmp_path: Path) -> None:
    drafts = _build_work_order_drafts(tmp_path / "reports")

    result = validate_work_order_drafts(drafts, checked_files={"drafts": "work_order_drafts.json"})

    assert result.status == "passed"
    assert result.counts.validated_drafts == len(drafts)
    assert result.checked_files == {"drafts": "work_order_drafts.json"}
    assert result.created_at.isoformat() == "1970-01-01T00:00:00+00:00"


def test_validate_work_order_drafts_fails_when_evidence_refs_are_missing(tmp_path: Path) -> None:
    drafts = _build_work_order_drafts(tmp_path / "reports")
    drafts[0]["evidence_refs"] = []

    with pytest.raises(WorkOrderValidationError) as exc_info:
        validate_work_order_drafts(drafts)

    assert "work_order_drafts[0] missing evidence_refs" in str(exc_info.value)


def test_validate_work_order_drafts_fails_when_status_is_not_draft(tmp_path: Path) -> None:
    drafts = _build_work_order_drafts(tmp_path / "reports")
    drafts[0]["status"] = "READY"

    with pytest.raises(WorkOrderValidationError) as exc_info:
        validate_work_order_drafts(drafts)

    assert "work_order_drafts[0] status must be DRAFT" in str(exc_info.value)


def test_validate_work_order_drafts_fails_when_human_review_is_relaxed(tmp_path: Path) -> None:
    drafts = _build_work_order_drafts(tmp_path / "reports")
    drafts[0]["human_review_required"] = False

    with pytest.raises(WorkOrderValidationError) as exc_info:
        validate_work_order_drafts(drafts)

    assert "work_order_drafts[0] requires human_review_required=true" in str(exc_info.value)


def test_validate_work_order_drafts_fails_when_source_recommendation_is_missing(tmp_path: Path) -> None:
    drafts = _build_work_order_drafts(tmp_path / "reports")
    drafts[0]["source_recommendation_id"] = ""

    with pytest.raises(WorkOrderValidationError) as exc_info:
        validate_work_order_drafts(drafts)

    assert "work_order_drafts[0] missing source_recommendation_id" in str(exc_info.value)

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def test_validate_work_orders_cli_writes_validation_and_audit(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    result = runner.invoke(
        app,
        [
            "run-mvp",
            "--log",
            "data/sample_logs/example_flight.csv",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(report_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(
        app,
        [
            "generate-work-orders",
            "--maintenance",
            str(report_dir / "maintenance_recommendations.json"),
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(report_dir),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "validate-work-orders",
            "--drafts",
            str(report_dir / "work_order_drafts.json"),
            "--out",
            str(report_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    validation_path = report_dir / "work_order_validation.json"
    assert validation_path.exists()
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    assert validation["status"] == "passed"
    assert validation["created_at"] == "1970-01-01T00:00:00Z"
    assert validation["counts"]["validated_drafts"] > 0
    audit_files = list((report_dir / "audit").glob("work-order-validation-*.json"))
    assert audit_files
    audit = json.loads(audit_files[0].read_text(encoding="utf-8"))
    assert audit["skill_name"] == "work-order-validation"
    assert audit["output_refs"] == [str(validation_path)]
    assert audit["human_review_required"] is True
    assert audit["metadata"]["safety_boundary"] == "offline-validation-only"


def test_validate_work_orders_cli_reports_invalid_drafts(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    drafts_path = report_dir / "work_order_drafts.json"
    drafts_path.write_text(
        json.dumps(
            [
                {
                    "work_order_id": "WO-UAV-001-001",
                    "asset_id": "UAV-001",
                    "component": "battery",
                    "priority": "BEFORE_NEXT_FLIGHT",
                    "action": "Replace battery.",
                    "reason": "Battery risk.",
                    "evidence_refs": [],
                    "required_approval": "maintenance_lead",
                    "estimated_effort": "30 minutes",
                    "status": "DRAFT",
                    "source_recommendation_id": "MAINT-001",
                    "human_review_required": True,
                }
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "validate-work-orders",
            "--drafts",
            str(drafts_path),
            "--out",
            str(report_dir),
        ],
    )

    assert result.exit_code == 1
    assert "work_order_drafts[0] missing evidence_refs" in result.output
    assert "Traceback" not in result.output

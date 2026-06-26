import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def test_generate_work_orders_cli_writes_json_markdown_and_audit(tmp_path: Path) -> None:
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
    drafts_path = report_dir / "work_order_drafts.json"
    markdown_path = report_dir / "work_order_drafts.md"
    assert drafts_path.exists()
    assert markdown_path.exists()
    drafts = json.loads(drafts_path.read_text(encoding="utf-8"))
    assert drafts
    assert all(item["status"] == "DRAFT" for item in drafts)
    assert all(item["human_review_required"] is True for item in drafts)
    assert all(item["evidence_refs"] for item in drafts)
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# 工单草稿" in markdown
    assert "不会自动派单" in markdown

    audit_files = list((report_dir / "audit").glob("work-order-drafting-*.json"))
    assert audit_files
    audit = json.loads(audit_files[0].read_text(encoding="utf-8"))
    assert audit["skill_name"] == "work-order-drafting"
    assert audit["output_refs"] == [str(drafts_path), str(markdown_path)]
    assert audit["human_review_required"] is True
    assert audit["status"] == "success"


def test_generate_work_orders_cli_missing_file_error_is_clear(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "generate-work-orders",
            "--maintenance",
            "missing.json",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "missing.json" in result.output
    assert "Traceback" not in result.output

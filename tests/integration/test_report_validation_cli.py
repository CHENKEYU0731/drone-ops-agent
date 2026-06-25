from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def _run_mvp(out_dir: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run-mvp",
            "--log",
            "data/sample_logs/example_flight.csv",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output


def test_validate_report_cli_passes_with_report_dir_and_write_index(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    _run_mvp(out_dir)

    result = runner.invoke(app, ["validate-report", "--report-dir", str(out_dir), "--write-index"])

    assert result.exit_code == 0, result.output
    assert "Report validation passed" in result.output
    assert "evidence refs:" in result.output
    assert (out_dir / "evidence_index.json").exists()
    assert (out_dir / "report_validation.json").exists()


def test_validate_report_cli_accepts_explicit_paths(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    _run_mvp(out_dir)

    result = runner.invoke(
        app,
        [
            "validate-report",
            "--summary",
            str(out_dir / "flight_summary.json"),
            "--anomalies",
            str(out_dir / "anomalies.json"),
            "--diagnosis",
            str(out_dir / "diagnosis.json"),
            "--maintenance",
            str(out_dir / "maintenance_recommendations.json"),
            "--report",
            str(out_dir / "ops_report.md"),
            "--audit-dir",
            str(out_dir / "audit"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Report validation passed" in result.output


def test_validate_report_cli_reports_clear_errors_without_traceback(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    _run_mvp(out_dir)
    anomalies_path = out_dir / "anomalies.json"
    anomalies = json.loads(anomalies_path.read_text(encoding="utf-8"))
    anomalies[0]["evidence_refs"] = []
    anomalies_path.write_text(json.dumps(anomalies, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = runner.invoke(app, ["validate-report", "--report-dir", str(out_dir)])

    assert result.exit_code == 1
    assert "Error: report validation failed" in result.output
    assert "- anomalies[0] missing evidence_refs" in result.output
    assert "Traceback" not in result.output

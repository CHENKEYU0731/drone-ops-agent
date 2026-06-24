from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def test_cli_commands_generate_expected_artifacts(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    result = runner.invoke(
        app,
        [
            "analyze-log",
            "--log",
            "data/sample_logs/example_flight.csv",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out_dir / "flight_summary.json").exists()
    assert (out_dir / "anomalies.json").exists()

    result = runner.invoke(
        app,
        [
            "diagnose",
            "--summary",
            str(out_dir / "flight_summary.json"),
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out_dir / "diagnosis.json").exists()
    assert (out_dir / "maintenance_recommendations.json").exists()

    result = runner.invoke(
        app,
        [
            "generate-report",
            "--summary",
            str(out_dir / "flight_summary.json"),
            "--diagnosis",
            str(out_dir / "diagnosis.json"),
            "--maintenance",
            str(out_dir / "maintenance_recommendations.json"),
            "--out",
            str(out_dir / "ops_report.md"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out_dir / "ops_report.md").exists()


def test_cli_reports_clear_missing_file_errors(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "analyze-log",
            "--log",
            "missing.csv",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "飞行日志不存在: missing.csv" in result.output
    assert "Traceback" not in result.output

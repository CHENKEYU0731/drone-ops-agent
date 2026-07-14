import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def test_nominal_log_audit_still_requires_human_review(tmp_path: Path) -> None:
    log_path = tmp_path / "nominal.csv"
    log_path.write_text(
        "timestamp,flight_mode,altitude_m,battery_voltage_v,battery_current_a,battery_soc_pct,"
        "gps_satellites,gps_hdop,vibration_x,vibration_y,vibration_z,motor_1_output,"
        "motor_2_output,motor_3_output,motor_4_output,link_quality_pct,temperature_c\n"
        "2026-06-24T10:00:00Z,STABILIZE,0,16.8,4,96,14,0.8,0.1,0.1,0.2,20,21,20,20,99,28\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "reports"

    result = runner.invoke(
        app,
        [
            "analyze-log",
            "--log",
            str(log_path),
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert json.loads((out_dir / "anomalies.json").read_text(encoding="utf-8")) == []
    audit_file = next((out_dir / "audit").glob("flight-log-analysis-*.json"))
    audit = json.loads(audit_file.read_text(encoding="utf-8"))
    assert audit["human_review_required"] is True


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
    report = (out_dir / "ops_report.md").read_text(encoding="utf-8")
    assert "## 7.6 审计摘要" in report
    assert "## 7.7 日志解析元数据" in report
    assert "解析器：`csv-json-flight-log@1.1.0`" in report
    assert "## 7.8 人工复核清单" in report


def test_generate_report_cli_accepts_simulation_run(tmp_path: Path) -> None:
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

    simulation_dir = tmp_path / "simulation"
    result = runner.invoke(
        app,
        [
            "validate-simulation",
            "--scenario",
            "data/sample_simulation/example_scenario.json",
            "--result",
            "data/sample_simulation/example_simulation_result.json",
            "--out",
            str(simulation_dir),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "generate-report",
            "--summary",
            str(out_dir / "flight_summary.json"),
            "--anomalies",
            str(out_dir / "anomalies.json"),
            "--diagnosis",
            str(out_dir / "diagnosis.json"),
            "--maintenance",
            str(out_dir / "maintenance_recommendations.json"),
            "--simulation",
            str(simulation_dir / "simulation_run.json"),
            "--out",
            str(out_dir / "ops_report.md"),
        ],
    )

    assert result.exit_code == 0, result.output
    report = (out_dir / "ops_report.md").read_text(encoding="utf-8")
    assert "## 7.5 仿真验证" in report
    assert "仿真状态：`PASS`" in report
    assert "SIM_RESULT_COMPLETED" in report


def test_generate_report_cli_accepts_work_order_outputs(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
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
    result = runner.invoke(
        app,
        [
            "generate-work-orders",
            "--maintenance",
            str(out_dir / "maintenance_recommendations.json"),
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(
        app,
        [
            "validate-work-orders",
            "--drafts",
            str(out_dir / "work_order_drafts.json"),
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "generate-report",
            "--summary",
            str(out_dir / "flight_summary.json"),
            "--anomalies",
            str(out_dir / "anomalies.json"),
            "--diagnosis",
            str(out_dir / "diagnosis.json"),
            "--maintenance",
            str(out_dir / "maintenance_recommendations.json"),
            "--work-orders",
            str(out_dir / "work_order_drafts.json"),
            "--work-order-validation",
            str(out_dir / "work_order_validation.json"),
            "--out",
            str(out_dir / "ops_report.md"),
        ],
    )

    assert result.exit_code == 0, result.output
    report = (out_dir / "ops_report.md").read_text(encoding="utf-8")
    assert "## 7.9 工单草稿" in report
    assert "## 7.10 工单验证" in report
    assert "验证状态：`passed`" in report
    assert "不会自动派单" in report


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

from pathlib import Path

from pypdf import PdfReader
from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def test_export_pdf_cli_writes_pdf(tmp_path: Path) -> None:
    markdown = tmp_path / "ops_report.md"
    pdf = tmp_path / "ops_report.pdf"
    markdown.write_text("# 无人机运维报告\n\n## 执行摘要\n\n- 离线报告。\n", encoding="utf-8")

    result = runner.invoke(app, ["export-pdf", "--markdown", str(markdown), "--out", str(pdf)])

    assert result.exit_code == 0, result.output
    assert pdf.exists()
    assert pdf.read_bytes().startswith(b"%PDF")


def test_export_pdf_cli_missing_file_error_is_clear(tmp_path: Path) -> None:
    result = runner.invoke(app, ["export-pdf", "--markdown", "missing.md", "--out", str(tmp_path / "out.pdf")])

    assert result.exit_code == 1
    assert "missing.md" in result.output
    assert "Traceback" not in result.output


def test_generate_report_pdf_option_writes_markdown_and_pdf(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    analyze = runner.invoke(
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
    assert analyze.exit_code == 0, analyze.output
    diagnose = runner.invoke(
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
    assert diagnose.exit_code == 0, diagnose.output

    pdf = out_dir / "ops_report.pdf"
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
            "--out",
            str(out_dir / "ops_report.md"),
            "--pdf",
            str(pdf),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (out_dir / "ops_report.md").exists()
    assert pdf.exists()
    assert pdf.read_bytes().startswith(b"%PDF")


def test_generate_report_pdf_includes_v08_report_sections(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    simulation_dir = tmp_path / "simulation"
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

    pdf = out_dir / "ops_report_with_v08_sections.pdf"
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
            str(out_dir / "ops_report_with_v08_sections.md"),
            "--pdf",
            str(pdf),
        ],
    )

    assert result.exit_code == 0, result.output
    assert pdf.exists()
    text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf)).pages)
    assert "7.5 仿真验证" in text
    assert "7.6 审计摘要" in text
    assert "7.7 日志解析元数据" in text
    assert "7.8 人工复核清单" in text
    assert "SIM_RESULT_COMPLETED" in text
    assert "csv-json-flight-log@1.1.0" in text

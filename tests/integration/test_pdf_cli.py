from pathlib import Path

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

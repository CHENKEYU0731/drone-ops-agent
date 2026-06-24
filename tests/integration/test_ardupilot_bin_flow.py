import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def test_analyze_log_accepts_ardupilot_bin_format(tmp_path: Path) -> None:
    out_dir = tmp_path / "bin-out"

    result = runner.invoke(
        app,
        [
            "analyze-log",
            "--log",
            "data/sample_logs/example_ardupilot.bin",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
            "--format",
            "ardupilot-bin",
        ],
    )

    assert result.exit_code == 0, result.output
    summary = json.loads((out_dir / "flight_summary.json").read_text(encoding="utf-8"))
    anomalies = json.loads((out_dir / "anomalies.json").read_text(encoding="utf-8"))
    audits = list((out_dir / "audit").glob("flight-log-analysis-*.json"))

    assert summary["source_log_id"] == "example_ardupilot.bin"
    assert summary["record_count"] == 3
    assert summary["evidence_refs"]
    assert all(item["evidence_refs"] for item in anomalies)
    assert len(audits) == 1

    audit = json.loads(audits[0].read_text(encoding="utf-8"))
    assert "parse_flight_log_with_metadata:ardupilot-bin@0.1.0" in audit["tools_called"]
    assert "format=ardupilot-bin" in audit["input_refs"]
    assert audit["human_review_required"] is True


def test_analyze_log_auto_accepts_bin_extension(tmp_path: Path) -> None:
    out_dir = tmp_path / "auto-bin-out"

    result = runner.invoke(
        app,
        [
            "analyze-log",
            "--log",
            "data/sample_logs/example_ardupilot.bin",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
            "--format",
            "auto",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (out_dir / "flight_summary.json").exists()


def test_analyze_log_dependency_error_has_no_traceback(tmp_path: Path) -> None:
    real_bin = tmp_path / "real-flight.bin"
    real_bin.write_bytes(b"\xa3\x95not-a-mock-dataflash-log")

    result = runner.invoke(
        app,
        [
            "analyze-log",
            "--log",
            str(real_bin),
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(tmp_path / "out"),
            "--format",
            "ardupilot-bin",
        ],
    )

    assert result.exit_code == 1
    assert "pip install -e .[ardupilot]" in result.output
    assert "Traceback" not in result.output


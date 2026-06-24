from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_analyze_log_px4_ulog_mock_writes_outputs_with_evidence_and_audit(tmp_path: Path) -> None:
    out_dir = tmp_path / "px4"
    result = runner.invoke(
        app,
        [
            "analyze-log",
            "--log",
            "data/sample_logs/example_px4_mock.ulg",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
            "--format",
            "px4-ulog",
        ],
    )

    assert result.exit_code == 0, result.output
    summary = read_json_file(out_dir / "flight_summary.json")
    anomalies = read_json_file(out_dir / "anomalies.json")
    audit_files = list((out_dir / "audit").glob("flight-log-analysis-*.json"))
    audit = read_json_file(audit_files[0])

    assert summary["source_log_id"] == "example_px4_mock.ulg"
    assert summary["evidence_refs"]
    assert "px4-ulog" in summary["evidence_refs"][0]["description"]
    assert anomalies
    assert all(event["evidence_refs"] for event in anomalies)
    assert audit["metadata"]["requested_format"] == "px4-ulog"
    assert audit["metadata"]["actual_format"] == "px4-ulog"
    assert audit["metadata"]["parser_name"] == "px4-ulog"
    assert audit["human_review_required"] is True


def test_analyze_log_auto_detects_px4_ulog_by_extension(tmp_path: Path) -> None:
    out_dir = tmp_path / "auto"
    result = runner.invoke(
        app,
        [
            "analyze-log",
            "--log",
            "data/sample_logs/example_px4_mock.ulg",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
            "--format",
            "auto",
        ],
    )

    assert result.exit_code == 0, result.output
    audit_file = next((out_dir / "audit").glob("flight-log-analysis-*.json"))
    audit = read_json_file(audit_file)
    assert audit["metadata"]["requested_format"] == "auto"
    assert audit["metadata"]["actual_format"] == "px4-ulog"


def test_analyze_log_px4_missing_dependency_error_has_no_traceback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = tmp_path / "realish.ulg"
    path.write_bytes(b"ULog\x01\x12not-json")
    monkeypatch.setattr("packages.log_parsers.px4_ulog.find_spec", lambda name: None)

    result = runner.invoke(
        app,
        [
            "analyze-log",
            "--log",
            str(path),
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(tmp_path / "out"),
            "--format",
            "px4-ulog",
        ],
    )

    assert result.exit_code == 1
    assert "pip install -e .[px4]" in result.output
    assert "pyulog" in result.output
    assert "Traceback" not in result.output


def test_analyze_log_csv_and_json_still_work_with_auto_format(tmp_path: Path) -> None:
    for extension in ("csv", "json"):
        out_dir = tmp_path / extension
        result = runner.invoke(
            app,
            [
                "analyze-log",
                "--log",
                f"data/sample_logs/example_flight.{extension}",
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
        assert (out_dir / "anomalies.json").exists()

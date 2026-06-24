import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def test_monitor_replay_cli_writes_outputs_and_audit(tmp_path: Path) -> None:
    out_dir = tmp_path / "monitoring"
    result = runner.invoke(
        app,
        [
            "monitor-replay",
            "--telemetry",
            "data/sample_logs/example_telemetry.csv",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--rules",
            "data/sample_rules/monitoring_rules.yaml",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    summary_path = out_dir / "monitoring_summary.json"
    events_path = out_dir / "monitoring_events.json"
    assert summary_path.exists()
    assert events_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    events = json.loads(events_path.read_text(encoding="utf-8"))
    assert summary["event_count"] == len(events)
    assert summary["human_review_required"] is True
    assert all(event["evidence_refs"] for event in events)

    audit_files = list((out_dir / "audit").glob("state-monitoring-*.json"))
    assert audit_files
    audit = json.loads(audit_files[0].read_text(encoding="utf-8"))
    assert audit["skill_name"] == "state-monitoring"
    assert audit["output_refs"] == [str(summary_path), str(events_path)]
    assert audit["status"] == "success"


def test_monitor_replay_cli_missing_file_error_is_clear(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "monitor-replay",
            "--telemetry",
            "missing_telemetry.csv",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--rules",
            "data/sample_rules/monitoring_rules.yaml",
            "--out",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "missing_telemetry.csv" in result.output
    assert "Traceback" not in result.output

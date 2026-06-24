from pathlib import Path

from packages.log_parsers import parse_flight_log
from packages.telemetry_rules import summarize_flight


def test_parse_csv_and_json_logs() -> None:
    csv_records = parse_flight_log(Path("data/sample_logs/example_flight.csv"))
    json_records = parse_flight_log(Path("data/sample_logs/example_flight.json"))

    assert len(csv_records) == len(json_records)
    assert csv_records[0].flight_mode == "STABILIZE"
    assert csv_records[-1].battery_soc_pct == 14


def test_summary_calculates_operational_metrics() -> None:
    records = parse_flight_log(Path("data/sample_logs/example_flight.csv"))
    summary = summarize_flight(records, drone_id="UAV-001", source_log_id="example_flight.csv")

    assert summary.duration_seconds == 360
    assert summary.min_battery_voltage_v == 13.4
    assert summary.max_battery_current_a == 42.0
    assert summary.min_battery_soc_pct == 14
    assert summary.gps_summary["min_satellites"] == 5
    assert summary.vibration_summary["max_magnitude"] > 3.0
    assert summary.motor_imbalance_summary["max_spread"] == 38
    assert summary.link_quality_summary["min_link_quality_pct"] == 48
    assert "FAILSAFE" in {item["flight_mode"] for item in summary.flight_mode_timeline}
    assert summary.flight_mode_timeline[-1]["flight_mode"] == "LAND"

import json
from pathlib import Path

from packages.drone_schemas import DroneAsset, Severity
from packages.state_monitoring import parse_telemetry_replay, run_monitoring_replay


RULES = Path("data/sample_rules/monitoring_rules.yaml")


def _asset() -> DroneAsset:
    return DroneAsset(
        drone_id="UAV-001",
        model="Quad-X4",
        serial_number="SN-UAV-001",
        firmware_version="simulated-1.0",
        total_flight_hours=42.5,
        battery_ids=["BAT-001"],
        maintenance_history=["2026-06-12: routine inspection closed"],
        operational_status="active",
    )


def _normal_row(**overrides) -> dict:
    row = {
        "timestamp": "2026-06-24T10:00:00Z",
        "flight_mode": "AUTO",
        "altitude_m": 30,
        "vertical_speed_mps": 0.2,
        "ground_speed_mps": 7.5,
        "battery_voltage_v": 15.8,
        "battery_current_a": 18,
        "battery_soc_pct": 82,
        "gps_satellites": 16,
        "gps_hdop": 0.8,
        "vibration_x": 0.15,
        "vibration_y": 0.16,
        "vibration_z": 0.18,
        "motor_1_output": 48,
        "motor_2_output": 49,
        "motor_3_output": 47,
        "motor_4_output": 48,
        "link_quality_pct": 96,
        "temperature_c": 34,
        "ekf_variance": 0.18,
        "failsafe_active": False,
    }
    row.update(overrides)
    return row


def test_parse_telemetry_replay_supports_csv_and_json(tmp_path: Path) -> None:
    csv_path = tmp_path / "telemetry.csv"
    json_path = tmp_path / "telemetry.json"
    row = _normal_row()
    csv_path.write_text(",".join(row.keys()) + "\n" + ",".join(str(value) for value in row.values()) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps([row]), encoding="utf-8")

    csv_records = parse_telemetry_replay(csv_path, drone_id="UAV-001")
    json_records = parse_telemetry_replay(json_path, drone_id="UAV-001")

    assert csv_records[0].drone_id == "UAV-001"
    assert json_records[0].flight_mode == "AUTO"
    assert csv_records[0].failsafe_active is False


def test_normal_state_produces_summary_without_events(tmp_path: Path) -> None:
    telemetry_path = tmp_path / "normal.json"
    telemetry_path.write_text(json.dumps([_normal_row(), _normal_row(timestamp="2026-06-24T10:00:10Z")]), encoding="utf-8")

    summary, events = run_monitoring_replay(telemetry_path, _asset(), RULES)

    assert events == []
    assert summary.event_count == 0
    assert summary.highest_severity == Severity.INFO
    assert summary.human_review_required is False
    assert summary.samples_processed == 2


def test_monitoring_rules_trigger_events_with_evidence() -> None:
    summary, events = run_monitoring_replay(Path("data/sample_logs/example_telemetry.csv"), _asset(), RULES)

    event_types = {event.event_type for event in events}
    assert {
        "LOW_BATTERY_SOC",
        "BATTERY_VOLTAGE_SAG",
        "HIGH_CURRENT_DRAW",
        "GPS_DEGRADATION",
        "HIGH_HDOP",
        "LOW_SATELLITE_COUNT",
        "HIGH_VIBRATION",
        "MOTOR_OUTPUT_IMBALANCE",
        "COMMUNICATION_LINK_DROP",
        "HIGH_TEMPERATURE",
        "EKF_VARIANCE_HIGH",
        "FAILSAFE_ACTIVE",
        "UNEXPECTED_MODE_TRANSITION",
    } <= event_types
    assert all(event.evidence_refs for event in events)
    assert all(event.human_review_required for event in events if event.severity in {Severity.HIGH, Severity.CRITICAL})
    assert summary.human_review_required is True
    assert summary.event_count == len(events)
    assert summary.source_refs == ["data/sample_logs/example_telemetry.csv", "data/sample_rules/monitoring_rules.yaml"]


def test_json_sample_matches_csv_monitoring_coverage() -> None:
    _, csv_events = run_monitoring_replay(Path("data/sample_logs/example_telemetry.csv"), _asset(), RULES)
    _, json_events = run_monitoring_replay(Path("data/sample_logs/example_telemetry.json"), _asset(), RULES)

    assert {event.event_type for event in json_events} == {event.event_type for event in csv_events}

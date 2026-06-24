from pathlib import Path

from packages.anomaly_detection import detect_anomalies
from packages.log_parsers import parse_flight_log


def test_detects_required_anomaly_types_with_evidence() -> None:
    records = parse_flight_log(Path("data/sample_logs/example_flight.csv"))
    anomalies = detect_anomalies(records, drone_id="UAV-001", source_log_id="example_flight.csv")
    anomaly_types = {event.type for event in anomalies}

    assert {
        "BATTERY_VOLTAGE_DROP",
        "LOW_BATTERY_SOC",
        "HIGH_CURRENT",
        "GPS_QUALITY_DEGRADED",
        "HIGH_HDOP",
        "LOW_GPS_SATELLITES",
        "HIGH_VIBRATION",
        "MOTOR_OUTPUT_IMBALANCE",
        "LOW_LINK_QUALITY",
        "HIGH_TEMPERATURE",
        "UNEXPECTED_FLIGHT_MODE",
    }.issubset(anomaly_types)
    assert all(event.evidence_refs for event in anomalies)
    assert all(event.human_review_required for event in anomalies)
    assert anomalies == sorted(anomalies, key=lambda item: (item.timestamp, item.anomaly_id))

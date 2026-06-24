from pathlib import Path

from packages.anomaly_detection import detect_anomalies
from packages.diagnosis_rules import generate_fault_hypotheses
from packages.drone_schemas import load_model
from packages.log_parsers import parse_flight_log
from packages.maintenance_rules import generate_maintenance_recommendations
from packages.telemetry_rules import summarize_flight
from packages.drone_schemas import DroneAsset


def test_diagnosis_ranks_multiple_fault_hypotheses() -> None:
    asset = load_model(Path("data/sample_assets/uav_001.json"), DroneAsset)
    records = parse_flight_log(Path("data/sample_logs/example_flight.csv"))
    summary = summarize_flight(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    anomalies = detect_anomalies(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")

    hypotheses = generate_fault_hypotheses(summary, anomalies, asset)

    assert len(hypotheses) >= 5
    assert hypotheses == sorted(hypotheses, key=lambda item: item.confidence, reverse=True)
    assert all(hypothesis.supporting_evidence for hypothesis in hypotheses)
    assert all(hypothesis.evidence_refs for hypothesis in hypotheses)
    assert all(hypothesis.human_review_required for hypothesis in hypotheses)


def test_maintenance_recommendations_include_review_and_evidence() -> None:
    asset = load_model(Path("data/sample_assets/uav_001.json"), DroneAsset)
    records = parse_flight_log(Path("data/sample_logs/example_flight.csv"))
    summary = summarize_flight(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    anomalies = detect_anomalies(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    hypotheses = generate_fault_hypotheses(summary, anomalies, asset)

    recommendations = generate_maintenance_recommendations(hypotheses, asset, summary)
    priorities = {item.priority.value for item in recommendations}

    assert "IMMEDIATE_GROUNDING" in priorities
    assert "BEFORE_NEXT_FLIGHT" in priorities
    assert "POST_FLIGHT_INSPECTION" in priorities
    assert all(item.evidence_refs for item in recommendations)
    assert all(item.required_approval for item in recommendations)

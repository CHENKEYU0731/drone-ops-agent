from pathlib import Path

from packages.drone_schemas import DroneAsset, load_model
from packages.anomaly_detection import detect_anomalies
from packages.diagnosis_rules import generate_fault_hypotheses
from packages.log_parsers import parse_flight_log
from packages.maintenance_rules import generate_maintenance_recommendations
from packages.telemetry_rules import summarize_flight
from packages.work_orders import generate_work_order_drafts, render_work_order_drafts_markdown


def test_generate_work_order_drafts_from_maintenance_recommendations() -> None:
    asset = load_model(Path("data/sample_assets/uav_001.json"), DroneAsset)
    records = parse_flight_log(Path("data/sample_logs/example_flight.csv"))
    summary = summarize_flight(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    anomalies = detect_anomalies(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    diagnosis = generate_fault_hypotheses(summary, anomalies, asset)
    recommendations = generate_maintenance_recommendations(diagnosis, asset, summary)

    drafts = generate_work_order_drafts(recommendations, asset)

    assert drafts
    assert all(draft.asset_id == asset.drone_id for draft in drafts)
    assert all(draft.status == "DRAFT" for draft in drafts)
    assert all(draft.required_approval for draft in drafts)
    assert all(draft.human_review_required for draft in drafts)
    assert all(draft.evidence_refs for draft in drafts)
    assert drafts[0].source_recommendation_id == recommendations[0].recommendation_id


def test_render_work_order_drafts_markdown_is_advisory_only() -> None:
    asset = load_model(Path("data/sample_assets/uav_001.json"), DroneAsset)
    records = parse_flight_log(Path("data/sample_logs/example_flight.csv"))
    summary = summarize_flight(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    anomalies = detect_anomalies(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    diagnosis = generate_fault_hypotheses(summary, anomalies, asset)
    recommendations = generate_maintenance_recommendations(diagnosis, asset, summary)
    drafts = generate_work_order_drafts(recommendations, asset)

    markdown = render_work_order_drafts_markdown(drafts)

    assert "# 工单草稿" in markdown
    assert "仅供人工复核" in markdown
    assert "不会自动派单" in markdown
    assert "DRAFT" in markdown
    assert recommendations[0].recommendation_id in markdown

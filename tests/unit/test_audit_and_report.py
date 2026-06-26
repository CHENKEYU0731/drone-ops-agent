from pathlib import Path

from packages.audit_logger import write_audit_record
from packages.drone_schemas import DroneAsset, SimulationRun, load_model
from packages.anomaly_detection import detect_anomalies
from packages.diagnosis_rules import generate_fault_hypotheses
from packages.log_parsers import parse_flight_log
from packages.maintenance_rules import generate_maintenance_recommendations
from packages.report_templates import render_ops_report
from packages.telemetry_rules import summarize_flight


def test_audit_record_is_written(tmp_path: Path) -> None:
    audit = write_audit_record(
        out_dir=tmp_path,
        skill_name="flight-log-analysis",
        skill_version="1.0.0",
        input_refs=["input.csv"],
        output_refs=["summary.json"],
        tools_called=["parse_flight_log"],
        rules_triggered=["LOW_BATTERY_SOC"],
        human_review_required=True,
        status="success",
    )

    audit_file = tmp_path / "audit" / f"{audit.skill_name}-{audit.run_id}.json"
    assert audit_file.exists()
    assert "LOW_BATTERY_SOC" in audit_file.read_text(encoding="utf-8")


def test_report_contains_required_sections() -> None:
    asset = load_model(Path("data/sample_assets/uav_001.json"), DroneAsset)
    records = parse_flight_log(Path("data/sample_logs/example_flight.csv"))
    summary = summarize_flight(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    anomalies = detect_anomalies(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    diagnosis = generate_fault_hypotheses(summary, anomalies, asset)
    maintenance = generate_maintenance_recommendations(diagnosis, asset, summary)
    report = render_ops_report(
        summary=summary,
        anomalies=anomalies,
        diagnosis=diagnosis,
        maintenance=maintenance,
        asset=asset,
        audits=[],
    )

    for heading in [
        "## 1. 执行摘要",
        "## 2. 飞行概况",
        "## 3. 资产概况",
        "## 4. 关键指标",
        "## 5. 异常事件时间线",
        "## 6. 故障假设",
        "## 7. 维护建议",
        "## 8. 安全说明",
        "## 9. 人工复核要求",
        "## 10. 审计记录",
        "## 11. 证据引用附录",
    ]:
        assert heading in report
    assert "证据：" in report
    assert "LOW_BATTERY_SOC" in report


def test_report_can_include_simulation_validation_section() -> None:
    asset = load_model(Path("data/sample_assets/uav_001.json"), DroneAsset)
    records = parse_flight_log(Path("data/sample_logs/example_flight.csv"))
    summary = summarize_flight(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    anomalies = detect_anomalies(records, drone_id=asset.drone_id, source_log_id="example_flight.csv")
    diagnosis = generate_fault_hypotheses(summary, anomalies, asset)
    maintenance = generate_maintenance_recommendations(diagnosis, asset, summary)
    simulation = load_model(Path("data/sample_reports/simulation_run.json"), SimulationRun)

    report = render_ops_report(
        summary=summary,
        anomalies=anomalies,
        diagnosis=diagnosis,
        maintenance=maintenance,
        asset=asset,
        audits=[],
        simulation=simulation,
    )

    assert "## 7.5 仿真验证" in report
    assert "仿真状态：`PASS`" in report
    assert "场景 ID：`SIM-SCENARIO-001`" in report
    assert "人工复核：`true`" in report
    assert "SIM_RESULT_COMPLETED" in report
    assert "## 11. 证据引用附录" in report

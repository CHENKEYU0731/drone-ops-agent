from __future__ import annotations

from pathlib import Path

import typer

from packages.anomaly_detection import detect_anomalies
from packages.audit_logger import write_audit_record
from packages.diagnosis_rules import generate_fault_hypotheses
from packages.drone_schemas import (
    AnomalyEvent,
    DroneAsset,
    FaultHypothesis,
    FlightLogSummary,
    MaintenanceRecommendation,
    load_model,
    load_model_list,
    write_model,
    write_model_list,
)
from packages.log_parsers import parse_flight_log
from packages.maintenance_rules import generate_maintenance_recommendations
from packages.report_templates import render_ops_report
from packages.telemetry_rules import summarize_flight


app = typer.Typer(help="无人机运维 Agent 离线 MVP CLI。")


@app.command("analyze-log")
def analyze_log_command(
    log: Path = typer.Option(..., "--log", help="CSV 或 JSON 飞行日志路径。"),
    asset: Path = typer.Option(..., "--asset", help="无人机资产 JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    _run_analyze_log(log, asset, out)
    typer.echo(f"日志分析完成: {out}")


@app.command("diagnose")
def diagnose_command(
    summary: Path = typer.Option(..., "--summary", help="flight_summary.json 路径。"),
    asset: Path = typer.Option(..., "--asset", help="无人机资产 JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    _run_diagnose(summary, asset, out)
    typer.echo(f"诊断和维护建议完成: {out}")


@app.command("generate-report")
def generate_report_command(
    summary: Path = typer.Option(..., "--summary", help="flight_summary.json 路径。"),
    diagnosis: Path = typer.Option(..., "--diagnosis", help="diagnosis.json 路径。"),
    maintenance: Path = typer.Option(..., "--maintenance", help="maintenance_recommendations.json 路径。"),
    out: Path = typer.Option(..., "--out", help="Markdown 报告输出路径。"),
    asset: Path = typer.Option(Path("data/sample_assets/uav_001.json"), "--asset", help="无人机资产 JSON 路径。"),
) -> None:
    _run_generate_report(summary, diagnosis, maintenance, out, asset)
    typer.echo(f"报告生成完成: {out}")


@app.command("run-mvp")
def run_mvp_command(
    log: Path = typer.Option(..., "--log", help="CSV 或 JSON 飞行日志路径。"),
    asset: Path = typer.Option(..., "--asset", help="无人机资产 JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    _run_analyze_log(log, asset, out)
    _run_diagnose(out / "flight_summary.json", asset, out)
    _run_generate_report(
        out / "flight_summary.json",
        out / "diagnosis.json",
        out / "maintenance_recommendations.json",
        out / "ops_report.md",
        asset,
    )
    typer.echo(f"MVP 流程完成: {out}")


def _run_analyze_log(log: Path, asset: Path, out: Path) -> tuple[FlightLogSummary, list[AnomalyEvent]]:
    out.mkdir(parents=True, exist_ok=True)
    drone = load_model(asset, DroneAsset)
    records = parse_flight_log(log)
    anomalies = detect_anomalies(records, drone_id=drone.drone_id, source_log_id=log.name)
    summary = summarize_flight(
        records,
        drone_id=drone.drone_id,
        source_log_id=log.name,
        anomaly_count=len(anomalies),
    )
    write_model(out / "flight_summary.json", summary)
    write_model_list(out / "anomalies.json", anomalies)
    write_audit_record(
        out_dir=out,
        skill_name="flight-log-analysis",
        skill_version="1.0.0",
        input_refs=[str(log), str(asset)],
        output_refs=[str(out / "flight_summary.json"), str(out / "anomalies.json")],
        tools_called=["parse_flight_log", "summarize_flight", "detect_anomalies"],
        rules_triggered=sorted({event.rule_id for event in anomalies}),
        human_review_required=bool(anomalies),
        status="success",
    )
    return summary, anomalies


def _run_diagnose(
    summary_path: Path,
    asset_path: Path,
    out: Path,
) -> tuple[list[FaultHypothesis], list[MaintenanceRecommendation]]:
    out.mkdir(parents=True, exist_ok=True)
    summary = load_model(summary_path, FlightLogSummary)
    anomalies_path = summary_path.parent / "anomalies.json"
    anomalies = load_model_list(anomalies_path, AnomalyEvent)
    asset = load_model(asset_path, DroneAsset)
    diagnosis = generate_fault_hypotheses(summary, anomalies, asset)
    maintenance = generate_maintenance_recommendations(diagnosis, asset, summary)
    write_model_list(out / "diagnosis.json", diagnosis)
    write_model_list(out / "maintenance_recommendations.json", maintenance)
    write_audit_record(
        out_dir=out,
        skill_name="fault-diagnosis",
        skill_version="1.0.0",
        input_refs=[str(summary_path), str(anomalies_path), str(asset_path)],
        output_refs=[str(out / "diagnosis.json")],
        tools_called=["generate_fault_hypotheses"],
        rules_triggered=[item.fault_name for item in diagnosis],
        human_review_required=True,
        status="success",
    )
    write_audit_record(
        out_dir=out,
        skill_name="maintenance-advisor",
        skill_version="1.0.0",
        input_refs=[str(summary_path), str(out / "diagnosis.json"), str(asset_path)],
        output_refs=[str(out / "maintenance_recommendations.json")],
        tools_called=["generate_maintenance_recommendations"],
        rules_triggered=[item.priority.value for item in maintenance],
        human_review_required=True,
        status="success",
    )
    return diagnosis, maintenance


def _run_generate_report(
    summary_path: Path,
    diagnosis_path: Path,
    maintenance_path: Path,
    out: Path,
    asset_path: Path,
) -> str:
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = load_model(summary_path, FlightLogSummary)
    anomalies_path = summary_path.parent / "anomalies.json"
    anomalies = load_model_list(anomalies_path, AnomalyEvent)
    diagnosis = load_model_list(diagnosis_path, FaultHypothesis)
    maintenance = load_model_list(maintenance_path, MaintenanceRecommendation)
    asset = load_model(asset_path, DroneAsset)
    audit = write_audit_record(
        out_dir=out.parent,
        skill_name="ops-report-generation",
        skill_version="1.0.0",
        input_refs=[str(summary_path), str(diagnosis_path), str(maintenance_path), str(anomalies_path), str(asset_path)],
        output_refs=[str(out)],
        tools_called=["render_ops_report"],
        rules_triggered=[],
        human_review_required=True,
        status="success",
    )
    report = render_ops_report(
        summary=summary,
        anomalies=anomalies,
        diagnosis=diagnosis,
        maintenance=maintenance,
        asset=asset,
        audits=[audit],
    )
    out.write_text(report, encoding="utf-8")
    return report


if __name__ == "__main__":
    app()

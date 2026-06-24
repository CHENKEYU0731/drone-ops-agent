from __future__ import annotations

from pathlib import Path

import typer

from packages.anomaly_detection import detect_anomalies
from packages.audit_logger import write_audit_record
from packages.diagnosis_rules import generate_fault_hypotheses
from packages.drone_schemas import (
    AnomalyEvent,
    BatteryAsset,
    DroneAsset,
    FaultHypothesis,
    FlightLogSummary,
    MaintenanceRecommendation,
    MissionPlan,
    MonitoringEvent,
    MonitoringSummary,
    PreflightCheckResult,
    load_model,
    load_model_list,
    read_json_file,
    write_model,
    write_model_list,
)
from packages.log_parsers import parse_flight_log
from packages.maintenance_rules import generate_maintenance_recommendations
from packages.preflight_rules import run_preflight_check
from packages.report_templates import render_ops_report
from packages.state_monitoring import run_monitoring_replay
from packages.telemetry_rules import summarize_flight


app = typer.Typer(help="无人机运维 Agent 离线 MVP CLI。")


def _run_cli(action) -> None:
    try:
        action()
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"错误: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command("analyze-log")
def analyze_log_command(
    log: Path = typer.Option(..., "--log", help="CSV 或 JSON 飞行日志路径。"),
    asset: Path = typer.Option(..., "--asset", help="无人机资产 JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    _run_cli(lambda: _run_analyze_log(log, asset, out))
    typer.echo(f"日志分析完成: {out}")


@app.command("diagnose")
def diagnose_command(
    summary: Path = typer.Option(..., "--summary", help="flight_summary.json 路径。"),
    asset: Path = typer.Option(..., "--asset", help="无人机资产 JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    _run_cli(lambda: _run_diagnose(summary, asset, out))
    typer.echo(f"诊断和维护建议完成: {out}")


@app.command("generate-report")
def generate_report_command(
    summary: Path = typer.Option(..., "--summary", help="flight_summary.json 路径。"),
    diagnosis: Path = typer.Option(..., "--diagnosis", help="diagnosis.json 路径。"),
    maintenance: Path = typer.Option(..., "--maintenance", help="maintenance_recommendations.json 路径。"),
    out: Path = typer.Option(..., "--out", help="Markdown 报告输出路径。"),
    asset: Path = typer.Option(Path("data/sample_assets/uav_001.json"), "--asset", help="无人机资产 JSON 路径。"),
) -> None:
    _run_cli(lambda: _run_generate_report(summary, diagnosis, maintenance, out, asset))
    typer.echo(f"报告生成完成: {out}")


@app.command("run-mvp")
def run_mvp_command(
    log: Path = typer.Option(..., "--log", help="CSV 或 JSON 飞行日志路径。"),
    asset: Path = typer.Option(..., "--asset", help="无人机资产 JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    _run_cli(
        lambda: (
            _run_analyze_log(log, asset, out),
            _run_diagnose(out / "flight_summary.json", asset, out),
            _run_generate_report(
                out / "flight_summary.json",
                out / "diagnosis.json",
                out / "maintenance_recommendations.json",
                out / "ops_report.md",
                asset,
            ),
        )
    )
    typer.echo(f"MVP 流程完成: {out}")


@app.command("preflight-check")
def preflight_check_command(
    asset: Path = typer.Option(..., "--asset", help="无人机资产 JSON 路径。"),
    battery: Path = typer.Option(..., "--battery", help="电池资产 JSON 路径。"),
    mission: Path = typer.Option(..., "--mission", help="任务计划 JSON 路径。"),
    observations: Path = typer.Option(..., "--observations", help="飞行前观测 JSON 路径。"),
    rules: Path = typer.Option(..., "--rules", help="飞行前检查规则 YAML 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    _run_cli(lambda: _run_preflight_check(asset, battery, mission, observations, rules, out))
    typer.echo(f"飞行前检查完成: {out}")


@app.command("monitor-replay")
def monitor_replay_command(
    telemetry: Path = typer.Option(..., "--telemetry", help="CSV 或 JSON 离线遥测文件路径。"),
    asset: Path = typer.Option(..., "--asset", help="无人机资产 JSON 路径。"),
    rules: Path = typer.Option(..., "--rules", help="状态监控规则 YAML 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    _run_cli(lambda: _run_monitor_replay(telemetry, asset, rules, out))
    typer.echo(f"状态监控回放完成: {out}")


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


def _run_preflight_check(
    asset_path: Path,
    battery_path: Path,
    mission_path: Path,
    observations_path: Path,
    rules_path: Path,
    out: Path,
) -> PreflightCheckResult:
    out.mkdir(parents=True, exist_ok=True)
    asset = load_model(asset_path, DroneAsset)
    battery = load_model(battery_path, BatteryAsset)
    mission = load_model(mission_path, MissionPlan)
    observations = read_json_file(observations_path)
    if not isinstance(observations, dict):
        raise ValueError(f"飞行前观测 JSON 必须是对象: {observations_path}")
    result = run_preflight_check(asset, battery, mission, observations, rules_path)
    output_path = out / "preflight_check_result.json"
    write_model(output_path, result)
    write_audit_record(
        out_dir=out,
        skill_name="preflight-check",
        skill_version="1.0.0",
        input_refs=[str(asset_path), str(battery_path), str(mission_path), str(observations_path), str(rules_path)],
        output_refs=[str(output_path)],
        tools_called=["load_preflight_rules", "run_preflight_check"],
        rules_triggered=sorted({item.rule_id for item in [*result.blocking_items, *result.warnings]}),
        human_review_required=result.human_review_required,
        status="success",
    )
    return result


def _run_monitor_replay(
    telemetry_path: Path,
    asset_path: Path,
    rules_path: Path,
    out: Path,
) -> tuple[MonitoringSummary, list[MonitoringEvent]]:
    out.mkdir(parents=True, exist_ok=True)
    asset = load_model(asset_path, DroneAsset)
    summary, events = run_monitoring_replay(telemetry_path, asset, rules_path)
    summary_path = out / "monitoring_summary.json"
    events_path = out / "monitoring_events.json"
    write_model(summary_path, summary)
    write_model_list(events_path, events)
    write_audit_record(
        out_dir=out,
        skill_name="state-monitoring",
        skill_version="1.0.0",
        input_refs=[str(telemetry_path), str(asset_path), str(rules_path)],
        output_refs=[str(summary_path), str(events_path)],
        tools_called=["parse_telemetry_replay", "load_monitoring_rules", "run_monitoring_replay"],
        rules_triggered=sorted({event.rule_id for event in events}),
        human_review_required=summary.human_review_required,
        status="success",
    )
    return summary, events


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

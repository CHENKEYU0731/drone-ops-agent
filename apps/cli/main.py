from __future__ import annotations

from pathlib import Path

import typer

from packages.anomaly_detection import detect_anomalies
from packages.audit_logger import write_audit_record
from packages.adapter_workflows import validate_adapter_registry, validate_approval_packet
from packages.diagnosis_rules import generate_fault_hypotheses
from packages.dashboard import build_dashboard_bundle
from packages.dataset_registry import validate_dataset_registry
from packages.drone_schemas import (
    AnomalyEvent,
    BatteryAsset,
    DroneAsset,
    FaultHypothesis,
    FleetHealthSummary,
    FlightLogSummary,
    MaintenanceRecommendation,
    MissionPlan,
    MonitoringEvent,
    MonitoringSummary,
    ReportBundleManifest,
    PreflightCheckResult,
    SimulationRun,
    SimulationScenario,
    WorkOrderDraft,
    load_model,
    load_model_list,
    read_json_file,
    write_json,
    write_model,
    write_model_list,
    SkillRunAudit,
)
from packages.evals import render_case_study_report, run_case_study, run_eval_suite
from packages.fleet_health import build_fleet_health_summary, load_fleet_manifest, render_fleet_health_report
from packages.log_parsers import SUPPORTED_LOG_FORMATS, ParsedFlightLog, parse_flight_log_details
from packages.maintenance_rules import generate_maintenance_recommendations
from packages.organization_handoff import validate_handoff_package
from packages.open_source_logs import (
    render_open_source_log_case_study,
    run_open_source_log_case_study,
    validate_open_source_log_registry,
)
from packages.operations_platform import validate_operations_platform
from packages.platform_index import validate_platform_index
from packages.platform_readiness import build_report_bundle_manifest, validate_platform_readiness
from packages.preflight_rules import run_preflight_check
from packages.report_validation import ReportValidationError, ReportValidationPaths, validate_report_outputs
from packages.report_templates import export_markdown_to_pdf, render_ops_report
from packages.rule_packs import build_skill_registry, list_rule_pack_refs, validate_rule_pack
from packages.simulation import parse_simulation_result, validate_simulation_result
from packages.state_monitoring import run_monitoring_replay
from packages.telemetry_rules import summarize_flight
from packages.work_orders import generate_work_order_drafts, render_work_order_drafts_markdown
from packages.work_orders import WorkOrderValidationError, validate_work_order_drafts
from packages.work_orders.validation import WorkOrderValidationResult


app = typer.Typer(help="无人机运维离线决策支持平台 CLI。")


def _run_cli(action) -> None:
    try:
        action()
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"错误: {exc}", err=True)
        raise typer.Exit(code=1) from exc


def _require_pass(result: dict) -> None:
    if result.get("status") != "PASS":
        raise typer.Exit(code=1)


@app.command("analyze-log")
def analyze_log_command(
    log: Path = typer.Option(..., "--log", help="CSV、JSON、PX4 ULog 或 ArduPilot BIN 飞行日志路径。"),
    asset: Path = typer.Option(..., "--asset", help="无人机资产 JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
    log_format: str = typer.Option("auto", "--format", help="auto, csv, json, px4-ulog, ardupilot-bin"),
) -> None:
    _run_cli(lambda: _run_analyze_log(log, asset, out, log_format))
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
    anomalies: Path | None = typer.Option(None, "--anomalies", help="anomalies.json 路径。"),
    diagnosis: Path = typer.Option(..., "--diagnosis", help="diagnosis.json 路径。"),
    maintenance: Path = typer.Option(..., "--maintenance", help="maintenance_recommendations.json 路径。"),
    simulation: Path | None = typer.Option(None, "--simulation", help="simulation_run.json 路径。"),
    work_orders: Path | None = typer.Option(None, "--work-orders", help="work_order_drafts.json 路径。"),
    work_order_validation: Path | None = typer.Option(
        None,
        "--work-order-validation",
        help="work_order_validation.json 路径。",
    ),
    out: Path = typer.Option(..., "--out", help="Markdown 报告输出路径。"),
    pdf: Path | None = typer.Option(None, "--pdf", help="PDF 报告输出路径。"),
    asset: Path = typer.Option(Path("data/sample_assets/uav_001.json"), "--asset", help="无人机资产 JSON 路径。"),
) -> None:
    _run_cli(
        lambda: _run_generate_report(
            summary,
            diagnosis,
            maintenance,
            out,
            asset,
            pdf,
            anomalies,
            simulation,
            work_orders,
            work_order_validation,
        )
    )
    typer.echo(f"报告生成完成: {out}")


@app.command("generate-work-orders")
def generate_work_orders_command(
    maintenance: Path = typer.Option(..., "--maintenance", help="maintenance_recommendations.json 路径。"),
    asset: Path = typer.Option(..., "--asset", help="无人机资产 JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    _run_cli(lambda: _run_generate_work_orders(maintenance, asset, out))
    typer.echo(f"工单草稿生成完成: {out}")


@app.command("validate-work-orders")
def validate_work_orders_command(
    drafts: Path = typer.Option(..., "--drafts", help="work_order_drafts.json 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    try:
        result = _run_validate_work_orders(drafts, out)
    except WorkOrderValidationError as exc:
        typer.echo("Error: work order validation failed", err=True)
        for error in exc.errors:
            typer.echo(f"- {error}", err=True)
        raise typer.Exit(code=1) from exc
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("Work order validation passed")
    typer.echo(f"validated drafts: {result.counts.validated_drafts}")
    typer.echo(f"evidence refs: {result.counts.evidence_refs}")


@app.command("fleet-summary")
def fleet_summary_command(
    manifest: Path = typer.Option(..., "--manifest", help="本地 fleet manifest JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
    markdown: Path | None = typer.Option(None, "--markdown", help="可选 fleet Markdown 报告输出路径。"),
) -> None:
    _run_cli(lambda: _run_fleet_summary(manifest, out, markdown))
    typer.echo(f"机队健康摘要生成完成: {out}")


@app.command("dashboard-bundle")
def dashboard_bundle_command(
    report_dir: Path = typer.Option(..., "--report-dir", help="本地报告目录。"),
    out: Path = typer.Option(..., "--out", help="dashboard_bundle.json 输出路径。"),
    fleet_summary: Path | None = typer.Option(None, "--fleet-summary", help="可选 fleet_health_summary.json 路径。"),
    fleet_report: Path | None = typer.Option(None, "--fleet-report", help="可选 fleet_health_report.md 路径。"),
) -> None:
    _run_cli(lambda: _run_dashboard_bundle(report_dir, out, fleet_summary, fleet_report))
    typer.echo(f"Dashboard 数据包生成完成: {out}")


@app.command("build-report-bundle")
def build_report_bundle_command(
    report_dir: Path = typer.Option(..., "--report-dir", help="本地报告目录。"),
    workspace_project_id: str = typer.Option(..., "--workspace-project-id", help="本地 workspace project id。"),
    bundle_id: str = typer.Option(..., "--bundle-id", help="本地 report bundle id。"),
    out: Path = typer.Option(..., "--out", help="report_bundle_manifest.json 输出路径。"),
    drone_id: str | None = typer.Option(None, "--drone-id", help="可选无人机 ID。"),
) -> None:
    _run_cli(lambda: _run_build_report_bundle(report_dir, workspace_project_id, bundle_id, out, drone_id))
    typer.echo(f"Report bundle manifest 写出完成: {out}")


@app.command("validate-platform-readiness")
def validate_platform_readiness_command(
    workspace: Path = typer.Option(..., "--workspace", help="workspace_project.json 路径。"),
    bundle: Path = typer.Option(..., "--bundle", help="report_bundle_manifest.json 路径。"),
    checklist: Path = typer.Option(..., "--checklist", help="platform_readiness_checklist.json 路径。"),
    out: Path = typer.Option(..., "--out", help="platform_readiness_validation.json 输出路径。"),
    adapter: list[Path] = typer.Option([], "--adapter", help="可选 offline adapter contract JSON，可重复。"),
) -> None:
    result = _run_validate_platform_readiness(workspace, bundle, checklist, out, adapter)
    if result["status"] == "PASS":
        typer.echo("Platform readiness validation passed")
    else:
        typer.echo("Platform readiness validation requires review")
    typer.echo(f"findings: {result['counts']['findings']}")
    _require_pass(result)


@app.command("validate-rule-pack")
def validate_rule_pack_command(
    rule_pack: Path = typer.Option(..., "--rule-pack", help="本地 rule pack JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="rule_pack_validation.json 输出路径。"),
) -> None:
    _run_cli(lambda: _run_validate_rule_pack(rule_pack, out))
    typer.echo(f"规则包验证完成: {out}")


@app.command("list-skills")
def list_skills_command(
    out: Path = typer.Option(..., "--out", help="skill_registry.json 输出路径。"),
    rule_pack: list[Path] = typer.Option([], "--rule-pack", help="可选本地 rule pack JSON 路径，可重复。"),
) -> None:
    _run_cli(lambda: _run_list_skills(rule_pack, out))
    typer.echo(f"Skill registry 写出完成: {out}")


@app.command("list-rule-packs")
def list_rule_packs_command(
    out: Path = typer.Option(..., "--out", help="rule_packs.json 输出路径。"),
    rule_pack: list[Path] = typer.Option([], "--rule-pack", help="可选本地 rule pack JSON 路径，可重复。"),
) -> None:
    _run_cli(lambda: _run_list_rule_packs(rule_pack, out))
    typer.echo(f"规则包列表写出完成: {out}")


@app.command("run-evals")
def run_evals_command(
    case: list[Path] = typer.Option(..., "--case", help="本地 eval case JSON 路径，可重复。"),
    out: Path = typer.Option(..., "--out", help="eval_results.json 输出目录。"),
) -> None:
    payload = _run_evals(case, out)
    typer.echo(f"Eval suite status: {payload['status']}")
    typer.echo(f"Eval suite score: {payload['score']}")
    _require_pass(payload)


@app.command("run-case-studies")
def run_case_studies_command(
    simulation_matrix: Path = typer.Option(..., "--simulation-matrix", help="离线仿真场景矩阵 JSON 路径。"),
    eval_case: list[Path] = typer.Option([], "--eval-case", help="诊断/报告 eval case JSON 路径，可重复。"),
    out: Path = typer.Option(..., "--out", help="案例研究输出目录。"),
) -> None:
    payload = _run_case_studies(simulation_matrix, eval_case, out)
    typer.echo(f"Case study status: {payload['status']}")
    typer.echo(f"Case study accuracy: {payload['metrics']['expected_status_accuracy']}")
    if payload["status"] != "PASS":
        raise typer.Exit(code=1)


@app.command("validate-open-log-registry")
def validate_open_log_registry_command(
    registry: Path = typer.Option(..., "--registry", help="开源日志注册表 JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="注册表验证结果 JSON 路径。"),
) -> None:
    payload = _run_validate_open_log_registry(registry, out)
    typer.echo(f"Open-source log registry status: {payload['status']}")


@app.command("run-open-log-case-studies")
def run_open_log_case_studies_command(
    registry: Path = typer.Option(..., "--registry", help="开源日志注册表 JSON 路径。"),
    cache_dir: Path = typer.Option(..., "--cache-dir", help="已经显式下载并校验的本地缓存目录。"),
    drone_id: str = typer.Option(..., "--drone-id", help="案例研究使用的本地资产标识。"),
    out: Path = typer.Option(..., "--out", help="案例研究输出目录。"),
) -> None:
    payload = _run_open_log_case_studies(registry, cache_dir, drone_id, out)
    typer.echo(f"Open-source log case study status: {payload['status']}")
    if payload["status"] != "PASS":
        raise typer.Exit(code=1)


@app.command("validate-datasets")
def validate_datasets_command(
    registry: Path = typer.Option(..., "--registry", help="dataset registry JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="dataset_validation.json 输出路径。"),
) -> None:
    result = _run_validate_datasets(registry, out)
    if result["status"] == "PASS":
        typer.echo("Dataset registry validation passed")
    else:
        typer.echo("Dataset registry validation requires review")
    typer.echo(f"cases: {result['counts']['cases']}")
    typer.echo(f"findings: {result['counts']['findings']}")
    _require_pass(result)


@app.command("validate-adapters")
def validate_adapters_command(
    registry: Path = typer.Option(..., "--registry", help="offline_adapter_registry.json 路径。"),
    out: Path = typer.Option(..., "--out", help="adapter_validation.json 输出路径。"),
) -> None:
    result = _run_validate_adapters(registry, out)
    if result["status"] == "PASS":
        typer.echo("Adapter registry validation passed")
    else:
        typer.echo("Adapter registry validation requires review")
    typer.echo(f"adapters: {result['counts']['adapters']}")
    typer.echo(f"findings: {result['counts']['findings']}")
    _require_pass(result)


@app.command("validate-approvals")
def validate_approvals_command(
    packet: Path = typer.Option(..., "--packet", help="approval_packet.json 路径。"),
    out: Path = typer.Option(..., "--out", help="approval_validation.json 输出路径。"),
) -> None:
    result = _run_validate_approvals(packet, out)
    if result["status"] == "PASS":
        typer.echo("Approval workflow validation passed")
    else:
        typer.echo("Approval workflow validation requires review")
    typer.echo(f"approvals: {result['counts']['approvals']}")
    typer.echo(f"findings: {result['counts']['findings']}")
    _require_pass(result)


@app.command("validate-handoff-package")
def validate_handoff_package_command(
    package: Path = typer.Option(..., "--package", help="organization_handoff_package.json 路径。"),
    out: Path = typer.Option(..., "--out", help="handoff_validation.json 输出路径。"),
) -> None:
    result = _run_validate_handoff_package(package, out)
    if result["status"] == "PASS":
        typer.echo("Organization handoff package validation passed")
    else:
        typer.echo("Organization handoff package validation requires review")
    typer.echo(f"artifacts: {result['counts']['artifacts']}")
    typer.echo(f"findings: {result['counts']['findings']}")
    _require_pass(result)


@app.command("validate-platform-index")
def validate_platform_index_command(
    index: Path = typer.Option(..., "--index", help="platform_readiness_index.json 路径。"),
    out: Path = typer.Option(..., "--out", help="platform_index_validation.json 输出路径。"),
) -> None:
    result = _run_validate_platform_index(index, out)
    if result["status"] == "PASS":
        typer.echo("Platform readiness index validation passed")
    else:
        typer.echo("Platform readiness index validation requires review")
    typer.echo(f"capabilities: {result['counts']['capabilities']}")
    typer.echo(f"findings: {result['counts']['findings']}")
    if result["status"] != "PASS":
        raise typer.Exit(code=1)


@app.command("validate-operations-platform")
def validate_operations_platform_command(
    baseline: Path = typer.Option(..., "--baseline", help="operations_platform_baseline.json 路径。"),
    out: Path = typer.Option(..., "--out", help="operations_platform_validation.json 输出路径。"),
) -> None:
    result = _run_validate_operations_platform(baseline, out)
    if result["status"] == "PASS":
        typer.echo("Operations platform baseline validation passed")
    else:
        typer.echo("Operations platform baseline validation requires review")
    typer.echo(f"modules: {result['counts']['modules']}")
    typer.echo(f"findings: {result['counts']['findings']}")
    if result["status"] != "PASS":
        raise typer.Exit(code=1)


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
                None,
            ),
        )
    )
    typer.echo(f"核心离线流程完成: {out}")


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


@app.command("validate-simulation")
def validate_simulation_command(
    scenario: Path = typer.Option(..., "--scenario", help="离线仿真场景 JSON 路径。"),
    result: Path = typer.Option(..., "--result", help="离线仿真结果 JSON 路径。"),
    out: Path = typer.Option(..., "--out", help="输出目录。"),
) -> None:
    _run_cli(lambda: _run_validate_simulation(scenario, result, out))
    typer.echo(f"仿真验证完成: {out}")


@app.command("export-pdf")
def export_pdf_command(
    markdown: Path = typer.Option(..., "--markdown", help="Markdown 报告输入路径。"),
    out: Path = typer.Option(..., "--out", help="PDF 报告输出路径。"),
) -> None:
    _run_cli(lambda: export_markdown_to_pdf(markdown, out))
    typer.echo(f"PDF 报告导出完成: {out}")


@app.command("validate-report")
def validate_report_command(
    report_dir: Path | None = typer.Option(None, "--report-dir", help="包含 run-mvp 输出的目录。"),
    summary: Path | None = typer.Option(None, "--summary", help="flight_summary.json 路径。"),
    anomalies: Path | None = typer.Option(None, "--anomalies", help="anomalies.json 路径。"),
    diagnosis: Path | None = typer.Option(None, "--diagnosis", help="diagnosis.json 路径。"),
    maintenance: Path | None = typer.Option(None, "--maintenance", help="maintenance_recommendations.json 路径。"),
    report: Path | None = typer.Option(None, "--report", help="ops_report.md 路径。"),
    audit_dir: Path | None = typer.Option(None, "--audit-dir", help="audit JSON 目录。"),
    write_index: bool = typer.Option(False, "--write-index", help="写出 evidence_index.json 和 report_validation.json。"),
) -> None:
    try:
        paths = _resolve_report_validation_paths(report_dir, summary, anomalies, diagnosis, maintenance, report, audit_dir)
        result = validate_report_outputs(paths, write_index=write_index)
    except ReportValidationError as exc:
        typer.echo("Error: report validation failed", err=True)
        for error in exc.errors:
            typer.echo(f"- {error}", err=True)
        raise typer.Exit(code=1) from exc
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("Report validation passed")
    typer.echo(f"evidence refs: {result.counts.evidence_refs}")
    typer.echo(f"validated anomalies: {result.counts.validated_anomalies}")
    typer.echo(f"validated hypotheses: {result.counts.validated_hypotheses}")
    typer.echo(f"validated recommendations: {result.counts.validated_recommendations}")
    typer.echo(f"validated audit files: {result.counts.validated_audit_files}")


def _resolve_report_validation_paths(
    report_dir: Path | None,
    summary: Path | None,
    anomalies: Path | None,
    diagnosis: Path | None,
    maintenance: Path | None,
    report: Path | None,
    audit_dir: Path | None,
) -> ReportValidationPaths:
    if report_dir is not None:
        return ReportValidationPaths.from_report_dir(report_dir)

    explicit_paths = {
        "summary": summary,
        "anomalies": anomalies,
        "diagnosis": diagnosis,
        "maintenance": maintenance,
        "report": report,
        "audit_dir": audit_dir,
    }
    missing = [name for name, path in explicit_paths.items() if path is None]
    if missing:
        raise ValueError("validate-report requires --report-dir or explicit paths for: " + ", ".join(missing))
    return ReportValidationPaths(
        summary=summary,
        anomalies=anomalies,
        diagnosis=diagnosis,
        maintenance=maintenance,
        report=report,
        audit_dir=audit_dir,
    )


def _run_analyze_log(
    log: Path,
    asset: Path,
    out: Path,
    log_format: str = "auto",
) -> tuple[FlightLogSummary, list[AnomalyEvent]]:
    if log_format not in SUPPORTED_LOG_FORMATS:
        supported = ", ".join(SUPPORTED_LOG_FORMATS)
        raise ValueError(f"Unsupported log format '{log_format}'. Supported formats: {supported}")
    out.mkdir(parents=True, exist_ok=True)
    drone = load_model(asset, DroneAsset)
    parsed = parse_flight_log_details(log, requested_format=log_format)
    records = parsed.records
    anomalies = detect_anomalies(records, drone_id=drone.drone_id, source_log_id=parsed.source_log_id)
    summary = summarize_flight(
        records,
        drone_id=drone.drone_id,
        source_log_id=parsed.source_log_id,
        anomaly_count=len(anomalies),
    )
    _annotate_summary_evidence(summary, parsed)
    write_model(out / "flight_summary.json", summary)
    write_model_list(out / "anomalies.json", anomalies)
    write_audit_record(
        out_dir=out,
        skill_name="flight-log-analysis",
        skill_version="1.0.0",
        input_refs=[str(log), str(asset), f"format={log_format}", f"parser={parsed.parser_name}@{parsed.parser_version}"],
        output_refs=[str(out / "flight_summary.json"), str(out / "anomalies.json")],
        tools_called=[
            f"parse_flight_log_with_metadata:{parsed.parser_name}@{parsed.parser_version}",
            "summarize_flight",
            "detect_anomalies",
        ],
        rules_triggered=sorted({event.rule_id for event in anomalies}),
        human_review_required=bool(anomalies),
        status="success",
        metadata={
            "requested_format": parsed.requested_format,
            "actual_format": parsed.actual_format,
            "parser_name": parsed.parser_name,
            "parser_version": parsed.parser_version,
            "warnings": parsed.warnings,
            "source_metadata": parsed.source_metadata,
            "parser_metadata": parsed.parser_metadata,
        },
    )
    return summary, anomalies


def _annotate_summary_evidence(summary: FlightLogSummary, parsed: ParsedFlightLog) -> None:
    for evidence in summary.evidence_refs:
        source_path = parsed.source_metadata.get("path", parsed.source_log_id)
        evidence.source_id = f"{parsed.source_log_id}:{source_path}"
        evidence.description = (
            f"{evidence.description} Parser={parsed.parser_name} "
            f"{parsed.parser_version}; format={parsed.actual_format}; field={evidence.field}."
        )


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


def _run_validate_simulation(
    scenario_path: Path,
    result_path: Path,
    out: Path,
) -> SimulationRun:
    out.mkdir(parents=True, exist_ok=True)
    scenario = load_model(scenario_path, SimulationScenario)
    result = parse_simulation_result(result_path)
    run = validate_simulation_result(
        scenario,
        result,
        scenario_path=scenario_path,
        result_path=result_path,
    )
    output_path = out / "simulation_run.json"
    write_model(output_path, run)
    write_audit_record(
        out_dir=out,
        skill_name="simulation-validation",
        skill_version="1.0.0",
        input_refs=[str(scenario_path), str(result_path)],
        output_refs=[str(output_path)],
        tools_called=["parse_simulation_result", "validate_simulation_result"],
        rules_triggered=sorted({ref.rule_id for ref in run.evidence_refs} | {item.rule_id for item in run.rule_results}),
        human_review_required=True,
        status="success",
        metadata={
            "scenario_id": scenario.scenario_id,
            "result_id": result.result_id,
            "result_source": result.source,
            "simulation_status": run.status,
            "safety_boundary": "offline-import-only",
        },
    )
    return run


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
    pdf_path: Path | None = None,
    anomalies_path: Path | None = None,
    simulation_path: Path | None = None,
    work_orders_path: Path | None = None,
    work_order_validation_path: Path | None = None,
) -> str:
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = load_model(summary_path, FlightLogSummary)
    resolved_anomalies_path = anomalies_path or summary_path.parent / "anomalies.json"
    anomalies = load_model_list(resolved_anomalies_path, AnomalyEvent)
    diagnosis = load_model_list(diagnosis_path, FaultHypothesis)
    maintenance = load_model_list(maintenance_path, MaintenanceRecommendation)
    asset = load_model(asset_path, DroneAsset)
    simulation = load_model(simulation_path, SimulationRun) if simulation_path is not None else None
    work_orders = load_model_list(work_orders_path, WorkOrderDraft) if work_orders_path is not None else None
    work_order_validation = (
        load_model(work_order_validation_path, WorkOrderValidationResult)
        if work_order_validation_path is not None
        else None
    )
    previous_audits = _load_report_audits(out.parent)
    audit = write_audit_record(
        out_dir=out.parent,
        skill_name="ops-report-generation",
        skill_version="1.0.0",
        input_refs=[
            str(summary_path),
            str(diagnosis_path),
            str(maintenance_path),
            str(resolved_anomalies_path),
            str(asset_path),
            *([str(simulation_path)] if simulation_path is not None else []),
            *([str(work_orders_path)] if work_orders_path is not None else []),
            *([str(work_order_validation_path)] if work_order_validation_path is not None else []),
        ],
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
        audits=[*previous_audits, audit],
        simulation=simulation,
        work_orders=work_orders,
        work_order_validation=work_order_validation,
    )
    out.write_text(report, encoding="utf-8")
    if pdf_path is not None:
        export_markdown_to_pdf(out, pdf_path)
    return report


def _load_report_audits(report_dir: Path) -> list[SkillRunAudit]:
    audit_dir = report_dir / "audit"
    if not audit_dir.exists():
        return []
    audits: list[SkillRunAudit] = []
    for path in sorted(audit_dir.glob("*.json")):
        audit = load_model(path, SkillRunAudit)
        if audit.skill_name == "ops-report-generation":
            continue
        audits.append(audit)
    return sorted(audits, key=lambda item: (item.created_at.isoformat(), item.skill_name, item.run_id))


def _run_generate_work_orders(
    maintenance_path: Path,
    asset_path: Path,
    out: Path,
) -> list[WorkOrderDraft]:
    out.mkdir(parents=True, exist_ok=True)
    recommendations = load_model_list(maintenance_path, MaintenanceRecommendation)
    asset = load_model(asset_path, DroneAsset)
    drafts = generate_work_order_drafts(recommendations, asset)
    drafts_path = out / "work_order_drafts.json"
    markdown_path = out / "work_order_drafts.md"
    write_model_list(drafts_path, drafts)
    markdown_path.write_text(render_work_order_drafts_markdown(drafts), encoding="utf-8")
    write_audit_record(
        out_dir=out,
        skill_name="work-order-drafting",
        skill_version="1.0.0",
        input_refs=[str(maintenance_path), str(asset_path)],
        output_refs=[str(drafts_path), str(markdown_path)],
        tools_called=["generate_work_order_drafts", "render_work_order_drafts_markdown"],
        rules_triggered=[draft.priority.value for draft in drafts],
        human_review_required=True,
        status="success",
        metadata={
            "draft_count": len(drafts),
            "safety_boundary": "offline-draft-only",
        },
    )
    return drafts


def _run_validate_work_orders(
    drafts_path: Path,
    out: Path,
):
    out.mkdir(parents=True, exist_ok=True)
    payload = read_json_file(drafts_path)
    if not isinstance(payload, list):
        raise ValueError(f"work_order_drafts.json 必须是列表: {drafts_path}")
    drafts = [item for item in payload if isinstance(item, dict)]
    if len(drafts) != len(payload):
        raise ValueError(f"work_order_drafts.json 中的每一项都必须是对象: {drafts_path}")
    result = validate_work_order_drafts(drafts, checked_files={"drafts": str(drafts_path)})
    validation_path = out / "work_order_validation.json"
    write_json(validation_path, result.serializable_payload())
    write_audit_record(
        out_dir=out,
        skill_name="work-order-validation",
        skill_version="1.0.0",
        input_refs=[str(drafts_path)],
        output_refs=[str(validation_path)],
        tools_called=["validate_work_order_drafts"],
        rules_triggered=[],
        human_review_required=True,
        status="success",
        metadata={
            "validated_drafts": result.counts.validated_drafts,
            "safety_boundary": "offline-validation-only",
        },
    )
    return result


def _run_fleet_summary(
    manifest_path: Path,
    out: Path,
    markdown_path: Path | None = None,
) -> FleetHealthSummary:
    out.mkdir(parents=True, exist_ok=True)
    manifest = load_fleet_manifest(manifest_path)
    summary = build_fleet_health_summary(manifest)
    output_path = out / "fleet_health_summary.json"
    write_model(output_path, summary)
    output_refs = [str(output_path)]
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_fleet_health_report(summary), encoding="utf-8")
        output_refs.append(str(markdown_path))
    write_audit_record(
        out_dir=out,
        skill_name="fleet-health-analytics",
        skill_version="1.1.0",
        input_refs=[str(manifest_path), *summary.source_refs],
        output_refs=output_refs,
        tools_called=["load_fleet_manifest", "build_fleet_health_summary"],
        rules_triggered=sorted({finding.evidence_refs[0].rule_id for finding in summary.findings if finding.evidence_refs}),
        human_review_required=True,
        status="success",
        metadata={
            "fleet_id": summary.fleet_id,
            "asset_count": summary.asset_count,
            "flight_count": summary.flight_count,
            "highest_risk": summary.highest_risk.value,
            "safety_boundary": "offline-fleet-summary-only",
        },
    )
    return summary


def _run_dashboard_bundle(
    report_dir: Path,
    out: Path,
    fleet_summary: Path | None = None,
    fleet_report: Path | None = None,
    reference_root: Path | None = None,
) -> dict:
    bundle = build_dashboard_bundle(
        report_dir=report_dir,
        fleet_summary=fleet_summary,
        fleet_report=fleet_report,
        reference_root=reference_root,
    )
    write_json(out, bundle)
    return bundle


def _run_build_report_bundle(
    report_dir: Path,
    workspace_project_id: str,
    bundle_id: str,
    out: Path,
    drone_id: str | None = None,
) -> ReportBundleManifest:
    manifest = build_report_bundle_manifest(
        report_dir=report_dir,
        workspace_project_id=workspace_project_id,
        bundle_id=bundle_id,
        drone_id=drone_id,
    )
    write_model(out, manifest)
    write_audit_record(
        out_dir=out.parent,
        skill_name="platform-readiness",
        skill_version="1.5.0",
        input_refs=[str(report_dir), f"workspace_project_id={workspace_project_id}", f"bundle_id={bundle_id}"],
        output_refs=[str(out)],
        tools_called=["build_report_bundle_manifest"],
        rules_triggered=[],
        human_review_required=True,
        status="success",
        metadata={
            "bundle_id": manifest.bundle_id,
            "file_count": manifest.file_count,
            "safety_boundary": "offline-report-bundle-only",
        },
    )
    return manifest


def _run_validate_platform_readiness(
    workspace: Path,
    bundle: Path,
    checklist: Path,
    out: Path,
    adapters: list[Path],
) -> dict:
    result = validate_platform_readiness(
        workspace_path=workspace,
        bundle_path=bundle,
        checklist_path=checklist,
        adapter_paths=adapters,
    )
    write_json(out, result)
    write_audit_record(
        out_dir=out.parent,
        skill_name="platform-readiness-validation",
        skill_version="1.5.0",
        input_refs=[str(workspace), str(bundle), str(checklist), *[str(path) for path in adapters]],
        output_refs=[str(out)],
        tools_called=["validate_platform_readiness"],
        rules_triggered=[finding["code"] for finding in result["findings"]],
        human_review_required=True,
        status="success",
        metadata={
            "validation_status": result["status"],
            "safety_boundary": "offline-platform-readiness-only",
        },
    )
    return result


def _run_validate_rule_pack(rule_pack_path: Path, out: Path) -> dict:
    result = validate_rule_pack(rule_pack_path)
    write_json(out, result)
    return result


def _run_list_skills(rule_pack_paths: list[Path], out: Path) -> dict:
    registry = build_skill_registry(rule_pack_paths=rule_pack_paths)
    write_json(out, registry)
    return registry


def _run_list_rule_packs(rule_pack_paths: list[Path], out: Path) -> dict:
    payload = {
        "schema_version": 1,
        "generated_at": "1970-01-01T00:00:00Z",
        "rule_packs": list_rule_pack_refs(rule_pack_paths),
        "human_review_required": True,
    }
    write_json(out, payload)
    return payload


def _run_evals(case_paths: list[Path], out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    output_path = out / "eval_results.json"
    report_path = out / "eval_report.md"
    payload = run_eval_suite(case_paths, output_path=output_path, report_path=report_path)
    rules_triggered = sorted(
        {
            metric["metric_id"]
            for result in payload["results"]
            for metric in result["metric_results"]
            if metric["status"] != "PASS" or payload["status"] == "PASS"
        }
    )
    write_audit_record(
        out_dir=out,
        skill_name="diagnosis-report-evaluation",
        skill_version="1.4.0",
        input_refs=[str(path) for path in case_paths],
        output_refs=[str(output_path), str(report_path)],
        tools_called=["run_eval_suite"],
        rules_triggered=rules_triggered,
        human_review_required=True,
        status="success",
        metadata={
            "eval_status": payload["status"],
            "case_count": payload["case_count"],
            "safety_boundary": "offline-eval-only",
        },
    )
    return payload


def _run_case_studies(simulation_matrix: Path, eval_case_paths: list[Path], out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    output_path = out / "case_study_results.json"
    report_path = out / "case_study_report.md"
    payload = run_case_study(simulation_matrix, eval_case_paths)
    write_json(output_path, payload)
    report_path.write_text(render_case_study_report(payload), encoding="utf-8")
    case_study_rules = {
        "CASE_EVIDENCE_COVERAGE",
        "CASE_EXPECTED_STATUS_MATCH",
        "CASE_FALSE_ALARM_COUNT",
        "CASE_MISSED_RISK_COUNT",
    }
    case_study_rules.update(
        rule_id
        for case in payload["simulation"]["cases"]
        for rule_id in case["triggered_rule_ids"]
    )
    rules_triggered = sorted(case_study_rules)
    audit_status = {
        "PASS": "success",
        "REVIEW_REQUIRED": "review_required",
        "FAIL": "failed",
    }.get(payload["status"], "failed")
    write_audit_record(
        out_dir=out,
        skill_name="evaluation-case-study",
        skill_version="2.2.0",
        input_refs=[str(simulation_matrix), *(str(path) for path in eval_case_paths)],
        output_refs=[str(output_path), str(report_path)],
        tools_called=["run_case_study"],
        rules_triggered=rules_triggered,
        human_review_required=True,
        status=audit_status,
        metadata={
            "case_study_status": payload["status"],
            "case_count": payload["case_count"],
            "expected_status_accuracy": payload["metrics"]["expected_status_accuracy"],
            "safety_boundary": "offline-case-study-only",
        },
    )
    return payload


def _run_validate_open_log_registry(registry: Path, out: Path) -> dict:
    payload = validate_open_source_log_registry(registry)
    write_json(out, payload)
    write_audit_record(
        out_dir=out.parent,
        skill_name="open-source-log-registry-validation",
        skill_version="2.3.0",
        input_refs=[str(registry)],
        output_refs=[str(out)],
        tools_called=["validate_open_source_log_registry"],
        rules_triggered=["SOURCE_COMMIT_PIN", "SOURCE_LICENSE", "SOURCE_SHA256", "SOURCE_SIZE"],
        human_review_required=True,
        status="success",
        metadata={
            "source_count": payload["source_count"],
            "all_real_world_flight_verified": payload["all_real_world_flight_verified"],
            "safety_boundary": "explicit-download-offline-analysis",
        },
    )
    return payload


def _run_open_log_case_studies(registry: Path, cache_dir: Path, drone_id: str, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    output_path = out / "open_log_case_study.json"
    report_path = out / "open_log_case_study.md"
    payload = run_open_source_log_case_study(registry, cache_dir, drone_id)
    write_json(output_path, payload)
    report_path.write_text(render_open_source_log_case_study(payload), encoding="utf-8")
    write_audit_record(
        out_dir=out,
        skill_name="open-source-log-case-study",
        skill_version="2.3.0",
        input_refs=[str(registry), str(cache_dir)],
        output_refs=[str(output_path), str(report_path)],
        tools_called=["run_open_source_log_case_study"],
        rules_triggered=["CACHE_SHA256", "PARSER_COMPATIBILITY", "PROVENANCE_DISCLOSURE"],
        human_review_required=True,
        status="success" if payload["status"] == "PASS" else "failed",
        metadata={
            "case_count": payload["case_count"],
            "passed_count": payload["passed_count"],
            "safety_boundary": "offline-open-log-analysis-only",
        },
    )
    return payload


def _run_validate_datasets(registry: Path, out: Path) -> dict:
    result = validate_dataset_registry(registry)
    write_json(out, result)
    write_audit_record(
        out_dir=out.parent,
        skill_name="dataset-registry-validation",
        skill_version="1.6.0",
        input_refs=[str(registry)],
        output_refs=[str(out)],
        tools_called=["validate_dataset_registry"],
        rules_triggered=[finding["code"] for finding in result["findings"]],
        human_review_required=True,
        status="success",
        metadata={
            "validation_status": result["status"],
            "case_count": result["counts"]["cases"],
            "safety_boundary": "offline-dataset-registry-only",
        },
    )
    return result


def _run_validate_adapters(registry: Path, out: Path) -> dict:
    result = validate_adapter_registry(registry)
    write_json(out, result)
    write_audit_record(
        out_dir=out.parent,
        skill_name="offline-adapter-validation",
        skill_version="1.7.0",
        input_refs=[str(registry)],
        output_refs=[str(out)],
        tools_called=["validate_adapter_registry"],
        rules_triggered=[finding["code"] for finding in result["findings"]],
        human_review_required=True,
        status="success",
        metadata={
            "validation_status": result["status"],
            "adapter_count": result["counts"]["adapters"],
            "safety_boundary": "offline-adapter-registry-only",
        },
    )
    return result


def _run_validate_approvals(packet: Path, out: Path) -> dict:
    result = validate_approval_packet(packet)
    write_json(out, result)
    write_audit_record(
        out_dir=out.parent,
        skill_name="approval-workflow-validation",
        skill_version="1.7.0",
        input_refs=[str(packet)],
        output_refs=[str(out)],
        tools_called=["validate_approval_packet"],
        rules_triggered=[finding["code"] for finding in result["findings"]],
        human_review_required=True,
        status="success",
        metadata={
            "validation_status": result["status"],
            "approval_count": result["counts"]["approvals"],
            "safety_boundary": "offline-approval-workflow-only",
        },
    )
    return result


def _run_validate_handoff_package(package: Path, out: Path) -> dict:
    result = validate_handoff_package(package)
    write_json(out, result)
    write_audit_record(
        out_dir=out.parent,
        skill_name="organization-handoff-validation",
        skill_version="1.8.0",
        input_refs=[str(package)],
        output_refs=[str(out)],
        tools_called=["validate_handoff_package"],
        rules_triggered=[finding["code"] for finding in result["findings"]],
        human_review_required=True,
        status="success",
        metadata={
            "validation_status": result["status"],
            "artifact_count": result["counts"]["artifacts"],
            "safety_boundary": "offline-organization-handoff-only",
        },
    )
    return result


def _run_validate_platform_index(index: Path, out: Path) -> dict:
    result = validate_platform_index(index)
    write_json(out, result)
    write_audit_record(
        out_dir=out.parent,
        skill_name="platform-readiness-index-validation",
        skill_version="1.9.0",
        input_refs=[str(index)],
        output_refs=[str(out)],
        tools_called=["validate_platform_index"],
        rules_triggered=[finding["code"] for finding in result["findings"]],
        human_review_required=True,
        status="success" if result["status"] == "PASS" else "review_required",
        metadata={
            "validation_status": result["status"],
            "capability_count": result["counts"]["capabilities"],
            "safety_boundary": "offline-platform-readiness-index-only",
        },
    )
    return result


def _run_validate_operations_platform(baseline: Path, out: Path) -> dict:
    result = validate_operations_platform(baseline)
    write_json(out, result)
    write_audit_record(
        out_dir=out.parent,
        skill_name="operations-platform-validation",
        skill_version="2.0.0",
        input_refs=[str(baseline)],
        output_refs=[str(out)],
        tools_called=["validate_operations_platform"],
        rules_triggered=[finding["code"] for finding in result["findings"]],
        human_review_required=True,
        status="success" if result["status"] == "PASS" else "review_required",
        metadata={
            "validation_status": result["status"],
            "module_count": result["counts"]["modules"],
            "safety_boundary": "offline-operations-platform-baseline-only",
        },
    )
    return result


if __name__ == "__main__":
    app()

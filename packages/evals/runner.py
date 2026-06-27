from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import (
    EvalCase,
    EvalResult,
    EvalStatus,
    load_model,
    read_json_file,
    write_json,
)


CREATED_AT = "1970-01-01T00:00:00Z"
SKILL_NAME = "diagnosis-report-evaluation"
SKILL_VERSION = "1.4.0"


def run_eval_case(case_path: Path) -> EvalResult:
    case = load_model(case_path, EvalCase)
    base_dir = case_path.parent
    findings: list[dict[str, Any]] = []
    metric_results: list[dict[str, Any]] = []

    diagnosis = _read_json_list(_resolve_input(case, "diagnosis", base_dir), "diagnosis", findings)
    maintenance = _read_json_list(_resolve_input(case, "maintenance", base_dir), "maintenance", findings)
    report = _read_text(_resolve_input(case, "report", base_dir), "report", findings)

    observed_diagnosis_ids = {str(item.get("fault_id", "")) for item in diagnosis}
    observed_recommendation_ids = {str(item.get("recommendation_id", "")) for item in maintenance}
    report_text = report or ""
    observed_evidence_refs = _collect_observed_evidence_refs(diagnosis, maintenance, report_text)

    for metric in case.metrics:
        checks = _metric_checks(
            metric.metric_id,
            case,
            observed_diagnosis_ids,
            observed_recommendation_ids,
            observed_evidence_refs,
            report_text,
        )
        score = 1.0 if not checks else 0.0
        status = _metric_status(score, metric.pass_threshold, metric.review_threshold)
        metric_findings = [
            {
                "metric_id": metric.metric_id,
                "code": code,
                "severity": "HIGH" if status == EvalStatus.FAIL else "MEDIUM",
                "message": message,
            }
            for code, message in checks
        ]
        findings.extend(metric_findings)
        metric_results.append(
            {
                "metric_id": metric.metric_id,
                "status": status.value,
                "score": score,
                "evidence_refs": sorted(ref for ref in metric.required_evidence_refs if ref in observed_evidence_refs),
                "message": "PASS" if status == EvalStatus.PASS else "; ".join(message for _, message in checks),
            }
        )

    if any(finding["code"] == "INPUT_UNREADABLE" for finding in findings):
        suite_status = EvalStatus.INVALID_INPUT
    elif any(item["status"] == EvalStatus.FAIL.value for item in metric_results):
        suite_status = EvalStatus.FAIL
    elif any(item["status"] == EvalStatus.REVIEW_REQUIRED.value for item in metric_results):
        suite_status = EvalStatus.REVIEW_REQUIRED
    else:
        suite_status = EvalStatus.PASS

    score = _weighted_score(case, metric_results)
    return EvalResult(
        id=f"EVAL-{case.case_id}",
        timestamp=CREATED_AT,
        drone_id=case.drone_id,
        case_id=case.case_id,
        status=suite_status,
        score=score,
        metric_results=metric_results,
        findings=findings,
        output_refs=[],
        human_review_required=True,
    )


def run_eval_suite(case_paths: list[Path], output_path: Path | None = None, report_path: Path | None = None) -> dict[str, Any]:
    results = [run_eval_case(path) for path in sorted(case_paths, key=lambda item: str(item))]
    status = _suite_status([result.status for result in results])
    score = round(sum(result.score for result in results) / len(results), 4) if results else 0.0
    payload = {
        "schema_version": 1,
        "created_at": CREATED_AT,
        "status": status.value,
        "score": score,
        "case_count": len(results),
        "results": [result.model_dump(mode="json") for result in results],
        "safety_boundary": {
            "offline_only": True,
            "advisory_only": True,
            "human_review_required": True,
            "no_external_model_call": True,
            "no_real_drone_connection": True,
            "no_mavlink_command_execution": True,
        },
        "human_review_required": True,
    }
    if output_path is not None:
        for result in payload["results"]:
            result["output_refs"] = [str(output_path)]
        write_json(output_path, payload)
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_eval_report(payload), encoding="utf-8")
    return payload


def render_eval_report(payload: dict[str, Any]) -> str:
    lines = [
        "# v1.4.0 诊断与报告评估结果",
        "",
        f"- 状态：`{payload['status']}`",
        f"- 平均分：`{payload['score']}`",
        f"- 用例数：`{payload['case_count']}`",
        "- 人工复核：`true`",
        "",
        "## 评估用例",
    ]
    for result in payload["results"]:
        lines.extend(
            [
                f"### {result['case_id']}",
                f"- 状态：`{result['status']}`",
                f"- 分数：`{result['score']}`",
                f"- findings：`{len(result['findings'])}`",
                "",
            ]
        )
        for metric in result["metric_results"]:
            lines.append(
                f"- `{metric['metric_id']}` status=`{metric['status']}` score=`{metric['score']}`"
            )
        lines.append("")
    lines.extend(
        [
            "## 安全边界",
            "",
            "- 本评估只读取本地 JSON / Markdown 文件。",
            "- 不调用外部模型，不连接真实无人机或飞控。",
            "- 不执行 MAVLink command，不启动 PX4 / ArduPilot / Gazebo / SITL。",
            "- 输出仅用于 advisory quality gate，所有结论默认需要人工复核。",
            "",
        ]
    )
    return "\n".join(lines)


def _resolve_input(case: EvalCase, key: str, base_dir: Path) -> Path:
    if key not in case.input_refs:
        raise ValueError(f"Eval case {case.case_id} missing input ref: {key}")
    path = Path(case.input_refs[key])
    if path.is_absolute() or path.exists():
        return path
    return base_dir / path


def _read_json_list(path: Path, label: str, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        payload = read_json_file(path)
    except (FileNotFoundError, ValueError) as exc:
        findings.append({"metric_id": "input", "code": "INPUT_UNREADABLE", "message": f"{label}: {exc}"})
        return []
    if not isinstance(payload, list):
        findings.append({"metric_id": "input", "code": "INPUT_UNREADABLE", "message": f"{label} must be a JSON list"})
        return []
    return [item for item in payload if isinstance(item, dict)]


def _read_text(path: Path, label: str, findings: list[dict[str, Any]]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        findings.append({"metric_id": "input", "code": "INPUT_UNREADABLE", "message": f"{label}: {exc}"})
    return None


def _collect_observed_evidence_refs(
    diagnosis: list[dict[str, Any]],
    maintenance: list[dict[str, Any]],
    report_text: str,
) -> set[str]:
    refs: set[str] = set()
    for item in diagnosis:
        item_id = str(item.get("fault_id", item.get("id", "")))
        for ref in item.get("evidence_refs", []):
            if isinstance(ref, dict) and ref.get("rule_id") and item_id:
                refs.add(f"{ref['rule_id']}@diagnosis.json#{item_id}")
    for item in maintenance:
        item_id = str(item.get("recommendation_id", item.get("id", "")))
        for ref in item.get("evidence_refs", []):
            if isinstance(ref, dict) and ref.get("rule_id") and item_id:
                refs.add(f"{ref['rule_id']}@maintenance_recommendations.json#{item_id}")
    for line in report_text.splitlines():
        if "BATTERY_LOW_SOC" in line:
            refs.add("BATTERY_LOW_SOC@ops_report.md#Evidence")
        if "offline-only" in line.lower() or "advisory-only" in line.lower() or "离线" in line:
            refs.add("SAFETY_BOUNDARY@ops_report.md#Safety")
    return refs


def _metric_checks(
    metric_id: str,
    case: EvalCase,
    observed_diagnosis_ids: set[str],
    observed_recommendation_ids: set[str],
    observed_evidence_refs: set[str],
    report_text: str,
) -> list[tuple[str, str]]:
    checks: list[tuple[str, str]] = []
    if metric_id == "diagnosis_hypothesis_quality":
        missing = sorted(set(case.expected_output.required_diagnosis_ids) - observed_diagnosis_ids)
        checks.extend(("MISSING_DIAGNOSIS", f"Missing diagnosis id: {item}") for item in missing)
    elif metric_id == "maintenance_recommendation_coverage":
        missing = sorted(set(case.expected_output.required_recommendation_ids) - observed_recommendation_ids)
        checks.extend(("MISSING_RECOMMENDATION", f"Missing recommendation id: {item}") for item in missing)
    elif metric_id == "report_section_completeness":
        missing = [section for section in case.expected_output.required_report_sections if section not in report_text]
        checks.extend(("MISSING_REPORT_SECTION", f"Missing report section: {item}") for item in missing)
    elif metric_id == "safety_boundary_correctness":
        lowered = report_text.lower()
        if "offline-only" not in lowered and "离线" not in report_text:
            checks.append(("MISSING_SAFETY_BOUNDARY", "Report must state offline-only or 离线 boundary."))
        if "advisory-only" not in lowered and "人工复核" not in report_text:
            checks.append(("MISSING_SAFETY_BOUNDARY", "Report must state advisory-only or 人工复核 boundary."))
    elif metric_id == "evidence_completeness":
        missing = sorted(set(case.expected_output.required_evidence_refs) - observed_evidence_refs)
        checks.extend(("MISSING_EVIDENCE_REF", f"Missing evidence ref: {item}") for item in missing)

    metric = next(item for item in case.metrics if item.metric_id == metric_id)
    missing_metric_refs = sorted(set(metric.required_evidence_refs) - observed_evidence_refs)
    for ref in missing_metric_refs:
        if not any(ref in message for _, message in checks):
            checks.append(("MISSING_EVIDENCE_REF", f"Missing metric evidence ref: {ref}"))
    return checks


def _metric_status(score: float, pass_threshold: float, review_threshold: float) -> EvalStatus:
    if score >= pass_threshold:
        return EvalStatus.PASS
    if score >= review_threshold:
        return EvalStatus.REVIEW_REQUIRED
    return EvalStatus.FAIL


def _weighted_score(case: EvalCase, metric_results: list[dict[str, Any]]) -> float:
    scores = {item["metric_id"]: float(item["score"]) for item in metric_results}
    return round(sum(metric.weight * scores.get(metric.metric_id, 0.0) for metric in case.metrics), 4)


def _suite_status(statuses: list[EvalStatus]) -> EvalStatus:
    if not statuses:
        return EvalStatus.INVALID_INPUT
    if EvalStatus.INVALID_INPUT in statuses:
        return EvalStatus.INVALID_INPUT
    if EvalStatus.FAIL in statuses:
        return EvalStatus.FAIL
    if EvalStatus.REVIEW_REQUIRED in statuses:
        return EvalStatus.REVIEW_REQUIRED
    return EvalStatus.PASS

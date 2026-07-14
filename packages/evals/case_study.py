from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from packages.drone_schemas import EvalCase, load_model
from packages.evals.runner import run_eval_case
from packages.simulation import INVALID_INPUT, load_simulation_scenario_matrix, validate_simulation_result


CREATED_AT = "1970-01-01T00:00:00Z"


def run_case_study(simulation_matrix_path: Path, eval_case_paths: list[Path]) -> dict[str, Any]:
    simulation_cases = _run_simulation_cases(simulation_matrix_path)
    diagnosis_cases = _run_diagnosis_report_cases(eval_case_paths)
    all_cases = [*simulation_cases, *diagnosis_cases]

    matched_count = sum(1 for case in all_cases if case["matched_expected"])
    total_evidence_checks = sum(case["evidence_check_count"] for case in all_cases)
    covered_evidence_checks = sum(case["evidence_covered_count"] for case in all_cases)
    evidence_coverage_rate = (
        round(covered_evidence_checks / total_evidence_checks, 4) if total_evidence_checks else 0.0
    )
    accuracy = round(matched_count / len(all_cases), 4) if all_cases else 0.0
    false_alarm_count = sum(
        1
        for case in simulation_cases
        if case["expected_result"] == "PASS" and case["actual_result"] != "PASS"
    )
    missed_risk_count = sum(
        1
        for case in simulation_cases
        if case["expected_result"] == "FAIL" and case["actual_result"] != "FAIL"
    )
    diagnosis_score = (
        round(sum(case["score"] for case in diagnosis_cases) / len(diagnosis_cases), 4)
        if diagnosis_cases
        else 0.0
    )

    status = "PASS"
    if accuracy < 1.0 or false_alarm_count or missed_risk_count:
        status = "FAIL"
    elif evidence_coverage_rate < 1.0:
        status = "REVIEW_REQUIRED"

    payload: dict[str, Any] = {
        "schema_version": 1,
        "created_at": CREATED_AT,
        "status": status,
        "case_count": len(all_cases),
        "simulation": {
            "matrix_ref": simulation_matrix_path.as_posix(),
            "case_count": len(simulation_cases),
            "status_counts": dict(sorted(Counter(case["actual_result"] for case in simulation_cases).items())),
            "cases": simulation_cases,
        },
        "diagnosis_report": {
            "case_count": len(diagnosis_cases),
            "cases": diagnosis_cases,
        },
        "metrics": {
            "diagnosis_report_average_score": diagnosis_score,
            "evidence_coverage_rate": evidence_coverage_rate,
            "expected_status_accuracy": accuracy,
            "false_alarm_count": false_alarm_count,
            "missed_risk_count": missed_risk_count,
        },
        "safety_boundary": {
            "offline_only": True,
            "advisory_only": True,
            "human_review_required": True,
            "no_external_model_call": True,
            "no_real_drone_connection": True,
            "no_mavlink_command_execution": True,
            "no_simulator_launch": True,
        },
        "human_review_required": True,
    }
    payload["result_digest"] = _digest(payload)
    return payload


def render_case_study_report(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    lines = [
        "# v2.2.0 离线评测与案例研究",
        "",
        "## 执行摘要",
        "",
        f"- 总体状态：`{payload['status']}`",
        f"- 案例数：`{payload['case_count']}`",
        f"- 预期状态准确率：`{metrics['expected_status_accuracy']:.2%}`",
        f"- 证据覆盖率：`{metrics['evidence_coverage_rate']:.2%}`",
        f"- 误报数：`{metrics['false_alarm_count']}`",
        f"- 漏检数：`{metrics['missed_risk_count']}`",
        f"- 诊断/报告平均分：`{metrics['diagnosis_report_average_score']}`",
        f"- 结果摘要：`{payload['result_digest']}`",
        "- 人工复核：`true`",
        "",
        "## 仿真场景矩阵",
        "",
        "| 场景 | 预期 | 实际 | 匹配 | 规则数 | 证据引用数 |",
        "|---|---|---|---:|---:|---:|",
    ]
    for case in payload["simulation"]["cases"]:
        lines.append(
            f"| `{case['case_id']}` | `{case['expected_result']}` | `{case['actual_result']}` | "
            f"{'是' if case['matched_expected'] else '否'} | {case['rule_count']} | {case['evidence_ref_count']} |"
        )

    lines.extend(["", "## 诊断与报告评测", ""])
    for case in payload["diagnosis_report"]["cases"]:
        lines.extend(
            [
                f"### `{case['case_id']}`",
                f"- 预期：`{case['expected_result']}`",
                f"- 实际：`{case['actual_result']}`",
                f"- 分数：`{case['score']}`",
                f"- 匹配预期：`{str(case['matched_expected']).lower()}`",
                "",
            ]
        )

    lines.extend(
        [
            "## 结论边界",
            "",
            "- 本案例研究只读取仓库内 sample / mock / sanitized 文件并调用现有确定性规则。",
            "- 不调用外部模型，不连接真实无人机、飞控、维修系统或 fleet platform。",
            "- 不执行 MAVLink command，不启动 PX4、ArduPilot、Gazebo 或 SITL。",
            "- PASS 仅表示当前离线输出符合预期，所有结论仍需人工复核。",
            "",
        ]
    )
    return "\n".join(lines)


def _run_simulation_cases(matrix_path: Path) -> list[dict[str, Any]]:
    matrix = load_simulation_scenario_matrix(matrix_path)
    results: list[dict[str, Any]] = []
    for case in sorted(matrix.cases, key=lambda item: item.case_id):
        actual_result = INVALID_INPUT
        error: str | None = None
        rule_results: list[dict[str, Any]] = []
        evidence_ref_count = 0
        try:
            scenario, simulation_result = case.validate_payloads()
            run = validate_simulation_result(
                scenario,
                simulation_result,
                scenario_path=matrix_path,
                result_path=matrix_path,
            )
            actual_result = str(run.status)
            evidence_ref_count = len(run.evidence_refs)
            rule_results = [
                {
                    "rule_id": item.rule_id,
                    "status": str(item.status),
                    "field": item.field,
                    "evidence_ref_count": len(item.evidence_refs),
                }
                for item in run.rule_results
            ]
        except ValueError as exc:
            error = str(exc)

        expected_error_matched = (
            case.expected_error_contains is None
            or (error is not None and case.expected_error_contains in error)
        )

        results.append(
            {
                "case_id": case.case_id,
                "description": case.description,
                "expected_result": case.expected_result,
                "actual_result": actual_result,
                "matched_expected": actual_result == case.expected_result and expected_error_matched,
                "expected_error_matched": expected_error_matched,
                "rule_count": len(rule_results),
                "evidence_ref_count": evidence_ref_count,
                "evidence_check_count": len(rule_results),
                "evidence_covered_count": sum(1 for item in rule_results if item["evidence_ref_count"] > 0),
                "triggered_rule_ids": sorted(
                    item["rule_id"] for item in rule_results if item["status"] != "PASS"
                ),
                "rule_results": rule_results,
                "error": error,
                "human_review_required": True,
            }
        )
    return results


def _run_diagnosis_report_cases(case_paths: list[Path]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted(case_paths, key=lambda item: item.as_posix()):
        case = load_model(path, EvalCase)
        result = run_eval_case(path)
        metric_results = result.metric_results
        actual_result = result.status.value
        expected_result = case.expected_output.expected_status.value
        results.append(
            {
                "case_id": case.case_id,
                "case_ref": path.as_posix(),
                "expected_result": expected_result,
                "actual_result": actual_result,
                "matched_expected": actual_result == expected_result,
                "score": result.score,
                "finding_count": len(result.findings),
                "evidence_check_count": len(metric_results),
                "evidence_covered_count": sum(1 for item in metric_results if item.get("evidence_refs")),
                "human_review_required": True,
            }
        )
    return results


def _digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

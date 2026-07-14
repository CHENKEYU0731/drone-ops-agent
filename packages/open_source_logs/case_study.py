from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from packages.log_parsers import parse_flight_log_details
from packages.open_source_logs.registry import load_open_source_log_registry, verify_cached_source
from packages.telemetry_rules import summarize_flight


CREATED_AT = "1970-01-01T00:00:00Z"


def run_open_source_log_case_study(registry_path: Path, cache_dir: Path, drone_id: str) -> dict[str, Any]:
    registry = load_open_source_log_registry(registry_path)
    cases = []
    for source in registry.sources:
        log_path = verify_cached_source(source, cache_dir)
        parsed = parse_flight_log_details(log_path, requested_format=source.format)
        summary = summarize_flight(parsed.records, drone_id, source.source_id)
        cases.append(
            {
                "source_id": source.source_id,
                "status": "PASS",
                "format": source.format,
                "parser_name": parsed.parser_name,
                "parser_version": parsed.parser_version,
                "record_count": len(parsed.records),
                "duration_seconds": summary.duration_seconds,
                "min_battery_voltage_v": summary.min_battery_voltage_v,
                "min_battery_soc_pct": summary.min_battery_soc_pct,
                "min_gps_satellites": summary.gps_summary["min_satellites"],
                "max_motor_output_spread": summary.motor_imbalance_summary["max_spread"],
                "warning_count": len(parsed.warnings),
                "warnings": sorted(parsed.warnings),
                "license_spdx": source.license_spdx,
                "provenance_class": source.provenance_class,
                "real_world_flight_verified": source.real_world_flight_verified,
                "sha256": source.sha256,
                "human_review_required": True,
            }
        )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "created_at": CREATED_AT,
        "registry_id": registry.registry_id,
        "status": "PASS" if cases and all(case["status"] == "PASS" for case in cases) else "FAIL",
        "case_count": len(cases),
        "passed_count": sum(1 for case in cases if case["status"] == "PASS"),
        "cases": cases,
        "limitations": [
            "上游 fixture 元数据不足以证明日志来自真实外场飞行。",
            "飞控启动相对时间被映射到 Unix epoch，不代表真实 UTC 时间。",
            "前四路 actuator 输出仅为兼容性假设，未证明一定对应四个电机。",
            "兼容性通过率不是真实场景异常检测准确率。",
        ],
        "safety_boundary": {
            "offline_analysis_only": True,
            "no_real_drone_connection": True,
            "no_mavlink_command_execution": True,
            "human_review_required": True,
        },
        "human_review_required": True,
    }
    payload["result_digest"] = _digest(payload)
    return payload


def render_open_source_log_case_study(payload: dict[str, Any]) -> str:
    lines = [
        "# v2.3.0 开源上游日志兼容性案例研究",
        "",
        f"- 状态：`{payload['status']}`",
        f"- 案例数：`{payload['case_count']}`",
        f"- 解析通过：`{payload['passed_count']}`",
        f"- 结果摘要：`{payload['result_digest']}`",
        "- 人工复核：`true`",
        "",
        "| 来源 | Parser | 记录数 | 时长(秒) | 最低电量 | Warning | 真实外场已验证 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for case in payload["cases"]:
        lines.append(
            f"| `{case['source_id']}` | `{case['parser_name']} {case['parser_version']}` | "
            f"{case['record_count']} | {case['duration_seconds']} | {case['min_battery_soc_pct']}% | "
            f"{case['warning_count']} | {'是' if case['real_world_flight_verified'] else '否'} |"
        )
    lines.extend(["", "## 限制", ""])
    lines.extend(f"- {item}" for item in payload["limitations"])
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 下载与分析分离；案例研究命令本身不联网。",
            "- 不连接真实无人机、飞控或外部平台，不执行 MAVLink command。",
            "- 所有输出仅用于公开上游日志兼容性验证和人工复核。",
            "",
        ]
    )
    return "\n".join(lines)


def _digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

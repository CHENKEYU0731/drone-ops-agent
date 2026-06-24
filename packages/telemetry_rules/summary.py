from __future__ import annotations

from math import sqrt

from packages.drone_schemas import EvidenceRef, FlightLogRecord, FlightLogSummary


SKILL_NAME = "flight-log-analysis"
SKILL_VERSION = "1.0.0"


def summarize_flight(
    records: list[FlightLogRecord],
    drone_id: str,
    source_log_id: str,
    anomaly_count: int = 0,
) -> FlightLogSummary:
    if not records:
        raise ValueError("无法汇总空飞行日志。")
    ordered = sorted(records, key=lambda item: item.timestamp)
    start = ordered[0].timestamp
    end = ordered[-1].timestamp
    magnitudes = [_vibration_magnitude(item) for item in ordered]
    motor_spreads = [_motor_spread(item) for item in ordered]

    return FlightLogSummary(
        drone_id=drone_id,
        generated_by_skill=SKILL_NAME,
        skill_version=SKILL_VERSION,
        source_log_id=source_log_id,
        start_time=start,
        end_time=end,
        duration_seconds=int((end - start).total_seconds()),
        record_count=len(ordered),
        min_battery_voltage_v=round(min(item.battery_voltage_v for item in ordered), 2),
        max_battery_current_a=round(max(item.battery_current_a for item in ordered), 2),
        min_battery_soc_pct=round(min(item.battery_soc_pct for item in ordered), 2),
        gps_summary={
            "min_satellites": min(item.gps_satellites for item in ordered),
            "max_hdop": round(max(item.gps_hdop for item in ordered), 2),
            "average_hdop": round(sum(item.gps_hdop for item in ordered) / len(ordered), 2),
        },
        vibration_summary={
            "max_magnitude": round(max(magnitudes), 3),
            "average_magnitude": round(sum(magnitudes) / len(magnitudes), 3),
        },
        motor_imbalance_summary={
            "max_spread": round(max(motor_spreads), 2),
            "average_spread": round(sum(motor_spreads) / len(motor_spreads), 2),
        },
        link_quality_summary={
            "min_link_quality_pct": round(min(item.link_quality_pct for item in ordered), 2),
            "average_link_quality_pct": round(
                sum(item.link_quality_pct for item in ordered) / len(ordered),
                2,
            ),
        },
        flight_mode_timeline=_mode_timeline(ordered),
        anomaly_count=anomaly_count,
        evidence_refs=[
            EvidenceRef(
                source_type="log",
                source_id=source_log_id,
                timestamp=start,
                field="record_count",
                measured_value=len(ordered),
                threshold=">0",
                rule_id="SUMMARY_INPUT",
                description="飞行摘要基于该日志的全部记录生成。",
            )
        ],
    )


def _vibration_magnitude(record: FlightLogRecord) -> float:
    return sqrt(record.vibration_x**2 + record.vibration_y**2 + record.vibration_z**2)


def _motor_spread(record: FlightLogRecord) -> float:
    outputs = [
        record.motor_1_output,
        record.motor_2_output,
        record.motor_3_output,
        record.motor_4_output,
    ]
    return max(outputs) - min(outputs)


def _mode_timeline(records: list[FlightLogRecord]) -> list[dict[str, str]]:
    timeline: list[dict[str, str]] = []
    previous_mode: str | None = None
    for record in records:
        if record.flight_mode != previous_mode:
            timeline.append(
                {
                    "timestamp": record.timestamp.isoformat(),
                    "flight_mode": record.flight_mode,
                }
            )
            previous_mode = record.flight_mode
    return timeline

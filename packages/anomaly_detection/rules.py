from __future__ import annotations

from math import sqrt

from packages.drone_schemas import AnomalyEvent, EvidenceRef, FlightLogRecord, Severity


SKILL_NAME = "flight-log-analysis"
SKILL_VERSION = "1.0.0"

EXPECTED_MODES = {"STABILIZE", "AUTO", "LAND"}


def detect_anomalies(
    records: list[FlightLogRecord],
    drone_id: str,
    source_log_id: str,
) -> list[AnomalyEvent]:
    anomalies: list[AnomalyEvent] = []
    ordered = sorted(records, key=lambda item: item.timestamp)
    previous: FlightLogRecord | None = None
    sequence = 1
    for record in ordered:
        checks = [
            _battery_voltage_drop(previous, record, source_log_id),
            _threshold(
                record,
                source_log_id,
                "LOW_BATTERY_SOC",
                "battery_soc_pct",
                record.battery_soc_pct,
                25,
                record.battery_soc_pct < 25,
                Severity.HIGH,
                "电池 SOC 低于安全阈值。",
            ),
            _threshold(
                record,
                source_log_id,
                "HIGH_CURRENT",
                "battery_current_a",
                record.battery_current_a,
                35,
                record.battery_current_a > 35,
                Severity.HIGH,
                "电池电流超过常规运维阈值。",
            ),
            _threshold(
                record,
                source_log_id,
                "GPS_QUALITY_DEGRADED",
                "gps_satellites",
                record.gps_satellites,
                8,
                record.gps_satellites < 8 or record.gps_hdop > 2.0,
                Severity.MEDIUM,
                "GPS 质量下降，卫星数或 HDOP 表现异常。",
            ),
            _threshold(
                record,
                source_log_id,
                "HIGH_HDOP",
                "gps_hdop",
                record.gps_hdop,
                2.0,
                record.gps_hdop > 2.0,
                Severity.MEDIUM,
                "HDOP 高于阈值，定位精度下降。",
            ),
            _threshold(
                record,
                source_log_id,
                "LOW_GPS_SATELLITES",
                "gps_satellites",
                record.gps_satellites,
                8,
                record.gps_satellites < 8,
                Severity.MEDIUM,
                "GPS 卫星数低于阈值。",
            ),
            _threshold(
                record,
                source_log_id,
                "HIGH_VIBRATION",
                "vibration_magnitude",
                _vibration_magnitude(record),
                2.5,
                _vibration_magnitude(record) > 2.5,
                Severity.HIGH,
                "振动幅值超过阈值。",
            ),
            _threshold(
                record,
                source_log_id,
                "MOTOR_OUTPUT_IMBALANCE",
                "motor_output_spread",
                _motor_spread(record),
                20,
                _motor_spread(record) > 20,
                Severity.HIGH,
                "四个电机输出差异过大。",
            ),
            _threshold(
                record,
                source_log_id,
                "LOW_LINK_QUALITY",
                "link_quality_pct",
                record.link_quality_pct,
                70,
                record.link_quality_pct < 70,
                Severity.HIGH,
                "通信链路质量低于阈值。",
            ),
            _threshold(
                record,
                source_log_id,
                "HIGH_TEMPERATURE",
                "temperature_c",
                record.temperature_c,
                60,
                record.temperature_c > 60,
                Severity.HIGH,
                "温度超过运维阈值。",
            ),
            _unexpected_mode(record, source_log_id),
        ]
        for anomaly in [item for item in checks if item is not None]:
            anomaly.anomaly_id = f"ANOM-{sequence:03d}"
            anomaly.drone_id = drone_id
            anomalies.append(anomaly)
            sequence += 1
        previous = record
    return sorted(anomalies, key=lambda item: (item.timestamp, item.anomaly_id))


def _battery_voltage_drop(
    previous: FlightLogRecord | None,
    record: FlightLogRecord,
    source_log_id: str,
) -> AnomalyEvent | None:
    if previous is None:
        return None
    drop = round(previous.battery_voltage_v - record.battery_voltage_v, 2)
    if drop < 0.8:
        return None
    return _make_event(
        record,
        source_log_id,
        "BATTERY_VOLTAGE_DROP",
        Severity.HIGH,
        "battery_voltage_v",
        drop,
        0.8,
        f"电池电压在相邻采样间下降 {drop}V。",
    )


def _unexpected_mode(record: FlightLogRecord, source_log_id: str) -> AnomalyEvent | None:
    if record.flight_mode in EXPECTED_MODES:
        return None
    return _make_event(
        record,
        source_log_id,
        "UNEXPECTED_FLIGHT_MODE",
        Severity.HIGH if record.flight_mode == "FAILSAFE" else Severity.MEDIUM,
        "flight_mode",
        record.flight_mode,
        ",".join(sorted(EXPECTED_MODES)),
        f"检测到非预期飞行模式 {record.flight_mode}。",
    )


def _threshold(
    record: FlightLogRecord,
    source_log_id: str,
    rule_id: str,
    field: str,
    measured_value: float | int | str,
    threshold: float | int | str,
    triggered: bool,
    severity: Severity,
    summary: str,
) -> AnomalyEvent | None:
    if not triggered:
        return None
    return _make_event(
        record,
        source_log_id,
        rule_id,
        severity,
        field,
        round(measured_value, 3) if isinstance(measured_value, float) else measured_value,
        threshold,
        summary,
    )


def _make_event(
    record: FlightLogRecord,
    source_log_id: str,
    rule_id: str,
    severity: Severity,
    field: str,
    measured_value: float | int | str,
    threshold: float | int | str,
    summary: str,
) -> AnomalyEvent:
    evidence = EvidenceRef(
        source_type="log",
        source_id=f"{source_log_id}:{record.timestamp.isoformat()}",
        timestamp=record.timestamp,
        field=field,
        measured_value=measured_value,
        threshold=threshold,
        rule_id=rule_id,
        description=summary,
    )
    return AnomalyEvent(
        anomaly_id="ANOM-000",
        type=rule_id,
        severity=severity,
        timestamp=record.timestamp,
        evidence_refs=[evidence],
        human_readable_summary=summary,
        rule_id=rule_id,
        measured_value=measured_value,
        threshold=threshold,
        generated_by_skill=SKILL_NAME,
        skill_version=SKILL_VERSION,
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

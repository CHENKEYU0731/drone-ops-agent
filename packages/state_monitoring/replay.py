from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from packages.drone_schemas import (
    DroneAsset,
    EvidenceRef,
    MonitoringEvent,
    MonitoringSummary,
    Severity,
    TelemetrySnapshot,
    read_json_file,
)


SKILL_NAME = "state-monitoring"
SKILL_VERSION = "1.0.0"

REQUIRED_FIELDS = {
    "timestamp",
    "flight_mode",
    "altitude_m",
    "vertical_speed_mps",
    "ground_speed_mps",
    "battery_voltage_v",
    "battery_current_a",
    "battery_soc_pct",
    "gps_satellites",
    "gps_hdop",
    "vibration_x",
    "vibration_y",
    "vibration_z",
    "motor_1_output",
    "motor_2_output",
    "motor_3_output",
    "motor_4_output",
    "link_quality_pct",
    "temperature_c",
    "ekf_variance",
    "failsafe_active",
}

NUMERIC_FIELDS = REQUIRED_FIELDS - {"timestamp", "flight_mode", "failsafe_active"}
SEVERITY_ORDER = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


def load_monitoring_rules(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Input file does not exist: {path}") from exc
    try:
        data = _parse_simple_yaml(text)
    except ValueError as exc:
        raise ValueError(f"Invalid YAML rules file: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"YAML rules file must be an object: {path}")
    return data


def parse_telemetry_replay(path: Path, drone_id: str) -> list[TelemetrySnapshot]:
    if not path.exists():
        raise FileNotFoundError(f"Telemetry file does not exist: {path}")
    if path.suffix.lower() == ".csv":
        rows = _read_csv(path)
    elif path.suffix.lower() == ".json":
        rows = _read_json(path)
    else:
        raise ValueError(f"Unsupported telemetry format: {path.suffix}")
    if not rows:
        raise ValueError(f"Telemetry file is empty: {path}")
    records = [_snapshot_from_row(path, index, row, drone_id) for index, row in enumerate(rows, start=1)]
    return sorted(records, key=lambda record: record.timestamp)


def run_monitoring_replay(
    telemetry_path: Path,
    asset: DroneAsset,
    rules_path: Path,
) -> tuple[MonitoringSummary, list[MonitoringEvent]]:
    rules = load_monitoring_rules(rules_path)
    records = parse_telemetry_replay(telemetry_path, asset.drone_id)
    events: list[MonitoringEvent] = []
    previous: TelemetrySnapshot | None = None
    source_id = _path_ref(telemetry_path)

    for index, snapshot in enumerate(records, start=1):
        row_source_id = f"{source_id}:{index}"
        _check_numeric_rule(events, snapshot, rules, "low_battery_soc", "battery_soc_pct", lambda value, threshold: value < threshold, row_source_id)
        _check_numeric_rule(events, snapshot, rules, "battery_voltage_sag", "battery_voltage_v", lambda value, threshold: value < threshold, row_source_id)
        _check_numeric_rule(events, snapshot, rules, "high_current_draw", "battery_current_a", lambda value, threshold: value > threshold, row_source_id)
        _check_numeric_rule(events, snapshot, rules, "gps_degradation", "gps_satellites", lambda value, threshold: value < threshold, row_source_id)
        _check_numeric_rule(events, snapshot, rules, "high_hdop", "gps_hdop", lambda value, threshold: value > threshold, row_source_id)
        _check_numeric_rule(events, snapshot, rules, "low_satellite_count", "gps_satellites", lambda value, threshold: value < threshold, row_source_id)
        _check_vibration(events, snapshot, rules, row_source_id)
        _check_motor_imbalance(events, snapshot, rules, row_source_id)
        _check_numeric_rule(events, snapshot, rules, "communication_link_drop", "link_quality_pct", lambda value, threshold: value < threshold, row_source_id)
        _check_numeric_rule(events, snapshot, rules, "high_temperature", "temperature_c", lambda value, threshold: value > threshold, row_source_id)
        _check_numeric_rule(events, snapshot, rules, "ekf_variance_high", "ekf_variance", lambda value, threshold: value > threshold, row_source_id)
        _check_failsafe(events, snapshot, rules, row_source_id)
        _check_mode_transition(events, snapshot, previous, rules, row_source_id)
        previous = snapshot

    highest = _highest_severity(events)
    summary = MonitoringSummary(
        drone_id=asset.drone_id,
        source_refs=[_path_ref(telemetry_path), _path_ref(rules_path)],
        event_count=len(events),
        highest_severity=highest,
        monitored_duration_s=_duration_seconds(records),
        samples_processed=len(records),
        human_review_required=any(event.severity in {Severity.HIGH, Severity.CRITICAL} for event in events),
        generated_by_skill=SKILL_NAME,
        skill_version=SKILL_VERSION,
    )
    return summary, events


def _check_numeric_rule(
    events: list[MonitoringEvent],
    snapshot: TelemetrySnapshot,
    rules: dict[str, Any],
    rule_key: str,
    field: str,
    predicate: Callable[[float, float], bool],
    source_id: str,
) -> None:
    rule = _rule(rules, rule_key)
    if not rule:
        return
    threshold = _number(rule, "threshold")
    value = float(getattr(snapshot, field))
    if predicate(value, threshold):
        events.append(_event(snapshot, rule, field, value, threshold, source_id))


def _check_vibration(events: list[MonitoringEvent], snapshot: TelemetrySnapshot, rules: dict[str, Any], source_id: str) -> None:
    rule = _rule(rules, "high_vibration")
    if not rule:
        return
    threshold = _number(rule, "threshold")
    value = max(abs(snapshot.vibration_x), abs(snapshot.vibration_y), abs(snapshot.vibration_z))
    if value > threshold:
        events.append(_event(snapshot, rule, "vibration_peak", value, threshold, source_id))


def _check_motor_imbalance(events: list[MonitoringEvent], snapshot: TelemetrySnapshot, rules: dict[str, Any], source_id: str) -> None:
    rule = _rule(rules, "motor_output_imbalance")
    if not rule:
        return
    threshold = _number(rule, "threshold")
    outputs = [snapshot.motor_1_output, snapshot.motor_2_output, snapshot.motor_3_output, snapshot.motor_4_output]
    value = max(outputs) - min(outputs)
    if value > threshold:
        events.append(_event(snapshot, rule, "motor_output_spread", value, threshold, source_id))


def _check_failsafe(events: list[MonitoringEvent], snapshot: TelemetrySnapshot, rules: dict[str, Any], source_id: str) -> None:
    rule = _rule(rules, "failsafe_active")
    if rule and snapshot.failsafe_active:
        events.append(_event(snapshot, rule, "failsafe_active", "true", "false", source_id))


def _check_mode_transition(
    events: list[MonitoringEvent],
    snapshot: TelemetrySnapshot,
    previous: TelemetrySnapshot | None,
    rules: dict[str, Any],
    source_id: str,
) -> None:
    rule = _rule(rules, "unexpected_mode_transition")
    if not rule:
        return
    allowed_modes = {str(mode).upper() for mode in _list(rule, "allowed_modes")}
    allowed_transitions = {str(item).upper() for item in _list(rule, "allowed_transitions")}
    current_mode = snapshot.flight_mode.upper()
    if current_mode not in allowed_modes:
        events.append(_event(snapshot, rule, "flight_mode", snapshot.flight_mode, ",".join(sorted(allowed_modes)), source_id))
        return
    if previous is None:
        return
    transition = f"{previous.flight_mode.upper()}->{current_mode}"
    if previous.flight_mode.upper() != current_mode and transition not in allowed_transitions:
        events.append(_event(snapshot, rule, "flight_mode_transition", transition, ",".join(sorted(allowed_transitions)), source_id))


def _event(
    snapshot: TelemetrySnapshot,
    rule: dict[str, Any],
    field: str,
    measured_value: float | int | str,
    threshold: float | int | str,
    source_id: str,
) -> MonitoringEvent:
    severity = Severity(str(rule["severity"]).upper())
    rule_id = str(rule["rule_id"])
    event_type = str(rule["event_type"])
    message = str(rule["message"])
    ref = EvidenceRef(
        source_type="telemetry",
        source_id=source_id,
        timestamp=snapshot.timestamp,
        field=field,
        measured_value=measured_value,
        threshold=threshold,
        rule_id=rule_id,
        description=message,
    )
    return MonitoringEvent(
        drone_id=snapshot.drone_id,
        timestamp=snapshot.timestamp,
        event_type=event_type,
        severity=severity,
        message=message,
        measured_value=measured_value,
        threshold=threshold,
        rule_id=rule_id,
        evidence_refs=[ref],
        human_review_required=severity in {Severity.HIGH, Severity.CRITICAL},
        generated_by_skill=SKILL_NAME,
        skill_version=SKILL_VERSION,
    )


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV is missing a header: {path}")
        missing = REQUIRED_FIELDS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV is missing fields {sorted(missing)}: {path}")
        return [dict(row) for row in reader]


def _read_json(path: Path) -> list[dict[str, Any]]:
    data = read_json_file(path)
    if not isinstance(data, list):
        raise ValueError(f"JSON telemetry file must be a record list: {path}")
    for index, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"JSON record {index} is not an object: {path}")
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            raise ValueError(f"JSON record {index} is missing fields {sorted(missing)}: {path}")
    return data


def _snapshot_from_row(path: Path, index: int, row: dict[str, Any], drone_id: str) -> TelemetrySnapshot:
    converted = dict(row)
    converted["drone_id"] = drone_id
    for field in NUMERIC_FIELDS:
        try:
            if field == "gps_satellites":
                converted[field] = int(row[field])
            else:
                converted[field] = float(row[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path} row {index} field {field} is not a valid number") from exc
    converted["failsafe_active"] = _bool(row["failsafe_active"])
    try:
        return TelemetrySnapshot.model_validate(converted)
    except ValidationError as exc:
        raise ValueError(f"{path} row {index} field validation failed: {exc}") from exc


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    raise ValueError(f"failsafe_active is not a valid boolean value: {value}")


def _duration_seconds(records: list[TelemetrySnapshot]) -> int:
    if len(records) < 2:
        return 0
    return int((records[-1].timestamp - records[0].timestamp).total_seconds())


def _highest_severity(events: list[MonitoringEvent]) -> Severity:
    if not events:
        return Severity.INFO
    return max((event.severity for event in events), key=lambda severity: SEVERITY_ORDER[severity])


def _path_ref(path: Path) -> str:
    return path.as_posix()


def _rule(rules: dict[str, Any], key: str) -> dict[str, Any]:
    rule = rules.get(key, {})
    if not isinstance(rule, dict):
        raise ValueError(f"{key} must be an object")
    if not rule:
        return {}
    for required in ["event_type", "severity", "rule_id", "message"]:
        if required not in rule:
            raise ValueError(f"{key}.{required} is missing")
    return rule


def _number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    return float(value)


def _list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return [str(item) for item in value]


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            raise ValueError(f"Cannot parse line: {raw_line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"Invalid indentation: {raw_line}")
        parent = stack[-1][1]
        if raw_value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(raw_value)
    return root


def _parse_scalar(value: str) -> Any:
    value = value.split(" #", 1)[0].strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item.strip()) for item in inner.split(",")]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return value

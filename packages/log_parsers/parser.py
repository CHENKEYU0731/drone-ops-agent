from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from packages.drone_schemas import FlightLogRecord, read_json_file


REQUIRED_FIELDS = {
    "timestamp",
    "flight_mode",
    "altitude_m",
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
}


NUMERIC_FIELDS = REQUIRED_FIELDS - {"timestamp", "flight_mode"}


def parse_flight_log(path: Path) -> list[FlightLogRecord]:
    if not path.exists():
        raise FileNotFoundError(f"飞行日志不存在: {path}")
    if path.suffix.lower() == ".csv":
        rows = _read_csv(path)
    elif path.suffix.lower() == ".json":
        rows = _read_json(path)
    else:
        raise ValueError(f"不支持的日志格式: {path.suffix}")
    if not rows:
        raise ValueError(f"飞行日志为空: {path}")
    return [_record_from_row(path, index, row) for index, row in enumerate(rows, start=1)]


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV 缺少表头: {path}")
        missing = REQUIRED_FIELDS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV 缺少字段 {sorted(missing)}: {path}")
        return [dict(row) for row in reader]


def _read_json(path: Path) -> list[dict[str, Any]]:
    data = read_json_file(path)
    if not isinstance(data, list):
        raise ValueError(f"JSON 飞行日志必须是记录列表: {path}")
    for index, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"JSON 第 {index} 条记录不是对象: {path}")
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            raise ValueError(f"JSON 第 {index} 条记录缺少字段 {sorted(missing)}: {path}")
    return data


def _record_from_row(path: Path, index: int, row: dict[str, Any]) -> FlightLogRecord:
    converted = dict(row)
    for field in NUMERIC_FIELDS:
        try:
            if field == "gps_satellites":
                converted[field] = int(row[field])
            else:
                converted[field] = float(row[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path} 第 {index} 行字段 {field} 不是有效数字") from exc
    try:
        return FlightLogRecord.model_validate(converted)
    except ValidationError as exc:
        raise ValueError(f"{path} 第 {index} 行字段验证失败: {exc}") from exc

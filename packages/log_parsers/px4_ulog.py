from __future__ import annotations

import json
from datetime import UTC, datetime
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from packages.drone_schemas import FlightLogRecord
from packages.log_parsers.base import LogParserDependencyError, ParsedFlightLog


class PX4ULogParser:
    name = "px4-ulog"
    version = "0.1.0"
    supported_formats = ("px4-ulog",)

    def can_parse(self, path: Path, requested_format: str = "auto") -> bool:
        return requested_format in {"auto", "px4-ulog"} and path.suffix.lower() == ".ulg"

    def parse(self, path: Path, requested_format: str = "auto") -> ParsedFlightLog:
        if path.suffix.lower() != ".ulg":
            raise ValueError(f"log format px4-ulog cannot parse file: {path}")
        mock_data = _read_mock_fixture(path)
        if mock_data is not None:
            return self._parse_mock_fixture(path, mock_data, requested_format)
        if find_spec("pyulog") is None:
            raise LogParserDependencyError(
                "Missing optional dependency 'pyulog' for log format px4-ulog. "
                "Install it with: pip install -e .[px4]. This offline parser only reads "
                "local .ulg files and will not connect to a real drone, execute MAVLink "
                "commands, upload firmware, or write flight-controller parameters."
            )
        return self._parse_pyulog(path, requested_format)

    def _parse_mock_fixture(
        self,
        path: Path,
        data: dict[str, Any],
        requested_format: str,
    ) -> ParsedFlightLog:
        topics = data.get("topics")
        if not isinstance(topics, dict):
            raise ValueError(f"PX4 ULog mock fixture missing topics object: {path}")
        timestamps = _topic_timestamps(topics.get("battery_status"), path, "battery_status")
        if not timestamps:
            raise ValueError(f"PX4 ULog mock fixture has no battery_status samples: {path}")
        records = [
            _record_from_topics(path, timestamp, topics, index)
            for index, timestamp in enumerate(timestamps, start=1)
        ]
        return ParsedFlightLog(
            records=records,
            source_log_id=str(data.get("source_log_id") or path.name),
            parser_name=self.name,
            parser_version=self.version,
            warnings=[],
            requested_format=requested_format,
            actual_format="px4-ulog",
            source_metadata={
                "path": str(path),
                "source_type": "local_file",
                "extension": path.suffix.lower(),
            },
            parser_metadata={
                "mock_fixture": True,
                "topics_used": sorted(topics),
                "safety_boundary": "offline-read-only",
            },
        )

    def _parse_pyulog(self, path: Path, requested_format: str) -> ParsedFlightLog:
        from pyulog import ULog  # type: ignore[import-not-found]

        ulog = ULog(str(path))
        topics = {dataset.name: _dataset_rows(dataset) for dataset in ulog.data_list}
        timestamps = _topic_timestamps(topics.get("battery_status"), path, "battery_status")
        if not timestamps:
            raise ValueError(f"PX4 ULog has no usable battery_status samples: {path}")
        records = [
            _record_from_topics(path, timestamp, topics, index)
            for index, timestamp in enumerate(timestamps, start=1)
        ]
        return ParsedFlightLog(
            records=records,
            source_log_id=path.name,
            parser_name=self.name,
            parser_version=self.version,
            warnings=_topic_warnings(topics),
            requested_format=requested_format,
            actual_format="px4-ulog",
            source_metadata={
                "path": str(path),
                "source_type": "local_file",
                "extension": path.suffix.lower(),
            },
            parser_metadata={
                "mock_fixture": False,
                "topics_used": sorted(name for name, rows in topics.items() if rows),
                "sample_count": len(records),
                "safety_boundary": "offline-read-only",
            },
        )


def _read_mock_fixture(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if isinstance(data, dict) and data.get("format") == "px4-ulog-mock":
        return data
    return None


def _dataset_rows(dataset: Any) -> list[dict[str, Any]]:
    data = dataset.data
    if "timestamp" not in data:
        return []
    rows: list[dict[str, Any]] = []
    for index in range(len(data["timestamp"])):
        row: dict[str, Any] = {}
        for field, values in data.items():
            value = values[index]
            if hasattr(value, "item"):
                value = value.item()
            row[field] = value
        row["timestamp"] = _parse_timestamp(row["timestamp"])
        rows.append(row)
    return rows


def _topic_timestamps(rows: object, path: Path, topic: str) -> list[datetime]:
    if not isinstance(rows, list):
        raise ValueError(f"PX4 ULog missing required topic {topic}: {path}")
    timestamps = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"PX4 ULog topic {topic} sample {index} is not an object: {path}")
        timestamps.append(_parse_timestamp(row.get("timestamp")))
    return sorted(timestamps)


def _record_from_topics(
    path: Path,
    timestamp: datetime,
    topics: dict[str, Any],
    index: int,
) -> FlightLogRecord:
    try:
        battery = _nearest(topics, "battery_status", timestamp, path)
        status = _nearest(topics, "vehicle_status", timestamp, path)
        position = _nearest(topics, "vehicle_local_position", timestamp, path)
        gps = _nearest(topics, "vehicle_gps_position", timestamp, path)
        vibration = _nearest(topics, "vehicle_imu_status", timestamp, path)
        actuators = _nearest(topics, "actuator_outputs", timestamp, path)
        telemetry = _nearest(topics, "telemetry_status", timestamp, path)
        sensor = _nearest(topics, "sensor_combined", timestamp, path)
        outputs = _motor_outputs(actuators)
        return FlightLogRecord(
            timestamp=timestamp,
            flight_mode=str(status.get("nav_state", status.get("flight_mode", "UNKNOWN"))),
            altitude_m=round(abs(_float(position, "z", "altitude_m")), 3),
            battery_voltage_v=round(_float(battery, "voltage_v", "voltage_filtered_v"), 3),
            battery_current_a=round(_float(battery, "current_a", "current_filtered_a"), 3),
            battery_soc_pct=round(_soc_pct(battery), 3),
            gps_satellites=int(_float(gps, "satellites_used", "gps_satellites")),
            gps_hdop=round(_float(gps, "hdop", "eph"), 3),
            vibration_x=round(_float(vibration, "vibration_x", "accel_vibration_metric"), 3),
            vibration_y=round(_float(vibration, "vibration_y", "gyro_vibration_metric"), 3),
            vibration_z=round(_float(vibration, "vibration_z", "delta_angle_coning_metric"), 3),
            motor_1_output=outputs[0],
            motor_2_output=outputs[1],
            motor_3_output=outputs[2],
            motor_4_output=outputs[3],
            link_quality_pct=round(_float(telemetry, "link_quality_pct", "rssi"), 3),
            temperature_c=round(_float(sensor, "temperature_c", "temperature"), 3),
        )
    except KeyError as exc:
        raise ValueError(f"PX4 ULog missing required field {exc.args[0]} at sample {index}: {path}") from exc
    except ValidationError as exc:
        raise ValueError(f"PX4 ULog sample {index} validation failed: {path}: {exc}") from exc


def _nearest(topics: dict[str, Any], topic: str, timestamp: datetime, path: Path) -> dict[str, Any]:
    rows = topics.get(topic)
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"PX4 ULog missing required topic {topic}: {path}")
    valid_rows = [row for row in rows if isinstance(row, dict)]
    if not valid_rows:
        raise ValueError(f"PX4 ULog topic {topic} has no usable samples: {path}")
    return min(valid_rows, key=lambda row: abs((_parse_timestamp(row.get("timestamp")) - timestamp).total_seconds()))


def _parse_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value) / 1_000_000, tz=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    raise ValueError(f"invalid PX4 ULog timestamp: {value!r}")


def _float(row: dict[str, Any], *fields: str) -> float:
    for field in fields:
        if field in row and row[field] is not None:
            return float(row[field])
    raise KeyError(fields[0])


def _soc_pct(row: dict[str, Any]) -> float:
    if "battery_soc_pct" in row:
        return float(row["battery_soc_pct"])
    if "remaining" in row:
        value = float(row["remaining"])
        return value * 100 if value <= 1 else value
    raise KeyError("remaining")


def _motor_outputs(row: dict[str, Any]) -> list[float]:
    raw_outputs = row.get("outputs")
    if isinstance(raw_outputs, (list, tuple)) and len(raw_outputs) >= 4:
        return [_normalize_motor_output(value) for value in raw_outputs[:4]]
    return [
        _normalize_motor_output(_float(row, "motor_1_output", "output_0")),
        _normalize_motor_output(_float(row, "motor_2_output", "output_1")),
        _normalize_motor_output(_float(row, "motor_3_output", "output_2")),
        _normalize_motor_output(_float(row, "motor_4_output", "output_3")),
    ]


def _normalize_motor_output(value: object) -> float:
    numeric = float(value)
    if numeric <= 1:
        numeric *= 100
    return round(max(0, min(100, numeric)), 3)


def _topic_warnings(topics: dict[str, list[dict[str, Any]]]) -> list[str]:
    required = {
        "vehicle_status",
        "vehicle_local_position",
        "battery_status",
        "vehicle_gps_position",
        "vehicle_imu_status",
        "actuator_outputs",
        "telemetry_status",
        "sensor_combined",
    }
    missing = sorted(name for name in required if not topics.get(name))
    return [f"PX4 ULog topic missing or empty: {name}" for name in missing]

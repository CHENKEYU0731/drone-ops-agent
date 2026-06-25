from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from packages.drone_schemas import FlightLogRecord
from packages.log_parsers.base import LogParserDependencyError, ParsedFlightLog
from packages.log_parsers.parser import REQUIRED_FIELDS, _record_from_row


MOCK_MAGIC_LINE = b"DRONE_OPS_ARDUPILOT_BIN_MOCK_V1"


class ArduPilotBinParser:
    name = "ardupilot-bin"
    version = "0.1.0"
    supported_formats = ("ardupilot-bin",)

    def can_parse(self, path: Path, requested_format: str = "auto") -> bool:
        if requested_format == "ardupilot-bin":
            return path.suffix.lower() == ".bin"
        return requested_format == "auto" and path.suffix.lower() == ".bin"

    def parse(self, path: Path, requested_format: str = "auto") -> ParsedFlightLog:
        if not path.exists():
            raise FileNotFoundError(f"Flight log does not exist: {path}")
        if path.suffix.lower() != ".bin":
            raise ValueError(f"log format ardupilot-bin cannot parse file: {path}")

        raw = path.read_bytes()
        if not raw:
            raise ValueError(f"ArduPilot BIN log is empty: {path}")
        first_line, separator, payload = raw.partition(b"\n")
        if first_line.rstrip(b"\r") == MOCK_MAGIC_LINE and separator:
            return self._parse_mock_fixture(path, payload, requested_format)
        return self._parse_dataflash_log(path, requested_format)

    def _parse_mock_fixture(self, path: Path, payload: bytes, requested_format: str) -> ParsedFlightLog:
        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"ArduPilot BIN mock fixture is invalid JSON: {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"ArduPilot BIN mock fixture must be an object: {path}")
        rows = data.get("records")
        if not isinstance(rows, list):
            raise ValueError(f"ArduPilot BIN mock fixture must contain records list: {path}")
        if not rows:
            raise ValueError(f"ArduPilot BIN log is empty: {path}")

        records: list[FlightLogRecord] = []
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise ValueError(f"{path} record {index} is not an object")
            missing = REQUIRED_FIELDS - set(row)
            if missing:
                raise ValueError(f"{path} record {index} missing fields {sorted(missing)}")
            records.append(_record_from_row(path, index, row))
        return ParsedFlightLog(
            records=records,
            source_log_id=path.name,
            parser_name=self.name,
            parser_version=self.version,
            warnings=[],
            requested_format=requested_format,
            actual_format="ardupilot-bin",
            source_metadata={
                "path": str(path),
                "source_type": "local_file",
                "extension": path.suffix.lower(),
            },
            parser_metadata={
                "mock_fixture": True,
                "record_count": len(records),
                "safety_boundary": "offline-read-only",
            },
        )

    def _parse_dataflash_log(self, path: Path, requested_format: str) -> ParsedFlightLog:
        if find_spec("pymavlink") is None:
            raise LogParserDependencyError(
                "Missing optional dependency pymavlink for ardupilot-bin parsing. "
                "Install with: pip install -e .[ardupilot]. "
                "This offline parser only reads local .bin files and never connects "
                "to aircraft, executes MAVLink commands, writes parameters, arms, "
                "takes off, lands, runs missions, returns to launch, or uploads firmware."
            )

        from pymavlink import DFReader  # type: ignore[import-not-found]

        try:
            log = DFReader.DFReader_binary(str(path))
        except Exception as exc:  # pragma: no cover - depends on optional parser internals.
            raise ValueError(f"Unable to open ArduPilot BIN log: {path}: {exc}") from exc

        parsed_rows = self._rows_from_dataflash(path, log)
        if not parsed_rows.rows:
            raise ValueError(f"ArduPilot BIN log produced no usable records: {path}")

        records = [_record_from_row(path, index, row) for index, row in enumerate(parsed_rows.rows, start=1)]
        warnings = [
            "ArduPilot BIN parser uses a minimal first-pass message mapping.",
            "link_quality_pct defaulted to 100 because DataFlash link quality mapping is not yet supported.",
        ]
        return ParsedFlightLog(
            records=records,
            source_log_id=path.name,
            parser_name=self.name,
            parser_version=self.version,
            warnings=warnings,
            requested_format=requested_format,
            actual_format="ardupilot-bin",
            source_metadata={
                "path": str(path),
                "source_type": "local_file",
                "extension": path.suffix.lower(),
            },
            parser_metadata={
                "mock_fixture": False,
                "messages_used": ["BAT", "BAT2", "GPS", "GPS2", "VIBE", "RCOU", "MODE", "MODE2"],
                "messages_consumed": parsed_rows.messages_consumed,
                "snapshot_count": len(parsed_rows.rows),
                "safety_boundary": "offline-read-only",
            },
        )

    def _rows_from_dataflash(self, path: Path, log: Any) -> _ParsedDataFlashRows:
        rows: list[dict[str, Any]] = []
        state = _DefaultingRecordBuilder(path)
        messages_consumed = 0
        while True:
            message = log.recv_msg()
            if message is None:
                break
            messages_consumed += 1
            msg_type = message.get_type()
            values = message.to_dict()
            state.ingest(msg_type, values)
            if msg_type in {"BAT", "BAT2", "GPS", "GPS2", "VIBE", "RCOU", "MODE", "MODE2"}:
                row = state.snapshot()
                if row is not None:
                    rows.append(row)
        return _ParsedDataFlashRows(rows=rows, messages_consumed=messages_consumed)


class _ParsedDataFlashRows:
    def __init__(self, rows: list[dict[str, Any]], messages_consumed: int) -> None:
        self.rows = rows
        self.messages_consumed = messages_consumed


class _DefaultingRecordBuilder:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.start_time = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        self.current: dict[str, Any] = {
            "timestamp": self.start_time.isoformat().replace("+00:00", "Z"),
            "flight_mode": "UNKNOWN",
            "altitude_m": 0.0,
            "battery_voltage_v": 0.0,
            "battery_current_a": 0.0,
            "battery_soc_pct": 100.0,
            "gps_satellites": 0,
            "gps_hdop": 99.0,
            "vibration_x": 0.0,
            "vibration_y": 0.0,
            "vibration_z": 0.0,
            "motor_1_output": 0.0,
            "motor_2_output": 0.0,
            "motor_3_output": 0.0,
            "motor_4_output": 0.0,
            "link_quality_pct": 100.0,
            "temperature_c": 0.0,
        }

    def ingest(self, msg_type: str, values: dict[str, Any]) -> None:
        timestamp = _extract_timestamp(values, self.start_time)
        if timestamp is not None:
            self.current["timestamp"] = timestamp.isoformat().replace("+00:00", "Z")
        if msg_type in {"MODE", "MODE2"}:
            self.current["flight_mode"] = str(values.get("Mode") or values.get("ModeNum") or "UNKNOWN")
        elif msg_type in {"GPS", "GPS2"}:
            self.current["altitude_m"] = _first_number(values, ["Alt", "RelAlt", "HAGL"], self.current["altitude_m"])
            self.current["gps_satellites"] = int(_first_number(values, ["NSats", "Sats"], self.current["gps_satellites"]))
            self.current["gps_hdop"] = _first_number(values, ["HDop", "HDOP"], self.current["gps_hdop"])
        elif msg_type in {"BAT", "BAT2"}:
            self.current["battery_voltage_v"] = _first_number(values, ["Volt", "VoltR"], self.current["battery_voltage_v"])
            self.current["battery_current_a"] = _first_number(values, ["Curr", "CurrTot"], self.current["battery_current_a"])
            self.current["battery_soc_pct"] = _clamp(_first_number(values, ["RemPct", "SoC"], self.current["battery_soc_pct"]), 0, 100)
            self.current["temperature_c"] = _first_number(values, ["Temp", "Temp2"], self.current["temperature_c"])
        elif msg_type == "VIBE":
            self.current["vibration_x"] = _first_number(values, ["VibeX"], self.current["vibration_x"])
            self.current["vibration_y"] = _first_number(values, ["VibeY"], self.current["vibration_y"])
            self.current["vibration_z"] = _first_number(values, ["VibeZ"], self.current["vibration_z"])
        elif msg_type == "RCOU":
            for output_index, key in enumerate(["C1", "C2", "C3", "C4"], start=1):
                pwm = _first_number(values, [key], 1000.0)
                self.current[f"motor_{output_index}_output"] = _clamp((pwm - 1000.0) / 10.0, 0, 100)

    def snapshot(self) -> dict[str, Any] | None:
        try:
            FlightLogRecord.model_validate(self.current)
        except ValidationError:
            return None
        return dict(self.current)


def _extract_timestamp(values: dict[str, Any], start_time: datetime) -> datetime | None:
    for key in ("TimeUS", "TimeMS"):
        value = values.get(key)
        if isinstance(value, (int, float)):
            scale = 1_000_000 if key == "TimeUS" else 1_000
            return start_time + timedelta(seconds=float(value) / scale)
    return None


def _first_number(values: dict[str, Any], keys: list[str], default: float) -> float:
    for key in keys:
        value = values.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return float(default)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


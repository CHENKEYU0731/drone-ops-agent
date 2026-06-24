from __future__ import annotations

from pathlib import Path

from packages.drone_schemas import FlightLogRecord
from packages.log_parsers.base import ParsedFlightLog, resolve_log_format
from packages.log_parsers.parser import _read_csv, _read_json, _record_from_row
from packages.log_parsers.px4_ulog import PX4ULogParser


CSV_JSON_PARSER_NAME = "csv-json-flight-log"
CSV_JSON_PARSER_VERSION = "1.1.0"


def parse_flight_log_details(path: Path, requested_format: str = "auto") -> ParsedFlightLog:
    if not path.exists():
        raise FileNotFoundError(f"飞行日志不存在: {path}")
    actual_format = resolve_log_format(path, requested_format)
    if actual_format in {"csv", "json"}:
        return _parse_csv_json(path, requested_format, actual_format)
    if actual_format == "px4-ulog":
        parser = PX4ULogParser()
        if not parser.can_parse(path, actual_format):
            raise ValueError(f"log format px4-ulog cannot parse file: {path}")
        return parser.parse(path, requested_format=requested_format)
    if actual_format == "ardupilot-bin":
        raise ValueError(
            "log format ardupilot-bin is registered for auto-detection but is not "
            "implemented in this PX4 ULog worktree"
        )
    raise ValueError(f"Unsupported log format '{actual_format}' for file: {path}")


def parse_flight_log(path: Path, requested_format: str = "auto") -> list[FlightLogRecord]:
    return parse_flight_log_details(path, requested_format=requested_format).records


def _parse_csv_json(path: Path, requested_format: str, actual_format: str) -> ParsedFlightLog:
    if actual_format == "csv":
        if path.suffix.lower() != ".csv":
            raise ValueError(f"log format csv cannot parse file: {path}")
        rows = _read_csv(path)
    elif actual_format == "json":
        if path.suffix.lower() != ".json":
            raise ValueError(f"log format json cannot parse file: {path}")
        rows = _read_json(path)
    else:
        raise ValueError(f"Unsupported CSV/JSON log format: {actual_format}")
    if not rows:
        raise ValueError(f"飞行日志为空: {path}")
    records = [_record_from_row(path, index, row) for index, row in enumerate(rows, start=1)]
    return ParsedFlightLog(
        records=records,
        source_log_id=path.name,
        parser_name=CSV_JSON_PARSER_NAME,
        parser_version=CSV_JSON_PARSER_VERSION,
        warnings=[],
        requested_format=requested_format,
        actual_format=actual_format,
        source_metadata={
            "path": str(path),
            "source_type": "local_file",
            "extension": path.suffix.lower(),
        },
        parser_metadata={"fields": sorted(rows[0]) if rows else []},
    )

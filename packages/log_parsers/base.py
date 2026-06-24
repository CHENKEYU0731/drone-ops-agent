from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

from packages.drone_schemas import FlightLogRecord


ParserFormat = Literal["auto", "csv", "json", "px4-ulog", "ardupilot-bin"]

SUPPORTED_LOG_FORMATS: tuple[str, ...] = ("auto", "csv", "json", "px4-ulog", "ardupilot-bin")

EXTENSION_FORMATS: dict[str, str] = {
    ".csv": "csv",
    ".json": "json",
    ".ulg": "px4-ulog",
    ".bin": "ardupilot-bin",
}


@dataclass(frozen=True)
class ParsedFlightLog:
    records: list[FlightLogRecord]
    source_log_id: str
    parser_name: str
    parser_version: str
    warnings: list[str] = field(default_factory=list)
    requested_format: str = "auto"
    actual_format: str = "auto"
    source_metadata: dict[str, Any] = field(default_factory=dict)
    parser_metadata: dict[str, Any] = field(default_factory=dict)


class FlightLogParser(Protocol):
    name: str
    version: str
    supported_formats: tuple[str, ...]

    def can_parse(self, path: Path, requested_format: str = "auto") -> bool:
        ...

    def parse(self, path: Path, requested_format: str = "auto") -> ParsedFlightLog:
        ...


class LogParserDependencyError(ValueError):
    pass


def detect_log_format(path: Path) -> str:
    resolved = EXTENSION_FORMATS.get(path.suffix.lower())
    if resolved is None:
        raise ValueError(
            f"Cannot auto-detect log format for {path}. Supported extension rules: "
            ".csv->csv, .json->json, .ulg->px4-ulog, .bin->ardupilot-bin"
        )
    return resolved


def resolve_log_format(path: Path, requested_format: str = "auto") -> str:
    normalized = requested_format.lower()
    if normalized not in SUPPORTED_LOG_FORMATS:
        raise ValueError(
            f"Unsupported log format '{requested_format}'. Supported formats: "
            f"{', '.join(SUPPORTED_LOG_FORMATS)}"
        )
    if normalized == "auto":
        return detect_log_format(path)
    suffix_format = EXTENSION_FORMATS.get(path.suffix.lower())
    if suffix_format is not None and suffix_format != normalized:
        raise ValueError(f"log format {normalized} cannot parse file: {path}")
    return normalized

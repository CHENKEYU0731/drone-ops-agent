from pathlib import Path

import pytest

from packages.log_parsers import parse_flight_log, parse_flight_log_details
from packages.log_parsers.base import LogParserDependencyError, resolve_log_format


def test_auto_format_recognizes_required_extensions() -> None:
    assert resolve_log_format(Path("flight.csv"), "auto") == "csv"
    assert resolve_log_format(Path("flight.json"), "auto") == "json"
    assert resolve_log_format(Path("flight.ulg"), "auto") == "px4-ulog"
    assert resolve_log_format(Path("flight.bin"), "auto") == "ardupilot-bin"


def test_parse_px4_mock_ulog_returns_normalized_records() -> None:
    parsed = parse_flight_log_details(
        Path("data/sample_logs/example_px4_mock.ulg"),
        requested_format="px4-ulog",
    )

    assert parsed.parser_name == "px4-ulog"
    assert parsed.actual_format == "px4-ulog"
    assert parsed.source_log_id == "example_px4_mock.ulg"
    assert len(parsed.records) == 3
    assert parsed.records[0].flight_mode == "POSCTL"
    assert parsed.records[0].altitude_m == 12.0
    assert parsed.records[-1].battery_soc_pct == 22
    assert parsed.records[-1].gps_satellites == 7
    assert parsed.source_metadata["path"].endswith("example_px4_mock.ulg")
    assert parsed.parser_metadata["mock_fixture"] is True
    assert parsed.warnings == []


def test_legacy_parse_flight_log_still_returns_records_for_px4_auto() -> None:
    records = parse_flight_log(Path("data/sample_logs/example_px4_mock.ulg"), requested_format="auto")

    assert len(records) == 3
    assert records[-1].link_quality_pct == 58


def test_px4_dependency_error_is_clear_for_non_mock_ulog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "realish.ulg"
    path.write_bytes(b"ULog\x01\x12not-a-json-mock")
    monkeypatch.setattr("packages.log_parsers.px4_ulog.find_spec", lambda name: None)

    with pytest.raises(LogParserDependencyError) as exc_info:
        parse_flight_log_details(path, requested_format="px4-ulog")

    message = str(exc_info.value)
    assert "pyulog" in message
    assert "pip install -e .[px4]" in message
    assert "px4-ulog" in message
    assert "will not connect to a real drone" in message
    assert "Traceback" not in message


def test_px4_rejects_non_ulg_when_format_explicit(tmp_path: Path) -> None:
    path = tmp_path / "flight.csv"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="px4-ulog cannot parse file"):
        parse_flight_log_details(path, requested_format="px4-ulog")

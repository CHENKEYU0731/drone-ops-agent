from pathlib import Path

import pytest

from packages.log_parsers import parse_flight_log, parse_flight_log_with_metadata
from packages.log_parsers.ardupilot_bin import ArduPilotBinParser


FIXTURE = Path("data/sample_logs/example_ardupilot.bin")


def test_ardupilot_bin_mock_fixture_normalizes_records() -> None:
    parsed = parse_flight_log_with_metadata(FIXTURE, requested_format="ardupilot-bin")

    assert parsed.parser_name == "ardupilot-bin"
    assert parsed.source_log_id == "example_ardupilot.bin"
    assert len(parsed.records) == 3
    assert parsed.records[0].flight_mode == "STABILIZE"
    assert parsed.records[-1].battery_soc_pct == 24
    assert parsed.warnings == []


def test_auto_format_detects_bin_extension() -> None:
    records = parse_flight_log(FIXTURE, requested_format="auto")

    assert len(records) == 3
    assert records[1].flight_mode == "AUTO"


def test_bin_parser_rejects_non_bin_file() -> None:
    parser = ArduPilotBinParser()

    assert parser.can_parse(Path("flight.csv"), requested_format="auto") is False
    assert parser.can_parse(Path("flight.bin"), requested_format="auto") is True


def test_real_bin_without_optional_dependency_has_clear_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "real-flight.bin"
    path.write_bytes(b"\xa3\x95not-a-mock-dataflash-log")
    monkeypatch.setattr("packages.log_parsers.ardupilot_bin.find_spec", lambda name: None)
    monkeypatch.setattr(Path, "read_bytes", lambda *_args, **_kwargs: pytest.fail("real BIN probe used read_bytes"))

    with pytest.raises(ValueError, match=r"pip install -e \.\[ardupilot\]"):
        parse_flight_log_with_metadata(path, requested_format="ardupilot-bin")


def test_ardupilot_bin_parser_stays_offline_and_read_only() -> None:
    source = Path("packages/log_parsers/ardupilot_bin.py").read_text(encoding="utf-8").lower()

    forbidden_fragments = [
        "mavutil.mavlink_connection",
        "command_long_send",
        "param_set_send",
        "arducopter_with",
        "ardusub_with",
        "ardurover_with",
        "set_mode_send",
        "mission_item",
        "ftp_upload",
    ]
    assert not any(fragment in source for fragment in forbidden_fragments)

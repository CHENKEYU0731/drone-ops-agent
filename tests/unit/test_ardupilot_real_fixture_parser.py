from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from packages.log_parsers import parse_flight_log_details


REAL_FIXTURE = Path("data/sample_logs/ardupilot/real_sample.bin")


class _FakeMessage:
    def __init__(self, message_type: str, values: dict[str, object]) -> None:
        self._message_type = message_type
        self._values = values

    def get_type(self) -> str:
        return self._message_type

    def to_dict(self) -> dict[str, object]:
        return dict(self._values)


class _FakeDataFlashLog:
    def __init__(self, messages: list[_FakeMessage]) -> None:
        self._messages = list(messages)

    def recv_msg(self) -> _FakeMessage | None:
        if not self._messages:
            return None
        return self._messages.pop(0)


def _install_fake_dfreader(monkeypatch: pytest.MonkeyPatch, messages: list[_FakeMessage]) -> None:
    class FakeDFReader:
        @staticmethod
        def DFReader_binary(path: str) -> _FakeDataFlashLog:
            assert path.endswith(".bin")
            return _FakeDataFlashLog(messages)

    monkeypatch.setitem(sys.modules, "pymavlink", types.SimpleNamespace(DFReader=FakeDFReader))
    monkeypatch.setattr("packages.log_parsers.ardupilot_bin.find_spec", lambda name: object() if name == "pymavlink" else None)


def test_missing_ardupilot_real_fixture_is_documented_skip() -> None:
    if not REAL_FIXTURE.exists():
        pytest.skip("Optional real ArduPilot BIN fixture not present; see data/sample_logs/ardupilot/README.md")

    parsed = parse_flight_log_details(REAL_FIXTURE, requested_format="auto")

    assert parsed.actual_format == "ardupilot-bin"
    assert parsed.records
    assert parsed.parser_metadata["mock_fixture"] is False


def test_ardupilot_dataflash_path_records_message_and_snapshot_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = tmp_path / "redacted.bin"
    fixture.write_bytes(b"\xa3\x95fake dataflash")
    messages = [
        _FakeMessage("MODE", {"TimeUS": 1_000_000, "Mode": "AUTO"}),
        _FakeMessage("GPS", {"TimeUS": 1_000_000, "Alt": 44.0, "NSats": 12, "HDop": 0.8}),
        _FakeMessage("BAT", {"TimeUS": 1_000_000, "Volt": 16.1, "Curr": 18.2, "RemPct": 76, "Temp": 35}),
        _FakeMessage("VIBE", {"TimeUS": 1_000_000, "VibeX": 0.2, "VibeY": 0.3, "VibeZ": 0.4}),
        _FakeMessage("RCOU", {"TimeUS": 1_000_000, "C1": 1320, "C2": 1330, "C3": 1340, "C4": 1350}),
    ]
    _install_fake_dfreader(monkeypatch, messages)

    parsed = parse_flight_log_details(fixture, requested_format="ardupilot-bin")

    assert parsed.records
    assert parsed.records[-1].flight_mode == "AUTO"
    assert parsed.records[-1].battery_soc_pct == 76
    assert parsed.parser_metadata["mock_fixture"] is False
    assert parsed.parser_metadata["messages_consumed"] == 5
    assert parsed.parser_metadata["snapshot_count"] >= 1
    assert "link_quality_pct defaulted" in " ".join(parsed.warnings)


def test_ardupilot_no_required_messages_error_is_clear(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = tmp_path / "empty-real.bin"
    fixture.write_bytes(b"\xa3\x95fake dataflash")
    _install_fake_dfreader(monkeypatch, [_FakeMessage("MSG", {"TimeUS": 1_000_000})])

    with pytest.raises(ValueError, match="produced no usable records"):
        parse_flight_log_details(fixture, requested_format="ardupilot-bin")
